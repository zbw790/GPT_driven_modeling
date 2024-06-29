import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import IntProperty, FloatProperty

class SubdivisionDecimateProperties(PropertyGroup):
    subdivision_levels: IntProperty(name="Subdivision Levels", default=1, min=1, max=6)
    decimate_ratio: FloatProperty(name="Decimate Ratio", default=0.5, min=0.0, max=1.0)

class ApplySubdivisionSurface(Operator):
    bl_idname = "object.apply_subdivision_surface"
    bl_label = "Apply Subdivision Surface"

    def execute(self, context):
        levels = context.scene.subdivision_decimate_props.subdivision_levels
        for obj in context.selected_objects:
            mod = obj.modifiers.new(name="Subdivision Surface", type='SUBSURF')
            mod.levels = levels
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}

class ApplyDecimate(Operator):
    bl_idname = "object.apply_decimate"
    bl_label = "Apply Decimate"

    def execute(self, context):
        ratio = context.scene.subdivision_decimate_props.decimate_ratio
        for obj in context.selected_objects:
            mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
            mod.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}

class SubdivisionDecimatePanel(Panel):
    bl_label = "Subdivision and Decimate"
    bl_idname = "OBJECT_PT_subdivision_decimate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene.subdivision_decimate_props

        # 细分表面
        layout.label(text="细分表面")
        layout.prop(scene, "subdivision_levels", text="Levels")
        layout.operator("object.apply_subdivision_surface", text="Apply Subdivision Surface")

        # 分割线
        layout.separator()

        # 简化
        layout.label(text="简化表面")
        layout.prop(scene, "decimate_ratio", text="Ratio")
        layout.operator("object.apply_decimate", text="Apply Decimate")