import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import FloatProperty

class GeometryProperties(PropertyGroup):
    move_geometry_x: FloatProperty(name="Move X", default=0.0)
    move_geometry_y: FloatProperty(name="Move Y", default=0.0)
    move_geometry_z: FloatProperty(name="Move Z", default=0.0)

class MoveGeometryWithoutAffectingOrigin(Operator):
    bl_idname = "object.move_geometry_without_affecting_origin"
    bl_label = "Translate Geometry"

    move_x: FloatProperty(name="Move X", default=0.0)
    move_y: FloatProperty(name="Move Y", default=0.0)
    move_z: FloatProperty(name="Move Z", default=0.0)

    def execute(self, context):
        for obj in context.selected_objects:
            bpy.context.view_layer.objects.active = obj

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.translate(value=(self.move_x, self.move_y, self.move_z))
            bpy.ops.object.mode_set(mode='OBJECT')
            
        return {'FINISHED'}

class ResetGeometryToOrigin(Operator):
    bl_idname = "object.reset_geometry_to_origin"
    bl_label = "Reset Geometry to Origin"

    def execute(self, context):
        for obj in context.selected_objects:
            bpy.context.view_layer.objects.active = obj

            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            bpy.ops.object.location_clear()
            
        return {'FINISHED'}

class GeometryPanel(Panel):
    bl_label = "Geometry Operations"
    bl_idname = "OBJECT_PT_geometry_operations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene.geometry_props

        layout.label(text="Translate Geometry")
        layout.prop(scene, "move_geometry_x", text="X Axis Translation")
        layout.prop(scene, "move_geometry_y", text="Y Axis Translation")
        layout.prop(scene, "move_geometry_z", text="Z Axis Translation")
        translate_op = layout.operator("object.move_geometry_without_affecting_origin", text="Translate Geometry")
        translate_op.move_x = scene.move_geometry_x
        translate_op.move_y = scene.move_geometry_y
        translate_op.move_z = scene.move_geometry_z

        layout.separator()

        layout.label(text="Reset Geometry")
        layout.operator("object.reset_geometry_to_origin", text="Reset Geometry to Origin")
