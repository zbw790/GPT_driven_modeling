# common_utils.py

import base64
import os
import textwrap
import logging
import bpy
import traceback
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
    b. 将所有命令包含在一对三重反引号内，并在开头标注 'python'。
    c. 不要包含任何额外的描述性文本、符号或注释。
    d. 确保每个命令都是有效的 Blender Python API 调用。

3. 在没有明确要求生成 Blender 指令的情况下：
    a. 提供详细的回答和解释。
    b. 确保回答的内容与对话历史和上下文一致。
    c. 如果需要举例说明 Blender 指令，请使用与规则 2 相同的格式。

示例 - 当要求生成 Blender 指令时，你应该只返回如下格式的内容，除blender指令外，若你要提供任何描述性文字，必须是以注释的形式出现，以防影响指令的运行，以下是一个例子：
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
# 添加一个圆柱体
bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0))
"""

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

def sanitize_command(command):
    try:
        if command.startswith("```") and command.endswith("```"):
            command = command[3:-3].strip()
            if command.startswith("python"):
                command = command[6:].strip()
        
        sanitized_command = ''.join(char for char in command if ord(char) < 128)
        sanitized_command = sanitized_command.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        
        sanitized_lines = sanitized_command.split('\n')
        cleaned_lines = [line.strip() for line in sanitized_lines if line.strip()]
        cleaned_command = '\n'.join(cleaned_lines)
        
        # 检查和修复缩进
        lines = cleaned_command.split('\n')
        fixed_lines = []
        current_indent = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except:', 'finally:')):
                fixed_lines.append(' ' * current_indent + stripped)
                current_indent += 4
            elif stripped.startswith(('return', 'break', 'continue', 'pass')):
                current_indent = max(0, current_indent - 4)
                fixed_lines.append(' ' * current_indent + stripped)
            else:
                fixed_lines.append(' ' * current_indent + stripped)
        
        return '\n'.join(fixed_lines)
    except Exception as e:
        logger.error(f"Error sanitizing command: {e}")
        return command

def execute_blender_command(command):
    try:
        sanitized_command = sanitize_command(command)
        logger.info(f"Executing sanitized command: {sanitized_command}")
        
        dedented_command = textwrap.dedent(sanitized_command)
        
        exec_globals = {'bpy': bpy}
        
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