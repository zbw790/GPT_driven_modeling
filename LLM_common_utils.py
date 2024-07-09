# common_utils.py

import base64
import os
import textwrap
import logging
import bpy
import re
import traceback
import importlib
import sys
from bpy.props import StringProperty, CollectionProperty
from bpy.types import PropertyGroup

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

# 定义全局提示词
GLOBAL_PROMPT = """
你将充当一个智能助手，需要根据用户的指令提供相应的回答。在执行任何操作时，请参考对话历史中提到的内容和上下文。请严格遵守以下规则：

1. 所有的回答都应基于对话历史，并尽量参考之前提到过的信息。

2. 如果用户明确要求生成 Blender 指令：
    a. 仅返回可直接执行的 Blender Python 命令。
    c. 不要包含任何额外的描述性文本或符号。包括类似：“根据您的要求，我们需要使用以下的指令。”这种类型的文字也不能出现。
    d. 确保每个命令都是有效的 Blender Python API 调用。
    e. 如果必须添加说明，只能以Python单行注释的形式出现（使用#开头）。
    f. 绝对不要使用三引号形式的多行注释

3. 在没有明确要求生成 Blender 指令的情况下：
    a. 提供详细的回答和解释。
    b. 确保回答的内容与对话历史和上下文一致。
    c. 如果需要举例说明 Blender 指令，请使用与规则 2 相同的格式。

示例 - 当要求生成 Blender 指令时，你应该只返回如下格式的内容：
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0))

4. 在没有明确要求用其他语言回复的情况下，统一用中文回答。

以下是一些我自定义的blender API的介绍，你需要在合适的时候使用他们：
"""

SCREENSHOT_PROMPTS = """
以下是Blender内的模型图片,所有图片拍摄自同一模型的不同角度。请检查这个模型是否存在以下问题：

所有部件是否都连接在一起，没有悬空或分离的部分
模型的比例是否合理，各部分大小是否协调
是否存在明显的几何错误，如穿模、非流畅边缘等
模型的整体形状是否符合预期的物体外观
是否有多余或缺失的部件

如果发现任何问题，请生成相应的Blender Python命令来修复。如果模型没有明显问题，请回复"这个模型没有问题"。
生成指令时，请只返回可直接执行的Blender Python命令，不要包含任何额外的描述性文本或符号。
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
custom_prompts_file = os.path.join(current_dir, "LLM_API_prompts.txt")

try:
    with open(custom_prompts_file, "r", encoding="utf-8") as f:
        custom_prompts = f.read()
        # 将自定义提示词添加到 GLOBAL_PROMPT
    GLOBAL_PROMPT += "\n" + custom_prompts
except FileNotFoundError:
    print(f"警告：未找到自定义提示词文件 {custom_prompts_file}")
except Exception as e:
    print(f"读取自定义提示词文件时出错：{str(e)}")



class Message(PropertyGroup):
    role: StringProperty(name="Role")
    content: StringProperty(name="Content")

class Properties(PropertyGroup):
    input_text: StringProperty(
        name="Input Text",
        description="Enter text to send to GPT"
    )
    messages: CollectionProperty(type=Message)

def initialize_conversation(tool):
    if not any(msg.content == GLOBAL_PROMPT.strip() for msg in tool.messages):
        system_message = tool.messages.add()
        system_message.role = "system"
        system_message.content = GLOBAL_PROMPT.strip()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

import re
import ast

def is_valid_python(line):
    try:
        # 尝试作为表达式解析
        ast.parse(line, mode='eval')
        return True
    except SyntaxError:
        try:
            # 尝试作为语句解析
            ast.parse(line, mode='exec')
            return True
        except SyntaxError:
            # 检查是否是以某些关键字开头的不完整语句
            if re.match(r'^\s*(def|class|if|for|while|try|with|else|elif|return)', line):
                return True
            return False
    
def is_potential_multiline_start(line):
    return line.strip().endswith(('=', '[', '{', '('))

def sanitize_command(command):
    try:
        # 移除代码块标记和语言标识
        command = re.sub(r'^(```|"""|\'\'\')\s*(?:python)?\s*\n|(```|"""|\'\'\')\s*$', '', command, flags=re.MULTILINE | re.IGNORECASE).strip()
        
        # 移除可能残留的单独 'python' 行
        lines = command.split('\n')
        if lines and lines[0].strip().lower() == 'python':
            lines = lines[1:]
        
        cleaned_lines = []
        buffer = []
        i = 0
        in_multiline = False
        
        while i < len(lines):
            current_line = lines[i].strip()
            
            # 替换特殊引号和其他字符
            current_line = current_line.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
            current_line = current_line.replace('，', ',').replace('：', ':').replace('；', ';')
            
            # 保留原始缩进
            indent = len(lines[i]) - len(lines[i].lstrip())
            
            if current_line.startswith('#') or not current_line:  # 注释或空行
                if buffer:
                    cleaned_lines.extend(buffer)
                    buffer = []
                    in_multiline = False
                cleaned_lines.append(' ' * indent + current_line)
                i += 1
                continue
            
            if is_potential_multiline_start(current_line):
                in_multiline = True
            
            # 尝试添加新行并验证
            new_buffer = buffer + [' ' * indent + current_line]
            if is_valid_python('\n'.join(new_buffer)) or in_multiline:
                buffer = new_buffer
                i += 1
                if not is_potential_multiline_start(current_line) and not current_line.strip().endswith(','):
                    in_multiline = False
            else:
                # 如果新行添加后不合法，先保存之前的buffer
                if buffer:
                    cleaned_lines.extend(buffer)
                    buffer = []
                    in_multiline = False
                
                # 单独检查当前行
                if is_valid_python(current_line):
                    cleaned_lines.append(' ' * indent + current_line)
                else:
                    cleaned_lines.append(f"# {' ' * indent + current_line}")
                i += 1
        
        # 处理最后可能剩余的buffer
        if buffer:
            cleaned_lines.extend(buffer)
        
        return '\n'.join(cleaned_lines)
    except Exception as e:
        print(f"Error sanitizing command: {e}")
        return command

