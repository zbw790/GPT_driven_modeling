import bpy
import os
import logging
from bpy.types import Operator, PropertyGroup
from bpy.props import StringProperty, CollectionProperty
from anthropic import Anthropic
from dotenv import load_dotenv
from LLM_common_utils import *

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("ANTHROPIC_API_KEY")

def generate_text_with_claude(messages, current_instruction):
    try:
        client = Anthropic(api_key=api_key)
        
        prompt = generate_prompt(messages, current_instruction)
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        
        return message.content[0].text
    except Exception as e:
        logger.error(f"Error generating text from Claude with context: {e}")
        return "Error generating response from Claude."

def analyze_screenshots_with_claude(prompt):
    client = Anthropic(api_key=api_key)
    
    # 在函数内部获取截图
    screenshots_path = os.path.join(os.path.dirname(__file__), 'screenshots')
    screenshots = [os.path.join(screenshots_path, f) for f in os.listdir(screenshots_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]

    content = []
    for screenshot in screenshots:
        base64_image = encode_image(screenshot)
        view_name = os.path.splitext(os.path.basename(screenshot))[0]  # 获取文件名（不包括扩展名）
        content.extend([
            {"type": "text", "text": f"视图角度: {view_name}"},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_image,
                },
            }
        ])
    
    content.append({"type": "text", "text": prompt})

    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    return message.content[0].text

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
                
                response_text = generate_text_with_claude(messages, input_text)
                
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

            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)

            prompt = f"""分析这些图片，描述你看到的3D模型。每张图片都标注了对应的视图角度。
            请在你的分析中引用这些视图名称，以便更清晰地描述模型的不同方面。
            指出任何可能的问题或需要改进的地方。
            以下是场景中对象的详细信息：

            {formatted_scene_info}

            请提供一个全面的分析，包括模型的整体形状、细节、比例和可能的用途。"""

            output_text = analyze_screenshots_with_claude(prompt)

            logger.info(f"Claude Response: {output_text}")

            claude_message = claude_tool.messages.add()
            claude_message.role = "assistant"
            claude_message.content = f"这是基于多个视角截图得到的场景分析:\n{output_text}"

            execute_blender_command(output_text)

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error in OBJECT_OT_send_screenshots_to_claude.execute: {str(e)}")
            return {'CANCELLED'}

class OBJECT_OT_analyze_screenshots_claude(Operator):
    bl_idname = "object.analyze_screenshots_claude"
    bl_label = "Analyze Screenshots with Claude"

    def execute(self, context):
        try:
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)
            
            prompt = f"""分析这些图片，描述你看到的3D模型。每张图片都标注了对应的视图角度。
            请在你的分析中引用这些视图名称，以便更清晰地描述模型的不同方面。
            指出任何可能的问题或需要改进的地方。
            以下是场景中对象的详细信息：

            {formatted_scene_info}

            请提供一个全面的分析，包括模型的整体形状、细节、比例和可能的用途。"""
            
            analysis_result = analyze_screenshots_with_claude(prompt)
            logger.info(f"Screenshot Analysis Result: {analysis_result}")
            
            # 将分析结果添加到对话历史
            claude_tool = context.scene.claude_tool
            claude_message = claude_tool.messages.add()
            claude_message.role = "assistant"
            claude_message.content = f"这是基于多个视角截图得到的场景分析: {analysis_result}"
            
            # 可以选择是否执行分析结果
            # execute_blender_command(analysis_result)
            
        except Exception as e:
            logger.error(f"Error in OBJECT_OT_analyze_screenshots_claude.execute: {e}")
        return {'FINISHED'}

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
        layout.operator("object.analyze_screenshots_claude", text="Analyze Screenshots")
        layout.operator("object.send_screenshots_to_claude", text="Send Screenshots to Claude")