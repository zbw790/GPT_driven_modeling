import bpy
import os
import math
import mathutils
from bpy.types import Panel, Operator
from bpy.props import FloatProperty, StringProperty

# 设置截图保存路径
SCREENSHOTS_PATH = r"D:\GPT_driven_modeling\resources\screenshots"

def ensure_camera():
    camera = bpy.context.scene.camera
    if camera is None:
        bpy.ops.object.camera_add()
        camera = bpy.context.object
        bpy.context.scene.camera = camera
    return camera

def calculate_scene_center_and_size(objects):
    if not objects:
        return mathutils.Vector((0, 0, 0)), 0

    min_corner, max_corner = calculate_combined_bounding_box(objects)
    center = mathutils.Vector([(min_corner[i] + max_corner[i]) / 2 for i in range(3)])
    size = max((max_corner[i] - min_corner[i]) for i in range(3))
    return center, size

def calculate_combined_bounding_box(objects):
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    
    for obj in objects:
        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        for corner in bbox_corners:
            min_x = min(min_x, corner.x)
            max_x = max(max_x, corner.x)
            min_y = min(min_y, corner.y)
            max_y = max(max_y, corner.y)
            min_z = min(min_z, corner.z)
            max_z = max(max_z, corner.z)
    
    return (min_x, min_y, min_z), (max_x, max_y, max_z)

def set_camera_position_and_rotation(camera, look_from, look_at):
    direction = look_at - look_from
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    camera.location = look_from

def add_label_to_object(obj, scene_size):
    # 计算物体的精确中心
    center = obj.location + obj.dimensions / 2

    # 创建新的文本对象
    bpy.ops.object.text_add(enter_editmode=False, location=(0, 0, 0))
    text_obj = bpy.context.active_object
    
    # 设置文本内容和属性
    text_obj.data.body = obj.name
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 调整文本大小为场景大小的 10%
    text_obj.data.size = scene_size * 0.06

    # 创建新材质并应用
    material = bpy.data.materials.new(name="Text_Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    # 设置为发光材质
    node_emission = nodes.new(type='ShaderNodeEmission')
    node_emission.inputs[0].default_value = (1, 1, 0, 1)  # 亮黄色
    node_emission.inputs[1].default_value = 2  # 发光强度
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(node_emission.outputs[0], node_output.inputs[0])

    # 将材质应用到文本对象
    if text_obj.data.materials:
        text_obj.data.materials[0] = material
    else:
        text_obj.data.materials.append(material)
    
    # 设置文本对象的原点为其边界框的中心
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    # 将文本移动到物体的精确中心
    text_obj.location = center
    
    # 使文本始终面向摄像机
    track_to = text_obj.constraints.new(type='TRACK_TO')
    track_to.target = bpy.context.scene.camera
    track_to.track_axis = 'TRACK_Z'
    track_to.up_axis = 'UP_Y'
    
    # 将文本对象设置为原始对象的子对象
    text_obj.parent = obj

    text_obj.show_in_front = True
    
    return text_obj


def remove_labels():
    for obj in bpy.data.objects:
        if obj.type == 'FONT':
            bpy.data.objects.remove(obj, do_unlink=True)

def save_screenshots(distance_factor=2.5):
    scene = bpy.context.scene

    # 保存原始设置
    original_resolution_x = scene.render.resolution_x
    original_resolution_y = scene.render.resolution_y
    original_resolution_percentage = scene.render.resolution_percentage
    original_camera = scene.camera

    # 保存原始 3D 视图设置
    original_view_settings = {}
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    original_view_settings[area] = {
                        'view_perspective': space.region_3d.view_perspective,
                        'view_matrix': space.region_3d.view_matrix.copy(),
                        'lock_camera': space.lock_camera,
                        'shading_type': space.shading.type  # 保存原始着色类型
                    }
                    break

    scene.render.resolution_x = 750
    scene.render.resolution_y = 750
    scene.render.resolution_percentage = 100

    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    if not mesh_objects:
        print("No mesh objects found in the scene")
        return

    if not os.path.exists(SCREENSHOTS_PATH):
        os.makedirs(SCREENSHOTS_PATH)

    camera = ensure_camera()
    center, size = calculate_scene_center_and_size(mesh_objects)

    # 设置相机的视野角度
    camera.data.angle = math.radians(50)

    # 计算相机距离
    camera_distance = size * distance_factor

    angles = [
        ((0, 0, 1), "俯视图"),
        ((0, 0, -1), "底视图"),
        ((-1, 0, 0), "左视图"),
        ((1, 0, 0), "右视图"),
        ((0, 1, 0), "后视图"),
        ((0, -1, 0), "前视图"),
        ((1, -1, 1), "右前上视图"),
        ((1, 1, -1), "右后下视图"),
    ]

    # 添加标签
    text_objects = [add_label_to_object(obj, size) for obj in mesh_objects]

    try:

        # 取消所有对象的选择
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = None
        
        for direction, view_name in angles:
            direction_vector = mathutils.Vector(direction).normalized()
            camera_position = center + direction_vector * camera_distance
            
            set_camera_position_and_rotation(camera, camera_position, center)
            
            bpy.context.view_layer.update()

            bpy.context.view_layer.objects.active = camera
            scene.camera = camera

            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    # 切换到材质预览模式
                    area.spaces[0].shading.type = 'MATERIAL'
                    area.spaces[0].region_3d.view_perspective = 'CAMERA'
                    break

            screenshot_path = os.path.join(SCREENSHOTS_PATH, f"{view_name}.png")
            scene.render.filepath = screenshot_path
            scene.render.image_settings.file_format = 'PNG'

            bpy.ops.render.opengl(write_still=True)

    finally:
        # 移除标签
        remove_labels()

        # 恢复原始设置
        scene.render.resolution_x = original_resolution_x
        scene.render.resolution_y = original_resolution_y
        scene.render.resolution_percentage = original_resolution_percentage
        scene.camera = original_camera

        # 恢复原始 3D 视图设置
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        if area in original_view_settings:
                            settings = original_view_settings[area]
                            space.region_3d.view_perspective = settings['view_perspective']
                            space.region_3d.view_matrix = settings['view_matrix']
                            space.lock_camera = settings['lock_camera']
                            space.shading.type = settings['shading_type']  # 恢复原始着色类型
                        break

    print(f"Screenshots saved to {SCREENSHOTS_PATH}")

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

class SaveScreenshotOperator(Operator):
    bl_idname = "model_viewer.save_screenshot"
    bl_label = "Save Screenshot"

    def execute(self, context):
        save_screenshots(distance_factor=2.5)
        return {'FINISHED'}

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
        row.prop(scene, "model_scale_percentage", text="Scale (%)")
        row = layout.row()
        row.label(text=f"Dimensions: {scene.model_dimensions}")
        row = layout.row()
        row.operator("model_viewer.apply_scale", text="Apply Scale")
        row = layout.row()
        row.operator("model_viewer.save_screenshot", text="Save Screenshot")