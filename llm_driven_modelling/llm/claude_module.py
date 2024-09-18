# claude_module.py

"""
This module integrates Claude AI functionality into a Blender addon.
It provides capabilities for text generation, image analysis, and Blender scene manipulation using Claude AI.
"""

import bpy
import os
import logging
from bpy.types import Operator, Panel
from anthropic import Anthropic
from dotenv import load_dotenv
from .LLM_common_utils import *

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("ANTHROPIC_API_KEY")


def generate_text_with_claude(prompt):
    """
    Generate text using Claude AI based on the given prompt.

    Args:
        prompt (str): The input prompt for text generation.

    Returns:
        str: The generated text response.
    """
    try:
        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Error generating text from Claude with context: {e}")
        return "Error generating response from Claude."


def analyze_screenshots_with_claude(prompt, screenshots):
    """
    Analyze screenshots using Claude AI vision capabilities.

    Args:
        prompt (str): The text prompt for analysis.
        screenshots (list): List of screenshot file paths.

    Returns:
        str: The analysis result from Claude AI.
    """
    client = Anthropic(api_key=api_key)
    content = []
    for screenshot in screenshots:
        base64_image = encode_image(screenshot)
        view_name = os.path.splitext(os.path.basename(screenshot))[0]
        content.extend(
            [
                {"type": "text", "text": f"View angle: {view_name}"},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64_image,
                    },
                },
            ]
        )
    content.append({"type": "text", "text": prompt})
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )
    return message.content[0].text


class OBJECT_OT_send_to_claude(Operator):
    """Operator to send text input to Claude AI and process the response."""

    bl_idname = "object.send_to_claude"
    bl_label = "Send to Claude"

    def execute(self, context):
        try:
            conversation_manager = context.scene.conversation_manager
            input_text = context.scene.llm_tool.input_text
            if input_text:
                initialize_conversation(context)
                conversation_manager.add_message("human", input_text)
                prompt_with_history = add_history_to_prompt(context, input_text)
                response_text = generate_text_with_claude(prompt_with_history)
                logger.info(f"Claude Response: {response_text}")
                conversation_manager.add_message("assistant", response_text)
                execute_blender_command(response_text)
            else:
                logger.warning("No input text provided.")
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_send_to_claude.execute: {str(e)}")
        return {"FINISHED"}


class OBJECT_OT_send_screenshots_to_claude(Operator):
    """Operator to send screenshots to Claude AI for analysis."""

    bl_idname = "object.send_screenshots_to_claude"
    bl_label = "Send Screenshots to Claude"

    def execute(self, context):
        try:
            conversation_manager = context.scene.conversation_manager
            initialize_conversation(context)
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)
            prompt = f"""Analyze these images and describe the 3D model you see. Each image is labeled with its corresponding view angle.
            Please reference these view names in your analysis to clearly describe different aspects of the model.
            Point out any potential issues or areas for improvement.
            Here are the details of objects in the scene:

            {formatted_scene_info}

            Please provide a comprehensive analysis, including the model's overall shape, details, proportions, and possible uses."""
            prompt_with_history = add_history_to_prompt(context, prompt)
            screenshots = get_screenshots()
            output_text = analyze_screenshots_with_claude(
                prompt_with_history, screenshots
            )
            logger.info(f"Claude Response: {output_text}")
            conversation_manager.add_message(
                "assistant",
                f"Scene analysis based on multiple view screenshots:\n{output_text}",
            )
            execute_blender_command(output_text)
            return {"FINISHED"}
        except Exception as e:
            self.report(
                {"ERROR"},
                f"Error in OBJECT_OT_send_screenshots_to_claude.execute: {str(e)}",
            )
            return {"CANCELLED"}


class OBJECT_OT_analyze_screenshots_claude(Operator):
    """Operator to analyze screenshots without sending commands to Blender."""

    bl_idname = "object.analyze_screenshots_claude"
    bl_label = "Analyze Screenshots with Claude"

    def execute(self, context):
        try:
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)
            prompt = f"""Analyze these images and describe the 3D model you see. Each image is labeled with its corresponding view angle.
            Please reference these view names in your analysis to clearly describe different aspects of the model.
            Point out any potential issues or areas for improvement.
            Here are the details of objects in the scene:

            {formatted_scene_info}

            Please provide a comprehensive analysis, including the model's overall shape, details, proportions, and possible uses."""
            prompt_with_history = add_history_to_prompt(context, prompt)
            screenshots = get_screenshots()
            analysis_result = analyze_screenshots_with_claude(
                prompt_with_history, screenshots
            )
            logger.info(f"Screenshot Analysis Result: {analysis_result}")
            conversation_manager = context.scene.conversation_manager
            conversation_manager.add_message(
                "assistant",
                f"Scene analysis based on multiple view screenshots: {analysis_result}",
            )
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_analyze_screenshots_claude.execute: {e}")
        return {"FINISHED"}


class CLAUDE_PT_panel(Panel):
    """Panel for Claude AI integration in Blender."""

    bl_label = "Claude Integration with Context"
    bl_idname = "CLAUDE_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.llm_tool, "input_text")
        layout.operator("object.send_to_claude")
        layout.operator("object.analyze_screenshots_claude", text="Analyze Screenshots")
        layout.operator(
            "object.send_screenshots_to_claude", text="Send Screenshots to Claude"
        )
