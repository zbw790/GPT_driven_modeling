# LLM_common_utils.py

"""
This module provides common utility functions for LLM-driven modeling in Blender.
It includes functions for handling conversations, processing commands, and managing scene information.
"""

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

# Define global prompt
GLOBAL_PROMPT = """
You will act as an intelligent assistant, providing responses based on user instructions. When performing any operation, please refer to the content and context mentioned in the conversation history. Please strictly adhere to the following rules:

1. All answers should be based on the conversation history and reference previously mentioned information as much as possible.

2. If the user explicitly requests to generate Blender instructions:
    a. Only return Blender Python commands that can be directly executed.
    c. Do not include any additional descriptive text or symbols. This includes text like: "Based on your request, we need to use the following instructions."
    d. Ensure that each command is a valid Blender Python API call.
    e. If explanations must be added, they can only appear as Python single-line comments (using # at the beginning).
    f. Never use triple-quote multi-line comments.

3. In cases where there is no explicit request to generate Blender instructions:
    a. Provide detailed answers and explanations.
    b. Ensure that the content of the answer is consistent with the conversation history and context.
    c. If you need to give examples of Blender instructions, please use the same format as in rule 2.

Example - When asked to generate Blender instructions, you should only return content in the following format:
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0))

4. Unless explicitly asked to reply in another language, always answer in Chinese.

Here are some introductions to my custom Blender APIs that you need to use when appropriate:
"""

class LLMToolProperties(PropertyGroup):
    """Properties for the LLM tool."""
    input_text: StringProperty(name="Input Text", default="")

def get_screenshots():
    """
    Get a list of screenshot file paths.

    Returns:
        list: A list of file paths to screenshots.
    """
    screenshots_path = r"D:\GPT_driven_modeling\resources\screenshots"
    return [
        os.path.join(screenshots_path, f)
        for f in os.listdir(screenshots_path)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
    ]

def initialize_conversation(context):
    """
    Initialize the conversation with the global prompt if not already present.

    Args:
        context (bpy.types.Context): The current Blender context.
    """
    conversation_manager = context.scene.conversation_manager
    if not any(msg.content == GLOBAL_PROMPT.strip() for msg in conversation_manager.messages):
        conversation_manager.add_message("system", GLOBAL_PROMPT.strip())

def encode_image(image_path):
    """
    Encode an image file to base64.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The base64 encoded image string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def is_valid_python(line):
    """
    Check if a line is valid Python code.

    Args:
        line (str): The line of code to check.

    Returns:
        bool: True if the line is valid Python, False otherwise.
    """
    try:
        # Try parsing as expression
        ast.parse(line, mode="eval")
        return True
    except SyntaxError:
        try:
            # Try parsing as statement
            ast.parse(line, mode="exec")
            return True
        except SyntaxError:
            # Check if it's an incomplete statement starting with certain keywords
            if re.match(r"^\s*(def|class|if|for|while|try|with|else|elif|return)", line):
                return True
            return False

def is_potential_multiline_start(line):
    """
    Check if a line potentially starts a multiline statement.

    Args:
        line (str): The line to check.

    Returns:
        bool: True if the line potentially starts a multiline statement, False otherwise.
    """
    return line.strip().endswith(("=", "[", "{", "("))

def sanitize_command(command):
    """
    Sanitize and format a Blender command string.

    Args:
        command (str): The command string to sanitize.

    Returns:
        str: The sanitized command string.
    """
    try:
        # Remove code block markers and language identifiers
        command = re.sub(
            r'^(```|"""|\'\'\')\s*(?:python)?\s*\n|(```|"""|\'\'\')\s*$',
            "",
            command,
            flags=re.MULTILINE | re.IGNORECASE,
        ).strip()

        # Remove potential standalone 'python' line
        lines = command.split("\n")
        if lines and lines[0].strip().lower() == "python":
            lines = lines[1:]

        cleaned_lines = []
        buffer = []
        i = 0
        in_multiline = False
        open_brackets = 0  # Track open brackets count

        while i < len(lines):
            current_line = lines[i].strip()

            # Replace special quotes and other characters
            current_line = (
                current_line.replace('"', '"')
                .replace('"', '"')
                .replace(""", "'").replace(""", "'")
            )
            current_line = (
                current_line.replace("，", ",").replace("：", ":").replace("；", ";")
            )

            # Preserve original indentation
            indent = len(lines[i]) - len(lines[i].lstrip())

            # Update bracket count
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

            if current_line.startswith("#") or not current_line:  # Comment or empty line
                if buffer and open_brackets == 0:
                    cleaned_lines.extend(buffer)
                    buffer = []
                    in_multiline = False
                cleaned_lines.append(" " * indent + current_line)
                i += 1
                continue

            if is_potential_multiline_start(current_line) or open_brackets > 0:
                in_multiline = True

            # Try adding new line and validate
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
                # If new line addition is invalid, save previous buffer first
                if buffer and open_brackets == 0:
                    cleaned_lines.extend(buffer)
                    buffer = []
                    in_multiline = False

                # Check current line separately
                if is_valid_python(current_line):
                    cleaned_lines.append(" " * indent + current_line)
                else:
                    cleaned_lines.append(f"# {' ' * indent + current_line}")
                i += 1

        # Handle potentially remaining buffer
        if buffer:
            cleaned_lines.extend(buffer)

        return "\n".join(cleaned_lines)
    except Exception as e:
        print(f"Error sanitizing command: {e}")
        return command

