import bpy
from bpy.types import Operator, Panel
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty

class BevelEdgesOperator(Operator):
    bl_idname = "object.bevel_edges"
    bl_label = "Bevel Edges"
    bl_options = {'REGISTER', 'UNDO'}

    width: FloatProperty(
        name="Width",
        description="Bevel width",
        default=0.1,
        min=0.0,
        max=1.0
    )

    segments: IntProperty(
        name="Segments",
        description="Number of segments for bevel",
        default=4,
        min=1,
        max=100
    )

    angle_limit: FloatProperty(
        name="Angle Limit",
        description="Angle above which to bevel edges",
        default=30.0,
        min=0.0,
        max=180.0,
        subtype='ANGLE'
    )

    offset_type: EnumProperty(
        name="Offset Type",
        description="How to measure the width of the bevel",
        items=[
            ('OFFSET', "Offset", "Amount is offset of new edges from original"),
            ('WIDTH', "Width", "Amount is width of new face"),
            ('DEPTH', "Depth", "Amount is perpendicular distance from original edge to bevel face"),
            ('PERCENT', "Percent", "Amount is percent of adjacent edge length"),
        ],
        default='OFFSET'
    )

    profile: FloatProperty(
        name="Profile",
        description="The profile shape (0.5 = round)",
        default=0.5,
        min=0.0,
        max=1.0
    )

    miter_outer: EnumProperty(
        name="Outer Miter",
        description="Pattern to use for outside of miters",
        items=[
            ('SHARP', "Sharp", "Sharp corners"),
            ('PATCH', "Patch", "Create a patch to smooth corners"),
            ('ARC', "Arc", "Create an arc to smooth corners"),
        ],
        default='SHARP'
    )

    miter_inner: EnumProperty(
        name="Inner Miter",
        description="Pattern to use for inside of miters",
        items=[
            ('SHARP', "Sharp", "Sharp corners"),
            ('ARC', "Arc", "Create an arc to smooth corners"),
        ],
        default='SHARP'
    )

    spread: FloatProperty(
        name="Spread",
        description="Amount to spread beveled vertices",
        default=0.0,
        min=0.0,
        max=1.0
    )

    harden_normals: BoolProperty(
        name="Harden Normals",
        description="Match normals of new faces to adjacent faces",
        default=False
    )

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bevel_modifier = obj.modifiers.new(name="Bevel", type='BEVEL')
                bevel_modifier.width = self.width
                bevel_modifier.segments = self.segments
                bevel_modifier.limit_method = 'ANGLE'
                bevel_modifier.angle_limit = self.angle_limit
                bevel_modifier.offset_type = self.offset_type
                bevel_modifier.profile = self.profile
                bevel_modifier.miter_outer = self.miter_outer
                bevel_modifier.miter_inner = self.miter_inner
                bevel_modifier.spread = self.spread
                bevel_modifier.harden_normals = self.harden_normals
                
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier="Bevel")
        return {'FINISHED'}

class OBJECT_PT_bevel_panel(Panel):
    bl_label = "Advanced Bevel Edges"
    bl_idname = "OBJECT_PT_bevel_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        
        op = layout.operator("object.bevel_edges")
        
        layout.prop(op, "width")
        layout.prop(op, "segments")
        layout.prop(op, "angle_limit")
        layout.prop(op, "offset_type")
        layout.prop(op, "profile")
        layout.prop(op, "miter_outer")
        layout.prop(op, "miter_inner")
        layout.prop(op, "spread")
        layout.prop(op, "harden_normals")
