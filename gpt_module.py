import requests
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty, CollectionProperty
from LLM_common_utils import *

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def generate_text(messages, current_instruction=None):
    try:
        prompt = generate_prompt(messages, current_instruction)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2560,
            temperature=0.8,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating text from GPT-4: {e}")
        return "Error generating response from GPT-4."

class OBJECT_OT_send_to_gpt(Operator):
    bl_idname = "object.send_to_gpt"
    bl_label = "Send to GPT-4"

    def execute(self, context):
        try:
            scn = context.scene
            gpt_tool = scn.gpt_tool
            input_text = gpt_tool.input_text
            
            if input_text:
                # 初始化对话历史，确保包含全局提示词
                initialize_conversation(gpt_tool)
                
                # 将用户输入添加到对话历史中
                user_message = gpt_tool.messages.add()
                user_message.role = "user"
                user_message.content = input_text
                
                # 将对话历史转换为列表
                messages = [{"role": msg.role, "content": msg.content} for msg in gpt_tool.messages]
                logger.info(f"Messages: {messages}")
                
                # 生成GPT-4响应
                response_text = generate_text(messages, input_text)
                logger.info(f"GPT-4 Response: {response_text}")
                
                # 将GPT-4响应添加到对话历史中
                gpt_message = gpt_tool.messages.add()
                gpt_message.role = "assistant"
                gpt_message.content = response_text
                
                # 执行GPT-4生成的Blender指令
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
            scn = context.scene
            gpt_tool = scn.gpt_tool

            # 初始化对话历史，确保包含全局提示词
            initialize_conversation(gpt_tool)

            # 获取截图文件
            screenshots_path = os.path.join(os.path.dirname(__file__), 'screenshots')
            screenshots = [os.path.join(screenshots_path, f) for f in os.listdir(screenshots_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            image_messages = []

            for screenshot in screenshots:
                base64_image = encode_image(screenshot)
                image_messages.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "low"  # 设置图片清晰度
                        }
                    }
                )

            # 更新对话历史
            messages = [{"role": msg.role, "content": msg.content} for msg in gpt_tool.messages]

            # 创建提示
            prompt = generate_screenshot_prompt(messages)
            text_message = {
                "type": "text",
                "text": f"{prompt}"
            }

            # 构建请求数据
            request_data = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            text_message
                        ] + image_messages
                    }
                ],
                "max_tokens": 2560,
                "temperature": 0.8,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }

            # 发送请求到GPT-4
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=request_data
            )
            output_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"GPT-4 Response: {output_text}")

            # 将GPT-4响应添加到对话历史中
            gpt_message = gpt_tool.messages.add()
            gpt_message.role = "assistant"
            gpt_message.content = output_text

            # 执行GPT-4生成的Blender指令
            execute_blender_command(output_text)

            return {'FINISHED'}
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_send_screenshots_to_gpt.execut e: {e}")
            return {'CANCELLED'}
        
class GPT_PT_panel(Panel):
    bl_label = "GPT-4 Integration with Context"
    bl_idname = "GPT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.gpt_tool, "input_text")
        layout.operator("object.send_to_gpt")
        layout.operator("object.send_screenshots_to_gpt", text="Send Screenshots to GPT")
