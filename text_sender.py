import bpy
import os
import re
import logging
import math
import mathutils
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
        prompt += f"\n在我发给你的信息中，包含了我和你过去的历史对话，请尽量参考之前提到过的信息。现在，请根据当前指令提供回答：\n{current_instruction}"
    return prompt

def generate_text(messages, current_instruction=None):
    try:
        prompt = generate_prompt(messages, current_instruction)
        print(prompt)
        response = client.chat.completions.create(
            model="gpt-4o",
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

# 额外功能：Model 操作和相机设置

def reset_mesh_origin_to_bbx_center():
    selected_objects = bpy.context.selected_objects

    for obj in selected_objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.location_clear()
        bbx_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        bbx_center = sum(bbx_corners, mathutils.Vector()) / 8
        bpy.context.scene.cursor.location = bbx_center
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')
        obj.location = (0, 0, 0)
    bpy.context.scene.cursor.location = (0, 0, 0)

def move_camera_backwards_by_percentage(percentage):
    scene = bpy.context.scene
    camera = scene.camera
    selected_obj = bpy.context.selected_objects[0]
    bbx_radius = max(selected_obj.dimensions) / 2
    move_distance = bbx_radius * percentage
    camera_direction = camera.matrix_world.to_quaternion() @ mathutils.Vector((0.0, 0.0, -1.0))
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs['Color'].default_value = (1, 1, 1, 1)
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs['Strength'].default_value = 1
    camera.data.clip_start = bbx_radius * 0.1
    camera.data.clip_end = bbx_radius * 100
    camera.data.lens = 100

def reset_camera(objects, camera):
    bpy.context.scene.camera = camera
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            area.spaces[0].lock_camera = True
            break
    bpy.ops.view3d.camera_to_view_selected()
    move_camera_backwards_by_percentage(-0.1)

class RotateObjectCW_Z(Operator):
    bl_idname = "model_viewer.rotate_object_cw_z"
    bl_label = "Rotate Object CW (Z)"

    def execute(self, context):
        for obj in context.selected_objects:
            obj.rotation_euler.z += math.radians(90)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

class RotateObjectCW_X(Operator):
    bl_idname = "model_viewer.rotate_object_cw_x"
    bl_label = "Rotate Object CW (X)"

    def execute(self, context):
        for obj in context.selected_objects:
            obj.rotation_euler.x += math.radians(90)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

class RotateObjectCW_Y(Operator):
    bl_idname = "model_viewer.rotate_object_cw_y"
    bl_label = "Rotate Object CW (Y)"

    def execute(self, context):
        for obj in context.selected_objects:
            obj.rotation_euler.y += math.radians(90)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}
    
class RotateObjectCW_X_Degree(Operator):
    bl_idname = "model_viewer.rotate_object_cw_x_degree"
    bl_label = "Rotate Object CW (X) by Degree"

    def execute(self, context):
        degree = context.scene.rotation_degree
        for obj in context.selected_objects:
            obj.rotation_euler.x += math.radians(degree)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

class RotateObjectCW_Y_Degree(Operator):
    bl_idname = "model_viewer.rotate_object_cw_y_degree"
    bl_label = "Rotate Object CW (Y) by Degree"

    def execute(self, context):
        degree = context.scene.rotation_degree
        for obj in context.selected_objects:
            obj.rotation_euler.y += math.radians(degree)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

class RotateObjectCW_Z_Degree(Operator):
    bl_idname = "model_viewer.rotate_object_cw_z_degree"
    bl_label = "Rotate Object CW (Z) by Degree"

    def execute(self, context):
        degree = context.scene.rotation_degree
        for obj in context.selected_objects:
            obj.rotation_euler.z += math.radians(degree)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

class ResetObjectLocation(Operator):
    bl_idname = "model_viewer.reset_object_location"
    bl_label = "Reset Object Location"

    def execute(self, context):
        reset_mesh_origin_to_bbx_center()
        return {'FINISHED'}

