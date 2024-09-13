# LLM_common_utils.py

import base64
import os
import textwrap
import logging
import bpy
import re
import traceback
import importlib
import sys
import ast
from bpy.props import StringProperty
from bpy.types import PropertyGroup

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

# 定义全局提示词
GLOBAL_PROMPT = """
你将充当一个智能助手，需要根据用户的指令提供相应的回答。在执行任何操作时，请参考对话历史中提到的内容和上下文。请严格遵守以下规则：

1. 所有的回答都应基于对话历史，并尽量参考之前提到过的信息。

2. 如果用户明确要求生成 Blender 指令：
    a. 仅返回可直接执行的 Blender Python 命令。
    c. 不要包含任何额外的描述性文本或符号。包括类似："根据您的要求，我们需要使用以下的指令。"这种类型的文字也不能出现。
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


class LLMToolProperties(PropertyGroup):
    input_text: StringProperty(name="Input Text", default="")


def get_screenshots():
    screenshots_path = r"D:\GPT_driven_modeling\resources\screenshots"
    return [
        os.path.join(screenshots_path, f)
        for f in os.listdir(screenshots_path)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
    ]


def initialize_conversation(context):
    conversation_manager = context.scene.conversation_manager
    if not any(
        msg.content == GLOBAL_PROMPT.strip() for msg in conversation_manager.messages
    ):
        conversation_manager.add_message("system", GLOBAL_PROMPT.strip())


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def is_valid_python(line):
    try:
        # 尝试作为表达式解析
        ast.parse(line, mode="eval")
        return True
    except SyntaxError:
        try:
            # 尝试作为语句解析
            ast.parse(line, mode="exec")
            return True
        except SyntaxError:
            # 检查是否是以某些关键字开头的不完整语句
            if re.match(
                r"^\s*(def|class|if|for|while|try|with|else|elif|return)", line
            ):
                return True
            return False


def is_potential_multiline_start(line):
    return line.strip().endswith(("=", "[", "{", "("))


def sanitize_command(command):
    try:
        # 移除代码块标记和语言标识
        command = re.sub(
            r'^(```|"""|\'\'\')\s*(?:python)?\s*\n|(```|"""|\'\'\')\s*$',
            "",
            command,
            flags=re.MULTILINE | re.IGNORECASE,
        ).strip()

        # 移除可能残留的单独 'python' 行
        lines = command.split("\n")
        if lines and lines[0].strip().lower() == "python":
            lines = lines[1:]

        cleaned_lines = []
        buffer = []
        i = 0
        in_multiline = False
        open_brackets = 0  # 新增：跟踪开放的括号数量

        while i < len(lines):
            current_line = lines[i].strip()

            # 替换特殊引号和其他字符
            current_line = (
                current_line.replace('"', '"')
                .replace('"', '"')
                .replace(""", "'").replace(""", "'")
            )
            current_line = (
                current_line.replace("，", ",").replace("：", ":").replace("；", ";")
            )

            # 保留原始缩进
            indent = len(lines[i]) - len(lines[i].lstrip())

            # 更新括号计数
            open_brackets += (
                current_line.count("(")
                + current_line.count("[")
                + current_line.count("{")
            )
            open_brackets -= (
                current_line.count(")")
                + current_line.count("]")
                + current_line.count("}")
            )

            if current_line.startswith("#") or not current_line:  # 注释或空行
                if buffer and open_brackets == 0:
                    cleaned_lines.extend(buffer)
                    buffer = []
                    in_multiline = False
                cleaned_lines.append(" " * indent + current_line)
                i += 1
                continue

            if is_potential_multiline_start(current_line) or open_brackets > 0:
                in_multiline = True

            # 尝试添加新行并验证
            new_buffer = buffer + [" " * indent + current_line]
            if (
                is_valid_python("\n".join(new_buffer))
                or in_multiline
                or open_brackets > 0
            ):
                buffer = new_buffer
                i += 1
                if (
                    not is_potential_multiline_start(current_line)
                    and not current_line.strip().endswith(",")
                    and open_brackets == 0
                ):
                    in_multiline = False
            else:
                # 如果新行添加后不合法，先保存之前的buffer
                if buffer and open_brackets == 0:
                    cleaned_lines.extend(buffer)
                    buffer = []
                    in_multiline = False

                # 单独检查当前行
                if is_valid_python(current_line):
                    cleaned_lines.append(" " * indent + current_line)
                else:
                    cleaned_lines.append(f"# {' ' * indent + current_line}")
                i += 1

        # 处理最后可能剩余的buffer
        if buffer:
            cleaned_lines.extend(buffer)

        return "\n".join(cleaned_lines)
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
            "scale": tuple(obj.scale),
            "dimensions": tuple(obj.dimensions),
        }

        if obj.type == "MESH":
            obj_info["vertex_count"] = len(obj.data.vertices)
            obj_info["face_count"] = len(obj.data.polygons)

            # 获取材质信息
            materials = [
                slot.material.name for slot in obj.material_slots if slot.material
            ]
            obj_info["materials"] = materials

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
        formatted_info += f"  尺寸:\n"
        formatted_info += f"    长 (X): {obj['dimensions'][0]:.3f}\n"
        formatted_info += f"    宽 (Y): {obj['dimensions'][1]:.3f}\n"
        formatted_info += f"    高 (Z): {obj['dimensions'][2]:.3f}\n"
        if obj["type"] == "MESH":
            formatted_info += f"  顶点数: {obj['vertex_count']}\n"
            formatted_info += f"  面数: {obj['face_count']}\n"
            if obj["materials"]:
                formatted_info += f"  材质: {', '.join(obj['materials'])}\n"
        formatted_info += "\n"
    return formatted_info


def execute_blender_command(command):
    try:
        sanitized_command = sanitize_command(command)
        logger.info(f"Executing sanitized command: {sanitized_command}")

        dedented_command = textwrap.dedent(sanitized_command)

        # 创建一个新的全局命名空间
        exec_globals = {
            "__name__": "__main__",
            "__builtins__": __builtins__,
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

        exec_globals["__import__"] = custom_import

        # 执行代码
        exec(dedented_command, exec_globals)

        logger.info("命令执行成功")
        return None  # 如果执行成功，返回 None
    except Exception as e:
        error_message = f"命令执行失败: {str(e)}\n"
        error_message += f"错误类型: {type(e).__name__}\n"
        error_message += f"完整的错误信息:\n{traceback.format_exc()}"
        logger.error(error_message)
        raise  # 重新抛出异常，以保持与原有行为一致


def execute_blender_command_with_error_handling(command):
    try:
        execute_blender_command(command)
        return None
    except Exception as e:
        error_message = f"命令执行失败: {str(e)}\n"
        error_message += f"错误类型: {type(e).__name__}\n"
        error_message += f"完整的错误信息:\n{traceback.format_exc()}"
        return error_message


def add_history_to_prompt(context, prompt):
    conversation_manager = context.scene.conversation_manager
    conversation = "\n".join(
        [
            f"{message['role']}: {message['content']}"
            for message in conversation_manager.get_conversation_history()
        ]
    )
    return f"历史对话记录如下：\n{conversation}\n\n在我发给你的信息中,包含了我和你过去的历史对话,请尽量参考之前提到过的信息。\n\n{prompt}"
