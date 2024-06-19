bl_info = {
    "name": "Basic GPT-4 Integration with Context",
    "blender": (3, 0, 0),
    "category": "3D View",
    "version": (1, 0, 0),
    "location": "View3D > Tool Shelf",
    "description": "Basic integration with GPT-4 for text output with context",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

import bpy
import os
import re
import logging
from openai import OpenAI
from dotenv import load_dotenv
from bpy.props import StringProperty, PointerProperty, CollectionProperty
from bpy.types import Panel, Operator, PropertyGroup

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/code/.env")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 定义全局提示词
GLOBAL_PROMPT = """
你将充当一个智能助手，需要根据用户的指令提供相应的回答。在执行任何操作时，请参考对话历史中提到的内容和上下文。请注意以下几点：

1. 所有的回答都应基于对话历史，并尽量参考之前提到过的信息。
2. 如果我明确要求生成 Blender 指令，返回的文本应仅包含 Blender 命令，不要包含任何额外的描述性文本、符号或注释。
3. 在没有明确要求生成 Blender 指令的情况下，你可以提供详细的回答和解释，但请确保回答的内容与对话历史和上下文一致。

例如，如果我要求生成 Blender 指令，你应返回：
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0))
"""

class GPTMessage(PropertyGroup):
    role: StringProperty(name="Role")
    content: StringProperty(name="Content")

class GPTProperties(PropertyGroup):
    input_text: StringProperty(
        name="Input Text",
        description="Enter text to send to GPT-4"
    )
    messages: CollectionProperty(type=GPTMessage)

def initialize_conversation(gpt_tool):
    # 检查对话历史中是否包含全局提示词，如果没有则添加
    if not any(msg.content == GLOBAL_PROMPT.strip() for msg in gpt_tool.messages):
        system_message = gpt_tool.messages.add()
        system_message.role = "system"
        system_message.content = GLOBAL_PROMPT.strip()

def generate_prompt(messages, current_instruction=None):
    conversation = "\n".join([f"{message['role']}: {message['content']}" for message in messages])
    prompt = f"历史对话记录如下：\n{conversation}"
    if current_instruction:
        prompt += f"\n在我发给你的信息中，包含了我和你过去的历史对话，请尽量参考之前提到过的信息，现在，请根据当前指令提供回答：\n{current_instruction}"
    return prompt

def generate_text(messages, current_instruction=None):
    try:
        prompt = generate_prompt(messages, current_instruction)
        print(prompt)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2560,
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating text from GPT-4: {e}")
        return "Error generating response from GPT-4."

def sanitize_command(command):
    try:
        # 移除Markdown代码块标记
        if command.startswith("```") and command.endswith("```"):
            command = command[3:-3].strip()
            if command.startswith("python"):
                command = command[6:].strip()
        # 移除所有非ASCII字符并处理引号问题
        sanitized_command = re.sub(r'[^\x00-\x7F]+', '', command)
        sanitized_command = sanitized_command.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        return sanitized_command
    except Exception as e:
        logger.error(f"Error sanitizing command: {e}")
        return command

def execute_blender_command(command):
    try:
        sanitized_command = sanitize_command(command)
        logger.info(f"Executing sanitized command: {sanitized_command}")
        exec(sanitized_command, {'bpy': bpy})
        logger.info("命令执行成功")
    except Exception as e:
        logger.error(f"命令执行失败: {e}")

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

# 定义要注册的类
classes = (
    GPTMessage,
    GPTProperties,
    OBJECT_OT_send_to_gpt,
    GPT_PT_panel,
)

def register():
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
        bpy.types.Scene.gpt_tool = PointerProperty(type=GPTProperties)  # 添加自定义属性组到场景
        # 初始化对话历史，确保包含全局提示词
        initialize_conversation(bpy.context.scene.gpt_tool)
        logger.info("Registered classes successfully.")
    except Exception as e:
        logger.error(f"Error registering classes: {e}")

def unregister():
    try:
        for cls in classes:
            bpy.utils.unregister_class(cls)
        del bpy.types.Scene.gpt_tool  # 从场景中删除自定义属性组
        logger.info("Unregistered classes successfully.")
    except Exception as e:
        logger.error(f"Error unregistering classes: {e}")

if __name__ == "__main__":
    register()