def get_scene_info():
    """
    Get information about objects in the current Blender scene.

    Returns:
        list: A list of dictionaries containing object information.
    """
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

            # Get material information
            materials = [
                slot.material.name for slot in obj.material_slots if slot.material
            ]
            obj_info["materials"] = materials

        scene_info.append(obj_info)
    return scene_info

def format_scene_info(scene_info):
    """
    Format scene information into a readable string.

    Args:
        scene_info (list): A list of dictionaries containing object information.

    Returns:
        str: A formatted string describing the scene.
    """
    formatted_info = "Scene Information:\n"
    for obj in scene_info:
        formatted_info += f"Object Name: {obj['name']}\n"
        formatted_info += f"  Type: {obj['type']}\n"
        formatted_info += f"  Location: {obj['location']}\n"
        formatted_info += f"  Rotation: {obj['rotation']}\n"
        formatted_info += f"  Scale: {obj['scale']}\n"
        formatted_info += f"  Dimensions:\n"
        formatted_info += f"    Length (X): {obj['dimensions'][0]:.3f}\n"
        formatted_info += f"    Width (Y): {obj['dimensions'][1]:.3f}\n"
        formatted_info += f"    Height (Z): {obj['dimensions'][2]:.3f}\n"
        if obj["type"] == "MESH":
            formatted_info += f"  Vertex Count: {obj['vertex_count']}\n"
            formatted_info += f"  Face Count: {obj['face_count']}\n"
            if obj["materials"]:
                formatted_info += f"  Materials: {', '.join(obj['materials'])}\n"
        formatted_info += "\n"
    return formatted_info

def execute_blender_command(command):
    """
    Execute a Blender command string.

    Args:
        command (str): The command string to execute.

    Raises:
        Exception: If the command execution fails.
    """
    try:
        sanitized_command = sanitize_command(command)
        logger.info(f"Executing sanitized command: {sanitized_command}")

        dedented_command = textwrap.dedent(sanitized_command)

        # Create a new global namespace
        exec_globals = {
            "__name__": "__main__",
            "__builtins__": __builtins__,
        }

        # Add a custom import function
        def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
            try:
                if name not in sys.modules:
                    importlib.import_module(name)
                return sys.modules[name]
            except ImportError as e:
                logger.error(f"Unable to import module {name}: {str(e)}")
                raise e

        exec_globals["__import__"] = custom_import

        # Execute the code
        exec(dedented_command, exec_globals)

        logger.info("Command executed successfully")
        return None  # Return None if execution is successful
    except Exception as e:
        error_message = f"Command execution failed: {str(e)}\n"
        error_message += f"Error type: {type(e).__name__}\n"
        error_message += f"Full error message:\n{traceback.format_exc()}"
        logger.error(error_message)
        raise  # Re-raise the exception to maintain consistency with original behavior

def execute_blender_command_with_error_handling(command):
    """
    Execute a Blender command with error handling.

    Args:
        command (str): The command string to execute.

    Returns:
        str or None: Error message if execution fails, None if successful.
    """
    try:
        execute_blender_command(command)
        return None
    except Exception as e:
        error_message = f"Command execution failed: {str(e)}\n"
        error_message += f"Error type: {type(e).__name__}\n"
        error_message += f"Full error message:\n{traceback.format_exc()}"
        return error_message

def add_history_to_prompt(context, prompt):
    """
    Add conversation history to the prompt.

    Args:
        context (bpy.types.Context): The current Blender context.
        prompt (str): The original prompt.

    Returns:
        str: The prompt with added conversation history.
    """
    conversation_manager = context.scene.conversation_manager
    conversation = "\n".join(
        [
            f"{message['role']}: {message['content']}"
            for message in conversation_manager.get_conversation_history()
        ]
    )
    return f"Conversation history:\n{conversation}\n\nIn the information I send you, I have included our past conversation history. Please try to reference previously mentioned information.\n\n{prompt}"