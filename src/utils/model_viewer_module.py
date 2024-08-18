# model_viewer_module.py

import bpy
import os
import math
import mathutils
from bpy.types import Panel, Operator
from bpy.props import FloatProperty, StringProperty
from bpy_extras.object_utils import world_to_camera_view
import bmesh

def ensure_camera():
    if bpy.context.scene.camera is None:
        existing_camera = bpy.data.objects.get("camera")
        if existing_camera:
            camera = existing_camera
        else:
            bpy.ops.object.camera_add()
            camera = bpy.context.object
            camera.name = "camera"
        bpy.context.scene.camera = camera
    else:
        camera = bpy.context.scene.camera
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

def add_label_to_object(obj, camera, scene_size, up_vector):
    # 检查物体是否在相机视图中可见
    is_visible, visible_point = is_object_visible(obj, camera)
    if not is_visible:
        return None

    # 使用可见点而不是物体的实际原点
    center = visible_point

    # 创建新的文本对象
    bpy.ops.object.text_add(enter_editmode=False, location=(0, 0, 0))
    text_obj = bpy.context.active_object
    
    # 设置文本内容和属性
    text_obj.data.body = obj.name
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 计算摄像机到可见点的方向向量
    direction = center - camera.location
    direction_length = direction.length
    direction.normalize()
    
    # 计算文本位置（在可见点和摄像机之间的30%处）
    text_position = camera.location + direction * (direction_length * 0.7)
    
    # 设置文本位置
    text_obj.location = text_position
    
    # 根据到摄像机的距离调整文本大小
    distance_to_camera = (text_position - camera.location).length
    text_obj.data.size = scene_size * 0.02 * (distance_to_camera / scene_size)

    # 创建新材质并应用
    material = bpy.data.materials.new(name="Text_Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    # 设置为发光材质
    node_emission = nodes.new(type='ShaderNodeEmission')
    node_emission.inputs[0].default_value = (1, 0, 0, 1)  # 红色
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
    
    # 计算文本的旋转
    forward = camera.location - text_position
    forward.normalize()
    right = forward.cross(up_vector)
    right.normalize()
    up = right.cross(forward)
    
    # 使用四元数计算旋转
    rot_matrix = mathutils.Matrix((-right, up, forward)).to_3x3()
    quat = rot_matrix.to_quaternion()
    quat.invert()
    
    # 应用旋转和位置
    text_obj.rotation_mode = 'QUATERNION'
    text_obj.rotation_quaternion = quat
    text_obj.location = text_position

    text_obj.show_in_front = True
    
    return text_obj

def is_object_visible(obj, camera):
    def check_point(point):
        co_ndc = world_to_camera_view(bpy.context.scene, camera, point)
        if 0 <= co_ndc.x <= 1 and 0 <= co_ndc.y <= 1 and 0 < co_ndc.z:
            direction = point - camera.location
            depsgraph = bpy.context.evaluated_depsgraph_get()
            
            offsets = [
                mathutils.Vector((0, 0, 0)),
                mathutils.Vector((0.001, 0.001, 0.001)),
                mathutils.Vector((-0.001, -0.001, -0.001))
            ]
            
            for offset in offsets:
                ray_origin = camera.location + offset
                ray_cast_result = bpy.context.scene.ray_cast(depsgraph, ray_origin, direction.normalized())
                if ray_cast_result[0] and ray_cast_result[4] == obj:
                    return True
        return False

    # 首先检查物体的中心
    center = obj.location
    if check_point(center):
        return True, center.copy()

    # 如果中心点不可见，创建一个bmesh来访问物体的实际几何形状
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)

    result = False, None

    # 检查所有顶点
    for v in bm.verts:
        if check_point(v.co):
            result = True, v.co.copy()
            break

    # 如果顶点检查失败，检查所有边的中点
    if not result[0]:
        for e in bm.edges:
            mid_point = (e.verts[0].co + e.verts[1].co) / 2
            if check_point(mid_point):
                result = True, mid_point.copy()
                break

    # 如果边检查失败，检查所有面的中心
    if not result[0]:
        for f in bm.faces:
            face_center = f.calc_center_median()
            if check_point(face_center):
                result = True, face_center.copy()
                break

    bm.free()  # 释放 BMesh
    return result

def remove_labels():
    for obj in bpy.data.objects:
        if obj.type == 'FONT':
            bpy.data.objects.remove(obj, do_unlink=True)

def _save_screenshots_common(output_path, distance_factor=2.5):
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
                        'shading_type': space.shading.type
                    }
                    break

    scene.render.resolution_x = 750
    scene.render.resolution_y = 750
    scene.render.resolution_percentage = 100

    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    if not mesh_objects:
        print("No mesh objects found in the scene")
        return []

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    camera = ensure_camera()
    center, size = calculate_scene_center_and_size(mesh_objects)

    camera.data.angle = math.radians(50)
    camera_distance = size * distance_factor

    angles = [
        ((0, 0, 1), "俯视图", (0, 1, 0)),
        ((0, 0, -1), "底视图", (0, 1, 0)),
        ((-1, 0, 0), "左视图", (0, 0, 1)),
        ((1, 0, 0), "右视图", (0, 0, 1)),
        ((0, 1, 0), "后视图", (0, 0, 1)),
        ((0, -1, 0), "前视图", (0, 0, 1)),
        ((1, -1, 1), "右前上视图", (0, 0, 1)),
        ((1, 1, -1), "右后下视图", (0, 0, 1)),
    ]

    screenshot_paths = []

    try:
        for direction, view_name, up_vector in angles:
            # 取消所有对象的选择
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = None

            direction_vector = mathutils.Vector(direction).normalized()
            camera_position = center + direction_vector * camera_distance
            
            set_camera_position_and_rotation(camera, camera_position, center)
            
            bpy.context.view_layer.update()

            bpy.context.view_layer.objects.active = camera
            scene.camera = camera

            # 添加标签
            text_objects = [add_label_to_object(obj, camera, size, mathutils.Vector(up_vector)) for obj in mesh_objects]

            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].shading.type = 'MATERIAL'
                    area.spaces[0].region_3d.view_perspective = 'CAMERA'
                    break

            # 再次取消所有对象的选择，确保没有对象被选中
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = None

            screenshot_path = os.path.join(output_path, f"{view_name}.png")
            scene.render.filepath = screenshot_path
            scene.render.image_settings.file_format = 'PNG'

            bpy.ops.render.opengl(write_still=True)
            screenshot_paths.append(screenshot_path)

            # 移除标签
            remove_labels()

    finally:
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
                            space.shading.type = settings['shading_type']
                        break

    return screenshot_paths

def save_screenshots():
    output_path = r"D:\GPT_driven_modeling\resources\screenshots"
    return _save_screenshots_common(output_path)

def save_screenshots_to_path(output_path):
    return _save_screenshots_common(output_path)

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
        save_screenshots()
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