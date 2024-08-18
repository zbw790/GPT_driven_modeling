# gpt_module.py

import requests
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty
from src.llm_modules.LLM_common_utils import *

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def generate_text_with_context(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.8,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating text from GPT-4 with context: {e}")
        return "Error generating response from GPT-4."

def analyze_screenshots_with_gpt4(prompt, screenshots):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    image_messages = []
    for screenshot in screenshots:
        base64_image = encode_image(screenshot)
        view_name = os.path.splitext(os.path.basename(screenshot))[0]  # 获取文件名（不包括扩展名）
        image_messages.extend([
            {
                "type": "text",
                "text": f"视图角度: {view_name}"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "low"
                }
            }
        ])

    text_message = {
        "type": "text",
        "text": prompt
    }

    request_data = {
        "model": "gpt-4-turbo",
        "messages": [
            {
                "role": "user",
                "content": [text_message] + image_messages
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.8,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=request_data
    )
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

class OBJECT_OT_send_to_gpt(Operator):
    bl_idname = "object.send_to_gpt"
    bl_label = "Send to GPT-4"

    def execute(self, context):
        try:
            conversation_manager = context.scene.conversation_manager
            input_text = context.scene.llm_tool.input_text
            
            if input_text:
                initialize_conversation(context)
                
                conversation_manager.add_message("user", input_text)
                
                # 添加历史记录到提示
                prompt_with_history = add_history_to_prompt(context, input_text)
                
                response_text = generate_text_with_context(prompt_with_history)
                logger.info(f"GPT-4 Response: {response_text}")
                
                conversation_manager.add_message("assistant", response_text)
                
                execute_blender_command(response_text)
            else:
                logger.warning("No input text provided.")
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_send_to_gpt.execute: {e}")
        return {'FINISHED'}

class OBJECT_OT_send_screenshots_to_gpt(Operator):
    bl_idname = "object.send_screenshots_to_gpt"
    bl_label = "Send Screenshots to GPT"

    def execute(self, context):
        try:
            conversation_manager = context.scene.conversation_manager

            initialize_conversation(context)

            # 获取场景信息
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)

            # 构建 prompt
            prompt = f"""分析这些图片，描述你看到的3D模型。每张图片都标注了对应的视图角度。
            请在你的分析中引用这些视图名称，以便更清晰地描述模型的不同方面。
            指出任何可能的问题或需要改进的地方。
            以下是场景中对象的详细信息：{formatted_scene_info}
            请提供一个全面的分析，包括模型的整体形状、细节、比例和可能的用途。"""

            # 添加历史记录到提示
            prompt_with_history = add_history_to_prompt(context, prompt)

            # 获取截图
            screenshots = get_screenshots()

            # 分析截图和场景信息
            output_text = analyze_screenshots_with_gpt4(prompt_with_history, screenshots)
            logger.info(f"GPT-4 Response: {output_text}")

            # 将GPT-4响应添加到对话历史中
            conversation_manager.add_message("assistant", f"这是基于多个视角截图得到的场景分析:\n{output_text}")

            # 执行GPT-4生成的Blender指令
            execute_blender_command(output_text)

            return {'FINISHED'}
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_send_screenshots_to_gpt.execute: {e}")
            return {'CANCELLED'}

class OBJECT_OT_analyze_screenshots(Operator):
    bl_idname = "object.analyze_screenshots"
    bl_label = "Analyze Screenshots"

    def execute(self, context):
        try:
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)
            
            # 构建 prompt
            prompt = f"""分析这些图片，描述你看到的3D模型。每张图片都标注了对应的视图角度。
            请在你的分析中引用这些视图名称，以便更清晰地描述模型的不同方面。
            指出任何可能的问题或需要改进的地方。
            以下是场景中对象的详细信息：{formatted_scene_info}
            请提供一个全面的分析，包括模型的整体形状、细节、比例和可能的用途。"""
            
            # 添加历史记录到提示
            prompt_with_history = add_history_to_prompt(context, prompt)
            
            # 获取截图
            screenshots = get_screenshots()
            
            analysis_result = analyze_screenshots_with_gpt4(prompt_with_history, screenshots)
            logger.info(f"Screenshot Analysis Result: {analysis_result}")
            
            # 将分析结果添加到对话历史
            conversation_manager = context.scene.conversation_manager
            conversation_manager.add_message("assistant", f"这是基于多个视角截图得到的场景分析: {analysis_result}")
            
            # 可以选择是否执行分析结果
            # execute_blender_command(analysis_result)
            
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_analyze_screenshots.execute: {e}")
        return {'FINISHED'}

class GPT_PT_panel(Panel):
    bl_label = "GPT-4 Integration with Context"
    bl_idname = "GPT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.llm_tool, "input_text")
        layout.operator("object.send_to_gpt")
        layout.operator("object.analyze_screenshots", text="Analyze Screenshots")
        layout.operator("object.send_screenshots_to_gpt", text="Send Screenshots to GPT")