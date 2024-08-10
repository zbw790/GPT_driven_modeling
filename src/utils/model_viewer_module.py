# model_viewer_modulke

import bpy
import os
import math
import mathutils
from bpy.types import Panel, Operator
from bpy.props import FloatProperty, StringProperty

# 设置截图保存路径
SCREENSHOTS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'screenshots')

def ensure_camera():
    camera = bpy.context.scene.camera
    if camera is None:
        bpy.ops.object.camera_add()
        camera = bpy.context.object
        bpy.context.scene.camera = camera
    return camera

def move_camera_to_position(camera, location, rotation):
    camera.location = location
    camera.rotation_euler = rotation
    bpy.context.view_layer.update()

def activate_camera(camera):
    bpy.context.view_layer.objects.active = camera
    bpy.context.scene.camera = camera
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            area.spaces[0].lock_camera = True
            break

def add_track_to_constraint(camera, target):
    constraint = camera.constraints.get('Track To')
    if constraint is None:
        constraint = camera.constraints.new(type='TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

def remove_track_to_constraint(camera):
    for constraint in camera.constraints:
        if constraint.type == 'TRACK_TO':
            camera.constraints.remove(constraint)

def calculate_combined_bounding_box(objects):
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    
    for obj in objects:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ mathutils.Vector(corner)
            min_x = min(min_x, world_corner.x)
            max_x = max(max_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            max_y = max(max_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            max_z = max(max_z, world_corner.z)
    
    return (min_x, min_y, min_z), (max_x, max_y, max_z)

def adjust_camera_distance(camera, objects, margin):
    min_corner, max_corner = calculate_combined_bounding_box(objects)
    bbx_center = mathutils.Vector([(min_corner[i] + max_corner[i]) / 2 for i in range(3)])
    
    max_distance_x = max_corner[0] - min_corner[0]
    max_distance_y = max_corner[1] - min_corner[1]
    max_distance_z = max_corner[2] - min_corner[2]
    
    fov = camera.data.angle

    adjusted_distance_x = (max_distance_x / 2) / math.tan(fov / 2) + margin
    adjusted_distance_y = (max_distance_y / 2) / math.tan(fov / 2) + margin
    adjusted_distance_z = (max_distance_z / 2) / math.tan(fov / 2) + margin
    adjusted_distance = max(adjusted_distance_x, adjusted_distance_y, adjusted_distance_z)

    direction_vector = (camera.location - bbx_center).normalized()
    
    camera.location = bbx_center + direction_vector * adjusted_distance

    camera.data.clip_start = adjusted_distance * 0.1
    camera.data.clip_end = adjusted_distance * 10
    camera.data.lens = 50

def save_screenshots():
    scene = bpy.context.scene

    # 保存原始渲染设置
    original_resolution_x = scene.render.resolution_x
    original_resolution_y = scene.render.resolution_y
    original_resolution_percentage = scene.render.resolution_percentage

    scene.render.resolution_x = 750
    scene.render.resolution_y = 750
    scene.render.resolution_percentage = 100

    # 自动选择所有模型
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)

    selected_objects = bpy.context.selected_objects

    if not selected_objects:
        print("No objects selected")
        return

    if not os.path.exists(SCREENSHOTS_PATH):
        os.makedirs(SCREENSHOTS_PATH)

    camera = ensure_camera()
    target = selected_objects[0]  # Assuming only one object is selected

    angles = [
        ((0, 0, 10), (0, math.radians(90), 0), "俯视图"),
        ((0, 0, -10), (0, math.radians(-90), 0), "底视图"),
        ((-10, 0, 0), (math.radians(90), 0, math.radians(90)), "左视图"),
        ((10, 0, 0), (math.radians(90), 0, math.radians(-90)), "右视图"),
        ((0, 10, 0), (math.radians(-90), 0, math.radians(180)), "后视图"),
        ((0, -10, 0), (math.radians(90), 0, 0), "前视图"),
        # ((-10, -10, 10), (math.radians(45), 0, math.radians(45)), "左前上视图"),
        ((10, -10, 10), (math.radians(45), 0, math.radians(-45)), "右前上视图"),
        # ((-10, 10, -10), (math.radians(-45), 0, math.radians(135)), "左后下视图"),
        ((10, 10, -10), (math.radians(-45), 0, math.radians(-135)), "右后下视图"),
    ]

    for location, rotation, view_name in angles:
        move_camera_to_position(camera, location, rotation)
        add_track_to_constraint(camera, target)
        activate_camera(camera)
        bpy.context.view_layer.update()

        adjust_camera_distance(camera, selected_objects, margin=4)

        screenshot_path = os.path.join(SCREENSHOTS_PATH, f"{view_name}.png")
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = screenshot_path

        bpy.ops.render.opengl(write_still=True)
    
    remove_track_to_constraint(camera)

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'PERSP'
            area.spaces[0].lock_camera = False
            break
    
    # 恢复原始渲染设置
    scene.render.resolution_x = original_resolution_x
    scene.render.resolution_y = original_resolution_y
    scene.render.resolution_percentage = original_resolution_percentage

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