import bpy
import math
from bpy.types import Panel, Operator, PropertyGroup

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
    
class RotatePanel(Panel):
    bl_label = "Rotate Objects"
    bl_idname = "OBJECT_PT_rotate_objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 按度数旋转
        layout.label(text="按度数旋转")
        layout.prop(scene, "rotation_degree", text="Rotation Degree")
        row = layout.row()
        row.operator("model_viewer.rotate_object_cw_x_degree", text="顺时针旋转 X by Degree")
        row.operator("model_viewer.rotate_object_cw_y_degree", text="顺时针旋转 Y by Degree")
        row.operator("model_viewer.rotate_object_cw_z_degree", text="顺时针旋转 Z by Degree")
        
        # 分割线
        layout.separator()
        
        # 一键旋转
        layout.label(text="一键旋转 90°")
        row = layout.row()
        row.operator("model_viewer.rotate_object_cw_x", text="顺时针90 (X)")
        row.operator("model_viewer.rotate_object_cw_y", text="顺时针90 (Y)")
        row.operator("model_viewer.rotate_object_cw_z", text="顺时针90 (Z)")
