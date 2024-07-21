import bpy
from bpy.types import Operator

class BevelEdgesOperator(Operator):
    bl_idname = "object.bevel_edges"
    bl_label = "Bevel Edges"
    bl_options = {'REGISTER', 'UNDO'}

    width: bpy.props.FloatProperty(
        name="Width",
        description="Bevel width",
        default=0.1,
        min=0.0,
        max=1.0
    )

    segments: bpy.props.IntProperty(
        name="Segments",
        description="Number of segments for bevel",
        default=4,
        min=1,
        max=20
    )

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bevel_modifier = obj.modifiers.new(name="Bevel", type='BEVEL')
                bevel_modifier.width = self.width
                bevel_modifier.segments = self.segments
                bevel_modifier.limit_method = 'ANGLE'
                bevel_modifier.angle_limit = 1.22173  # 约70度
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier="Bevel")
        return {'FINISHED'}

class OBJECT_PT_bevel_panel(bpy.types.Panel):
    bl_label = "Bevel Edges"
    bl_idname = "OBJECT_PT_bevel_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.bevel_edges")