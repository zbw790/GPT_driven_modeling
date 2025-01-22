# model_viewer_module.py

"""
This module provides functionality for viewing and manipulating 3D models in Blender.
It includes features for camera positioning, object labeling, screenshot capture, and model scaling.
"""

import bpy
import os
import math
import mathutils
from bpy.types import Panel, Operator
from bpy.props import FloatProperty, StringProperty
from bpy_extras.object_utils import world_to_camera_view
import bmesh


def ensure_camera():
    """
    Ensure that a camera exists in the scene and return it.

    Returns:
        bpy.types.Object: The camera object.
    """
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
    """
    Calculate the center and size of the scene based on the given objects.

    Args:
        objects (list): List of Blender objects.

    Returns:
        tuple: A tuple containing the scene center (Vector) and size (float).
    """
    if not objects:
        return mathutils.Vector((0, 0, 0)), 0

    min_corner, max_corner = calculate_combined_bounding_box(objects)
    center = mathutils.Vector([(min_corner[i] + max_corner[i]) / 2 for i in range(3)])
    size = max((max_corner[i] - min_corner[i]) for i in range(3))
    return center, size


def calculate_combined_bounding_box(objects):
    """
    Calculate the combined bounding box of multiple objects.

    Args:
        objects (list): List of Blender objects.

    Returns:
        tuple: A tuple containing the minimum and maximum corners of the bounding box.
    """
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")

    for obj in objects:
        bbox_corners = [
            obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box
        ]
        for corner in bbox_corners:
            min_x = min(min_x, corner.x)
            max_x = max(max_x, corner.x)
            min_y = min(min_y, corner.y)
            max_y = max(max_y, corner.y)
            min_z = min(min_z, corner.z)
            max_z = max(max_z, corner.z)

    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def set_camera_position_and_rotation(camera, look_from, look_at):
    """
    Set the camera's position and rotation to look at a specific point.

    Args:
        camera (bpy.types.Object): The camera object.
        look_from (mathutils.Vector): The position to place the camera.
        look_at (mathutils.Vector): The point for the camera to look at.
    """
    direction = look_at - look_from
    rot_quat = direction.to_track_quat("-Z", "Y")
    camera.rotation_euler = rot_quat.to_euler()
    camera.location = look_from


def add_label_to_object(obj, camera, scene_size, up_vector):
    """
    Add a label to an object in the scene.

    Args:
        obj (bpy.types.Object): The object to label.
        camera (bpy.types.Object): The camera object.
        scene_size (float): The size of the scene.
        up_vector (mathutils.Vector): The up vector for orienting the label.

    Returns:
        bpy.types.Object: The created text object, or None if the object is not visible.
    """
    is_visible, visible_point = is_object_visible(obj, camera)
    if not is_visible:
        return None

    center = visible_point

    bpy.ops.object.text_add(enter_editmode=False, location=(0, 0, 0))
    text_obj = bpy.context.active_object

    text_obj.data.body = obj.name
    text_obj.data.align_x = "CENTER"
    text_obj.data.align_y = "CENTER"

    direction = center - camera.location
    direction_length = direction.length
    direction.normalize()

    text_position = camera.location + direction * (direction_length * 0.7)

    text_obj.location = text_position

    distance_to_camera = (text_position - camera.location).length
    text_obj.data.size = scene_size * 0.02 * (distance_to_camera / scene_size)

    material = bpy.data.materials.new(name="Text_Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    node_emission = nodes.new(type="ShaderNodeEmission")
    node_emission.inputs[0].default_value = (1, 0, 0, 1)  # Red color
    node_emission.inputs[1].default_value = 2  # Emission strength
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    material.node_tree.links.new(node_emission.outputs[0], node_output.inputs[0])

    if text_obj.data.materials:
        text_obj.data.materials[0] = material
    else:
        text_obj.data.materials.append(material)

    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

    forward = camera.location - text_position
    forward.normalize()
    right = forward.cross(up_vector)
    right.normalize()
    up = right.cross(forward)

    rot_matrix = mathutils.Matrix((-right, up, forward)).to_3x3()
    quat = rot_matrix.to_quaternion()
    quat.invert()

    text_obj.rotation_mode = "QUATERNION"
    text_obj.rotation_quaternion = quat
    text_obj.location = text_position

    text_obj.show_in_front = True

    return text_obj


def is_object_visible(obj, camera):
    """
    Check if an object is visible from the camera's perspective.

    Args:
        obj (bpy.types.Object): The object to check.
        camera (bpy.types.Object): The camera object.

    Returns:
        tuple: A tuple containing a boolean (True if visible) and the visible point (or None).
    """

    def check_point(point):
        co_ndc = world_to_camera_view(bpy.context.scene, camera, point)
        if 0 <= co_ndc.x <= 1 and 0 <= co_ndc.y <= 1 and 0 < co_ndc.z:
            direction = point - camera.location
            depsgraph = bpy.context.evaluated_depsgraph_get()

            offsets = [
                mathutils.Vector((0, 0, 0)),
                mathutils.Vector((0.001, 0.001, 0.001)),
                mathutils.Vector((-0.001, -0.001, -0.001)),
            ]

            for offset in offsets:
                ray_origin = camera.location + offset
                ray_cast_result = bpy.context.scene.ray_cast(
                    depsgraph, ray_origin, direction.normalized()
                )
                if ray_cast_result[0] and ray_cast_result[4] == obj:
                    return True
        return False

    center = obj.location
    if check_point(center):
        return True, center.copy()

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)

    result = False, None

    for v in bm.verts:
        if check_point(v.co):
            result = True, v.co.copy()
            break

    if not result[0]:
        for e in bm.edges:
            mid_point = (e.verts[0].co + e.verts[1].co) / 2
            if check_point(mid_point):
                result = True, mid_point.copy()
                break

    if not result[0]:
        for f in bm.faces:
            face_center = f.calc_center_median()
            if check_point(face_center):
                result = True, face_center.copy()
                break

    bm.free()
    return result


