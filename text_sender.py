bl_info = {
    "name": "GPT-4 Model Adder with Streaming",  # 插件名称
    "blender": (3, 0, 0),  # 支持的Blender版本
    "category": "3D View",  # 插件分类
    "version": (1, 0, 0),  # 插件版本
    "location": "View3D > Tool Shelf",  # 插件位置
    "description": "Add a new model based on GPT-4 input with streaming support",  # 插件描述
    "warning": "",  # 插件警告信息
    "wiki_url": "",  # 插件文档URL
    "tracker_url": "",  # 插件问题追踪URL
}

import bpy  # 导入Blender的Python接口
import os  # 导入操作系统接口
import re  # 导入正则表达式库
import openai  # 导入OpenAI接口
from openai import OpenAI  # 从OpenAI库中导入OpenAI类
from bpy.props import StringProperty, PointerProperty  # 导入Blender属性定义
from bpy.types import Panel, Operator, PropertyGroup  # 导入Blender类型
from dotenv import load_dotenv  # 导入dotenv库以加载环境变量

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/code/.env")
api_key = os.getenv("OPENAI_API_KEY")  # 从环境变量中获取API密钥
client = OpenAI(api_key=api_key)  # 创建OpenAI客户端
openai.api_key = api_key  # 设置OpenAI API密钥

class GPTProperties(PropertyGroup):
    input_text: StringProperty(
        name="Input Text",  # 属性名称
        description="Enter command to add a new model"  # 属性描述
    )
    my_string: StringProperty(
        name="Input Text",  # 属性名称
        description="Enter some text here"  # 属性描述
    )

class OBJECT_OT_gpt_button(Operator):
    bl_idname = "object.gpt_button"  # 操作ID
    bl_label = "Add Model"  # 操作标签

    def sanitize_command(self, command):
        sanitized_command = re.sub(r'[^\x00-\x7F]+', '', command)  # 移除非ASCII字符
        sanitized_command = sanitized_command.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")  # 替换特殊引号
        return sanitized_command

    def execute_blender_command(self, command):
        try:
            sanitized_command = self.sanitize_command(command)  # 清理命令
            exec(sanitized_command, {'bpy': bpy})  # 执行Blender命令
            self.report({'INFO'}, "Model added successfully")  # 报告成功信息
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add model: {e}")  # 报告错误信息

    def execute(self, context):
        scn = context.scene
        input_text = scn.gpt_tool.input_text  # 获取用户输入的文本
        prompt = f"生成一个Blender命令来添加一个模型：{input_text}"  # 创建提示文本

        response = client.chat.completions.create(
            model="gpt-4",  # 使用GPT-4模型
            messages=[{"role": "user", "content": prompt}],  # 发送用户消息
            max_tokens=2560,  # 最大令牌数
            temperature=1,  # 采样温度
            top_p=1,  # 核心采样参数
            frequency_penalty=0,  # 频率惩罚
            presence_penalty=0,  # 存在惩罚
            stream=True  # 启用流式响应
        )

        command_buffer = ""
        try:
            for chunk in response:  # 处理流式响应
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
            self.report({'ERROR'}, f"Streaming error: {e}")  # 报告流式错误

        return {'FINISHED'}

class OBJECT_OT_send_button(Operator):
    bl_idname = "object.send_button"  # 操作ID
    bl_label = "Send"  # 操作标签

    def execute(self, context):
        scn = context.scene
        print(scn.gpt_tool.my_string)  # 打印用户输入的文本
        return {'FINISHED'}

class GPT_PT_panel(Panel):
    bl_label = "GPT-4 Model Adder with Streaming"  # 面板标签
    bl_idname = "GPT_PT_panel"  # 面板ID
    bl_space_type = 'VIEW_3D'  # 面板空间类型
    bl_region_type = 'UI'  # 面板区域类型
    bl_category = 'Tool'  # 面板分类

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.gpt_tool, "input_text")  # 添加输入框
        layout.operator(OBJECT_OT_gpt_button.bl_idname)  # 添加按钮操作

class TEXT_PT_panel(Panel):
    bl_label = "Text Input Panel"  # 面板标签
    bl_idname = "TEXT_PT_panel"  # 面板ID
    bl_space_type = 'VIEW_3D'  # 面板空间类型
    bl_region_type = 'UI'  # 面板区域类型
    bl_category = 'Tool'  # 面板分类
    
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.gpt_tool, "my_string")  # 添加输入框
        layout.operator(OBJECT_OT_send_button.bl_idname)  # 添加按钮操作

# 定义要注册的类
classes = (
    GPTProperties,
    OBJECT_OT_gpt_button,
    GPT_PT_panel,
    OBJECT_OT_send_button,
    TEXT_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)  # 注册类
    bpy.types.Scene.gpt_tool = PointerProperty(type=GPTProperties)  # 在场景中添加自定义属性

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)  # 注销类
    del bpy.types.Scene.gpt_tool  # 删除自定义属性

if __name__ == "__main__":
    register()  # 执行注册函数