class ApplyScale(Operator):
    bl_idname = "model_viewer.apply_scale"
    bl_label = "Apply Scale"

    def execute(self, context):
        scale_percentage = context.scene.model_scale_percentage
        scale_factor = scale_percentage / 100

        for obj in context.selected_objects:
            obj.scale = (scale_factor, scale_factor, scale_factor)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        if context.selected_objects:
            dimensions = context.selected_objects[0].dimensions
            context.scene.model_dimensions = f"{dimensions.x:.2f} x {dimensions.y:.2f} x {dimensions.z:.2f}"

        context.scene.model_scale_percentage = 100
        return {'FINISHED'}

def update_model_dimensions(self, context):
    scale_percentage = context.scene.model_scale_percentage
    scale_factor = scale_percentage / 100

    for obj in context.selected_objects:
        dimensions = obj.dimensions
        scaled_dimensions = dimensions * scale_factor
        context.scene.model_dimensions = f"{scaled_dimensions.x:.2f} x {scaled_dimensions.y:.2f} x {scaled_dimensions.z:.2f}"

class ModelViewerPanel(Panel):
    bl_label = "Model Viewer"
    bl_idname = "OBJECT_PT_model_viewer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.operator("model_viewer.rotate_object_cw_z", text="顺时针90 (Z)")
        row.operator("model_viewer.rotate_object_cw_x", text="顺时针90 (X)")
        row.operator("model_viewer.rotate_object_cw_y", text="顺时针90 (Y)")
        layout.operator("model_viewer.reset_object_location", text="重置中心")

        row = layout.row()
        row.prop(scene, "model_scale_percentage", text="Scale (%)")

        row = layout.row()
        row.label(text=f"Dimensions: {scene.model_dimensions}")

        row = layout.row()
        row.operator("model_viewer.apply_scale", text="Apply Scale")

        row = layout.row()
        row.prop(scene, "rotation_degree", text="Rotation Degree")
        row = layout.row()
        row.operator("model_viewer.rotate_object_cw_x_degree", text="Rotate X")
        row.operator("model_viewer.rotate_object_cw_y_degree", text="Rotate Y")
        row.operator("model_viewer.rotate_object_cw_z_degree", text="Rotate Z")


# 注册和注销类
classes = (
    GPTMessage,
    GPTProperties,
    OBJECT_OT_send_to_gpt,
    GPT_PT_panel,
    RotateObjectCW_X,
    RotateObjectCW_Y,
    RotateObjectCW_Z,
    RotateObjectCW_X_Degree,
    RotateObjectCW_Y_Degree,
    RotateObjectCW_Z_Degree,
    ResetObjectLocation,
    ApplyScale,
    ModelViewerPanel,
)

def register():
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
        bpy.types.Scene.gpt_tool = PointerProperty(type=GPTProperties)  # 添加自定义属性组到场景
        bpy.types.Scene.model_scale_percentage = bpy.props.FloatProperty(
            name="Model Scale Percentage",
            default=100.0,
            min=0.01,
            max=10000.0,
            update=update_model_dimensions
        )
        bpy.types.Scene.model_dimensions = bpy.props.StringProperty(
            name="Model Dimensions",
            default=""
        )
        bpy.types.Scene.rotation_degree = bpy.props.FloatProperty(
            name="Rotation Degree",
            description="Degree of rotation",
            default=0.0
        )
        logger.info("Registered classes successfully.")
    except Exception as e:
        logger.error(f"Error registering classes: {e}")

def unregister():
    try:
        for cls in classes:
            bpy.utils.unregister_class(cls)
        del bpy.types.Scene.gpt_tool
        del bpy.types.Scene.model_scale_percentage
        del bpy.types.Scene.model_dimensions
        del bpy.types.Scene.rotation_degree
        logger.info("Unregistered classes successfully.")
    except Exception as e:
        logger.error(f"Error unregistering classes: {e}")

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