def remove_labels():
    """Remove all text objects (labels) from the scene."""
    for obj in bpy.data.objects:
        if obj.type == "FONT":
            bpy.data.objects.remove(obj, do_unlink=True)


def _save_screenshots_common(output_path, distance_factor=2.5):
    """
    Common function to save screenshots from multiple angles.

    Args:
        output_path (str): The directory to save the screenshots.
        distance_factor (float): Factor to determine camera distance from the scene center.

    Returns:
        list: A list of paths to the saved screenshots.
    """
    scene = bpy.context.scene

    original_resolution_x = scene.render.resolution_x
    original_resolution_y = scene.render.resolution_y
    original_resolution_percentage = scene.render.resolution_percentage
    original_camera = scene.camera

    original_view_settings = {}
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    original_view_settings[area] = {
                        "view_perspective": space.region_3d.view_perspective,
                        "view_matrix": space.region_3d.view_matrix.copy(),
                        "lock_camera": space.lock_camera,
                        "shading_type": space.shading.type,
                    }
                    break

    scene.render.resolution_x = 750
    scene.render.resolution_y = 750
    scene.render.resolution_percentage = 100

    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

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
        ((0, 0, 1), "Top View", (0, 1, 0)),
        ((0, 0, -1), "Bottom View", (0, 1, 0)),
        ((-1, 0, 0), "Left View", (0, 0, 1)),
        ((1, 0, 0), "Right View", (0, 0, 1)),
        ((0, 1, 0), "Back View", (0, 0, 1)),
        ((0, -1, 0), "Front View", (0, 0, 1)),
        ((1, -1, 1), "Top-Right-Front View", (0, 0, 1)),
        ((1, 1, -1), "Bottom-Right-Back View", (0, 0, 1)),
    ]

    screenshot_paths = []

    try:
        for direction, view_name, up_vector in angles:
            bpy.ops.object.select_all(action="DESELECT")
            bpy.context.view_layer.objects.active = None

            direction_vector = mathutils.Vector(direction).normalized()
            camera_position = center + direction_vector * camera_distance

            set_camera_position_and_rotation(camera, camera_position, center)

            bpy.context.view_layer.update()

            bpy.context.view_layer.objects.active = camera
            scene.camera = camera

            text_objects = [
                add_label_to_object(obj, camera, size, mathutils.Vector(up_vector))
                for obj in mesh_objects
            ]

            for area in bpy.context.screen.areas:
                if area.type == "VIEW_3D":
                    area.spaces[0].shading.type = "MATERIAL"
                    area.spaces[0].region_3d.view_perspective = "CAMERA"
                    break

            bpy.ops.object.select_all(action="DESELECT")
            bpy.context.view_layer.objects.active = None

            screenshot_path = os.path.join(output_path, f"{view_name}.png")
            scene.render.filepath = screenshot_path
            scene.render.image_settings.file_format = "PNG"

            bpy.ops.render.opengl(write_still=True)
            screenshot_paths.append(screenshot_path)

            remove_labels()

    finally:
        scene.render.resolution_x = original_resolution_x
        scene.render.resolution_y = original_resolution_y
        scene.render.resolution_percentage = original_resolution_percentage
        scene.camera = original_camera

        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        if area in original_view_settings:
                            settings = original_view_settings[area]
                            space.region_3d.view_perspective = settings[
                                "view_perspective"
                            ]
                            space.region_3d.view_matrix = settings["view_matrix"]
                            space.lock_camera = settings["lock_camera"]
                            space.shading.type = settings["shading_type"]
                        break

    return screenshot_paths


def save_screenshots():
    """
    Save screenshots to a predefined path.

    Returns:
        list: A list of paths to the saved screenshots.
    """
    output_path = r"D:\GPT_driven_modeling\resources\screenshots"
    return _save_screenshots_common(output_path)


def save_screenshots_to_path(output_path):
    """
    Save screenshots to a specified path.

    Args:
        output_path (str): The directory to save the screenshots.

    Returns:
        list: A list of paths to the saved screenshots.
    """
    return _save_screenshots_common(output_path)


class ApplyScale(Operator):
    """Operator to apply scale to selected objects."""

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
            context.scene.model_dimensions = (
                f"{dimensions.x:.2f} x {dimensions.y:.2f} x {dimensions.z:.2f}"
            )
        context.scene.model_scale_percentage = 100
        return {"FINISHED"}


def update_model_dimensions(self, context):
    """Update the displayed model dimensions based on the scale percentage."""
    scale_percentage = context.scene.model_scale_percentage
    scale_factor = scale_percentage / 100
    for obj in context.selected_objects:
        dimensions = obj.dimensions
        scaled_dimensions = dimensions * scale_factor
        context.scene.model_dimensions = f"{scaled_dimensions.x:.2f} x {scaled_dimensions.y:.2f} x {scaled_dimensions.z:.2f}"


class SaveScreenshotOperator(Operator):
    """Operator to save screenshots of the current scene."""

    bl_idname = "model_viewer.save_screenshot"
    bl_label = "Save Screenshot"

    def execute(self, context):
        save_screenshots()
        return {"FINISHED"}


class ModelViewerPanel(Panel):
    """Panel for model viewing and manipulation tools."""

    bl_label = "Model Viewer"
    bl_idname = "OBJECT_PT_model_viewer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

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
