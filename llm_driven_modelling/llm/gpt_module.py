# gpt_module.py

"""
This module integrates GPT-4 functionality into a Blender addon.
It provides capabilities for text generation, image analysis, and Blender scene manipulation.
"""

import requests
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty
from llm_driven_modelling.llm.LLM_common_utils import (
    encode_image,
    initialize_conversation,
    add_history_to_prompt,
    get_scene_info,
    format_scene_info,
    get_screenshots,
    execute_blender_command,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def generate_text_with_context(prompt):
    """
    Generate text using GPT-4 based on the given prompt.

    Args:
        prompt (str): The input prompt for text generation.

    Returns:
        str: The generated text response.
    """
    try:
        response = client.chat.completions.create(
            model="o1-preview",
            messages=[{"role": "user", "content": prompt}],
            # Additional parameters can be uncommented and adjusted as needed
            # max_tokens=4096,
            # temperature=0.8,
            # top_p=1,
            # frequency_penalty=0,
            # presence_penalty=0
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating text from GPT-4 with context: {e}")
        return "Error generating response from GPT-4."


def analyze_screenshots_with_gpt4(prompt, screenshots):
    """
    Analyze screenshots using GPT-4 vision capabilities.

    Args:
        prompt (str): The text prompt for analysis.
        screenshots (list): List of screenshot file paths.

    Returns:
        str: The analysis result from GPT-4.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    image_messages = []
    for screenshot in screenshots:
        base64_image = encode_image(screenshot)
        view_name = os.path.splitext(os.path.basename(screenshot))[0]
        image_messages.extend(
            [
                {"type": "text", "text": f"View angle: {view_name}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                        "detail": "low",
                    },
                },
            ]
        )

    text_message = {"type": "text", "text": prompt}

    request_data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": [text_message] + image_messages}],
        "max_tokens": 4096,
        "temperature": 0.8,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=request_data
    )
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")


class OBJECT_OT_send_to_gpt(Operator):
    """Operator to send text input to GPT-4 and process the response."""

    bl_idname = "object.send_to_gpt"
    bl_label = "Send to GPT-4"

    def execute(self, context):
        try:
            conversation_manager = context.scene.conversation_manager
            input_text = context.scene.llm_tool.input_text

            if input_text:
                initialize_conversation(context)
                conversation_manager.add_message("user", input_text)
                prompt_with_history = add_history_to_prompt(context, input_text)
                response_text = generate_text_with_context(prompt_with_history)
                logger.info(f"GPT-4 Response: {response_text}")
                conversation_manager.add_message("assistant", response_text)
                execute_blender_command(response_text)
            else:
                logger.warning("No input text provided.")
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_send_to_gpt.execute: {e}")
        return {"FINISHED"}


class OBJECT_OT_send_screenshots_to_gpt(Operator):
    """Operator to send screenshots to GPT-4 for analysis."""

    bl_idname = "object.send_screenshots_to_gpt"
    bl_label = "Send Screenshots to GPT"

    def execute(self, context):
        try:
            conversation_manager = context.scene.conversation_manager
            initialize_conversation(context)
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)

            prompt = f"""Analyze these images and describe the 3D model you see. Each image is labeled with its corresponding view angle.
            Please reference these view names in your analysis to clearly describe different aspects of the model.
            Point out any potential issues or areas for improvement.
            Here are the details of objects in the scene: {formatted_scene_info}
            Please provide a comprehensive analysis, including the model's overall shape, details, proportions, and possible uses."""

            prompt_with_history = add_history_to_prompt(context, prompt)
            screenshots = get_screenshots()
            output_text = analyze_screenshots_with_gpt4(
                prompt_with_history, screenshots
            )
            logger.info(f"GPT-4 Response: {output_text}")
            conversation_manager.add_message(
                "assistant",
                f"Scene analysis based on multiple view screenshots:\n{output_text}",
            )
            execute_blender_command(output_text)
            return {"FINISHED"}
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_send_screenshots_to_gpt.execute: {e}")
            return {"CANCELLED"}


class OBJECT_OT_analyze_screenshots(Operator):
    """Operator to analyze screenshots without sending commands to Blender."""

    bl_idname = "object.analyze_screenshots"
    bl_label = "Analyze Screenshots"

    def execute(self, context):
        try:
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)
            prompt = f"""Analyze these images and describe the 3D model you see. Each image is labeled with its corresponding view angle.
            Please reference these view names in your analysis to clearly describe different aspects of the model.
            Point out any potential issues or areas for improvement.
            Here are the details of objects in the scene: {formatted_scene_info}
            Please provide a comprehensive analysis, including the model's overall shape, details, proportions, and possible uses."""

            prompt_with_history = add_history_to_prompt(context, prompt)
            screenshots = get_screenshots()
            analysis_result = analyze_screenshots_with_gpt4(
                prompt_with_history, screenshots
            )
            logger.info(f"Screenshot Analysis Result: {analysis_result}")
            conversation_manager = context.scene.conversation_manager
            conversation_manager.add_message(
                "assistant",
                f"Scene analysis based on multiple view screenshots: {analysis_result}",
            )
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_analyze_screenshots.execute: {e}")
        return {"FINISHED"}


class GPT_PT_panel(Panel):
    """Panel for GPT-4 integration in Blender."""

    bl_label = "GPT-4 Integration with Context"
    bl_idname = "GPT_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.llm_tool, "input_text")
        layout.operator("object.send_to_gpt")
        layout.operator("object.analyze_screenshots", text="Analyze Screenshots")
        layout.operator(
            "object.send_screenshots_to_gpt", text="Send Screenshots to GPT"
        )