def get_scene_info():
    scene_info = []
    for obj in bpy.context.scene.objects:
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": tuple(obj.location),
            "rotation": tuple(obj.rotation_euler),
            "scale": tuple(obj.scale)
        }
        if obj.type == 'MESH':
            obj_info["vertex_count"] = len(obj.data.vertices)
            obj_info["face_count"] = len(obj.data.polygons)
        scene_info.append(obj_info)
    return scene_info

def format_scene_info(scene_info):
    formatted_info = "场景信息:\n"
    for obj in scene_info:
        formatted_info += f"对象名称: {obj['name']}\n"
        formatted_info += f"  类型: {obj['type']}\n"
        formatted_info += f"  位置: {obj['location']}\n"
        formatted_info += f"  旋转: {obj['rotation']}\n"
        formatted_info += f"  缩放: {obj['scale']}\n"
        if 'vertex_count' in obj:
            formatted_info += f"  顶点数: {obj['vertex_count']}\n"
            formatted_info += f"  面数: {obj['face_count']}\n"
        formatted_info += "\n"
    return formatted_info

def execute_blender_command(command):
    try:
        sanitized_command = sanitize_command(command)
        logger.info(f"Executing sanitized command: {sanitized_command}")
        
        dedented_command = textwrap.dedent(sanitized_command)
        
        # 创建一个新的全局命名空间, 注意__builtins__的正确写法是 __builtins__
        exec_globals = {
            '__name__': '__main__',
            '__builtins__': __builtins__,
        }
        
        # 添加一个自定义的导入函数
        def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
            try:
                if name not in sys.modules:
                    importlib.import_module(name)
                return sys.modules[name]
            except ImportError as e:
                logger.error(f"无法导入模块 {name}: {str(e)}")
                raise e
        
        exec_globals['__import__'] = custom_import
        
        # 执行代码
        exec(dedented_command, exec_globals)
        
        logger.info("命令执行成功")
    except IndentationError as ie:
        logger.error(f"缩进错误: {str(ie)}")
        logger.error(f"出错的代码行: {ie.text}")
        logger.error(f"出错的行号: {ie.lineno}")
    except SyntaxError as se:
        logger.error(f"语法错误: {str(se)}")
        logger.error(f"出错的代码行: {se.text}")
        logger.error(f"出错的行号: {se.lineno}")
    except Exception as e:
        logger.error(f"命令执行失败: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"完整的错误信息: {traceback.format_exc()}")

def generate_prompt(messages, current_instruction=None):
    conversation = "\n".join([f"{message['role']}: {message['content']}" for message in messages])
    prompt = f"历史对话记录如下：\n{conversation}"
    if current_instruction:
        prompt += f"\n在我发给你的信息中,包含了我和你过去的历史对话,请尽量参考之前提到过的信息。现在,请根据当前指令提供回答：\n{current_instruction}"
    return prompt

def generate_screenshot_prompt(messages):
    conversation = "\n".join([f"{message['role']}: {message['content']}" for message in messages])
    prompt = f"历史对话记录如下：\n{conversation}\n\n{SCREENSHOT_PROMPTS}"
    return prompt
