import bpy
import os
import base64
import json
import logging
import sys
import codecs
import textwrap
import traceback
from bpy.types import Operator, PropertyGroup
from bpy.props import StringProperty, CollectionProperty
from anthropic import Anthropic
from dotenv import load_dotenv
from LLM_common_utils import *

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("ANTHROPIC_API_KEY")

class OBJECT_OT_send_to_claude(Operator):
    bl_idname = "object.send_to_claude"
    bl_label = "Send to Claude"

    def execute(self, context):
        try:
            scn = context.scene
            claude_tool = scn.claude_tool
            input_text = claude_tool.input_text
            
            if input_text:
                initialize_conversation(claude_tool)
                
                user_message = claude_tool.messages.add()
                user_message.role = "human"
                user_message.content = input_text
                
                messages = [{"role": msg.role, "content": msg.content} for msg in claude_tool.messages]
                logger.info(f"Messages: {messages}")
                
                client = Anthropic(api_key=api_key)
                
                message = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=2048,
                    messages=[
                        {
                            "role": "user",
                            "content": generate_prompt(messages, input_text)
                        }
                    ],
                )
                response_text = message.content[0].text
                
                logger.info(f"Claude Response: {response_text}")
                
                claude_message = claude_tool.messages.add()
                claude_message.role = "assistant"
                claude_message.content = response_text
                
                execute_blender_command(response_text)
            else:
                logger.warning("No input text provided.")
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_send_to_claude.execute: {str(e)}")
        return {'FINISHED'}

class OBJECT_OT_send_screenshots_to_claude(Operator):
    bl_idname = "object.send_screenshots_to_claude"
    bl_label = "Send Screenshots to Claude"

    def execute(self, context):
        try:
            scn = context.scene
            claude_tool = scn.claude_tool

            initialize_conversation(claude_tool)

            screenshots_path = os.path.join(os.path.dirname(__file__), 'screenshots')
            screenshots = [os.path.join(screenshots_path, f) for f in os.listdir(screenshots_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]

            client = Anthropic(api_key=api_key)

            content = []
            for i, screenshot in enumerate(screenshots, 1):
                base64_image = encode_image(screenshot)
                content.extend([
                    {"type": "text", "text": f"Image {i}:"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image,
                        },
                    }
                ])
            # 更新对话历史
            messages = [{"role": msg.role, "content": msg.content} for msg in claude_tool.messages]
            prompt = generate_screenshot_prompt(messages)
            content.append({"type": "text", "text": f"{prompt}"})

            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
            )

            output_text = message.content[0].text

            logger.info(f"Claude Response: {output_text}")

            claude_message = claude_tool.messages.add()
            claude_message.role = "assistant"
            claude_message.content = output_text

            execute_blender_command(output_text)

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error in OBJECT_OT_send_screenshots_to_claude.execute: {str(e)}")
            return {'CANCELLED'}

class CLAUDE_PT_panel(bpy.types.Panel):
    bl_label = "Claude Integration with Context"
    bl_idname = "CLAUDE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.claude_tool, "input_text")
        layout.operator("object.send_to_claude")
        layout.operator("object.send_screenshots_to_claude", text="Send Screenshots to Claude")