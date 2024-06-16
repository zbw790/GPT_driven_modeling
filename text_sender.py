bl_info = {
    "name": "Text Input Test",
    "blender": (2, 80, 0),
    "category": "3D View",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Tool Shelf",
    "description": "Text Input with Send Button",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

import bpy

class MyProperties(bpy.types.PropertyGroup):
    my_string : bpy.props.StringProperty(name="Input Text", description="Enter some text here")
bl_info = {
    "name": "GPT-4 Model Adder with Streaming",
    "blender": (3, 0, 0),
    "category": "3D View",
    "version": (1, 0, 0),
    "location": "View3D > Tool Shelf",
    "description": "Add a new model based on GPT-4 input with streaming support",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

import bpy
import os
import re
import openai
from openai import OpenAI
from bpy.props import StringProperty, PointerProperty
from bpy.types import Panel, Operator, PropertyGroup
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/code/.env")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
openai.api_key = api_key

class GPTProperties(PropertyGroup):
    input_text: StringProperty(
        name="Input Text",
        description="Enter command to add a new model"
    )

class OBJECT_OT_gpt_button(Operator):
    bl_idname = "object.gpt_button"
    bl_label = "Add Model"

    def sanitize_command(self, command):
        sanitized_command = re.sub(r'[^\x00-\x7F]+', '', command)
        sanitized_command = sanitized_command.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        return sanitized_command

    def execute_blender_command(self, command):
        try:
            sanitized_command = self.sanitize_command(command)
            exec(sanitized_command, {'bpy': bpy})
            self.report({'INFO'}, "Model added successfully")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add model: {e}")

    def execute(self, context):
        scn = context.scene
        input_text = scn.gpt_tool.input_text
        prompt = f"生成一个Blender命令来添加一个模型：{input_text}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2560,
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stream=True
        )

        command_buffer = ""
        try:
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    command_buffer += chunk.choices[0].delta.content
                    if '\n' in command_buffer:
                        commands = command_buffer.split('\n')
                        for cmd in commands[:-1]:
                            self.execute_blender_command(cmd)
                        command_buffer = commands[-1]
            # 处理剩余的命令
            if command_buffer:
                self.execute_blender_command(command_buffer)
        except Exception as e:
            self.report({'ERROR'}, f"Streaming error: {e}")

        return {'FINISHED'}

class GPT_PT_panel(Panel):
    bl_label = "GPT-4 Model Adder with Streaming"
    bl_idname = "GPT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.gpt_tool, "input_text")
        layout.operator(OBJECT_OT_gpt_button.bl_idname)

classes = (
    GPTProperties,
    OBJECT_OT_gpt_button,
    GPT_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gpt_tool = PointerProperty(type=GPTProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gpt_tool

if __name__ == "__main__":
    register()


class OBJECT_OT_send_button(bpy.types.Operator):
    bl_idname = "object.send_button"
    bl_label = "Send"

    def execute(self, context):
        scn = context.scene
        print(scn.my_tool.my_string)
        return {'FINISHED'}


class TEXT_PT_panel(bpy.types.Panel):
    bl_label = "Text Input Panel"
    bl_idname = "TEXT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.my_tool, "my_string")
        layout.operator(OBJECT_OT_send_button.bl_idname)


classes = (
    MyProperties,
    OBJECT_OT_send_button,
    TEXT_PT_panel,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()