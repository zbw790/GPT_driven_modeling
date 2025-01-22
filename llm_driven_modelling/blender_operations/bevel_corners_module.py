import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import FloatProperty, IntProperty, PointerProperty


class BevelProperties(PropertyGroup):
    width: FloatProperty(
        name="Width", description="Bevel width", default=0.1, min=0.0, max=1.0
    )

    segments: IntProperty(
        name="Segments",
        description="Number of segments for bevel",
        default=4,
        min=1,
        max=20,
    )

    profile: FloatProperty(
        name="Profile",
        description="The profile shape (0.5 for round)",
        default=0.5,
        min=0.0,
        max=1.0,
    )


class BevelEdgesOperator(Operator):
    bl_idname = "object.bevel_edges"
    bl_label = "Bevel Edges"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.bevel_properties
        original_mode = context.object.mode

        for obj in context.selected_objects:
            if obj.type == "MESH":
                bpy.context.view_layer.objects.active = obj

                if original_mode == "EDIT":
                    bpy.ops.mesh.bevel(
                        offset=props.width,
                        offset_type="WIDTH",
                        segments=props.segments,
                        profile=props.profile,
                        affect="EDGES",
                    )
                else:
                    bevel_modifier = obj.modifiers.new(name="Bevel", type="BEVEL")
                    bevel_modifier.width = props.width
                    bevel_modifier.segments = props.segments
                    bevel_modifier.profile = props.profile
                    bpy.ops.object.modifier_apply(modifier="Bevel")

        return {"FINISHED"}


class OBJECT_PT_bevel_panel(Panel):
    bl_label = "Bevel Edges"
    bl_idname = "OBJECT_PT_bevel_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        props = context.scene.bevel_properties

        layout.prop(props, "width")
        layout.prop(props, "segments")
        layout.prop(props, "profile")
        layout.operator("object.bevel_edges")
