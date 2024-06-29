import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import FloatVectorProperty, EnumProperty

class AlignProperties(PropertyGroup):
    align_point_obj1: FloatVectorProperty(name="Align Point Obj1", subtype='XYZ', default=(0.0, 0.0, 0.0))
    align_point_obj2: FloatVectorProperty(name="Align Point Obj2", subtype='XYZ', default=(0.0, 0.0, 0.0))
    align_direction: EnumProperty(
        name="Align Direction",
        items=[
            ('OBJ1_TO_OBJ2', "Object 1 to Object 2", ""),
            ('OBJ2_TO_OBJ1', "Object 2 to Object 1", "")
        ],
        default='OBJ2_TO_OBJ1'
    )

class SetAlignPointOperator(Operator):
    bl_idname = "object.set_align_point"
    bl_label = "Set Align Point"

    def execute(self, context):
        obj = context.active_object
        scene = context.scene
        align_props = scene.align_props

        # Get the center location of selected vertex, edge, or face
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_verts = [v for v in obj.data.vertices if v.select]
        selected_edges = [e for e in obj.data.edges if e.select]
        selected_faces = [f for f in obj.data.polygons if f.select]

        if len(selected_verts) == 1:
            vert = selected_verts[0]
            world_coord = obj.matrix_world @ vert.co
        elif len(selected_edges) == 1:
            edge = selected_edges[0]
            edge_center = (obj.data.vertices[edge.vertices[0]].co + obj.data.vertices[edge.vertices[1]].co) / 2
            world_coord = obj.matrix_world @ edge_center
        elif len(selected_faces) == 1:
            face = selected_faces[0]
            world_coord = obj.matrix_world @ face.center
        else:
            self.report({'WARNING'}, "Please select one vertex, one edge, or one face")
            return {'CANCELLED'}

        if scene.align_point_set == 1:
            align_props.align_point_obj1 = world_coord
            scene.align_point_set = 2
            self.report({'INFO'}, "Align point for Object 1 set successfully")
        else:
            align_props.align_point_obj2 = world_coord
            scene.align_point_set = 1
            self.report({'INFO'}, "Align point for Object 2 set successfully")

        return {'FINISHED'}

class AlignObjectsOperator(Operator):
    bl_idname = "object.align_objects"
    bl_label = "Align Objects"

    def execute(self, context):
        scene = context.scene
        align_props = scene.align_props

        if scene.align_point_set != 1:
            self.report({'WARNING'}, "Please set two align points")
            return {'CANCELLED'}

        selected_objects = context.selected_objects
        if len(selected_objects) != 2:
            self.report({'WARNING'}, "Please select two objects")
            return {'CANCELLED'}

        obj1, obj2 = selected_objects
        point1 = align_props.align_point_obj1
        point2 = align_props.align_point_obj2

        # Calculate offset
        if align_props.align_direction == 'OBJ2_TO_OBJ1':
            offset = point1 - point2
            obj_to_move = obj2
        else:
            offset = point2 - point1
            obj_to_move = obj1

        # Apply offset
        obj_to_move.location -= offset

        # Output new location
        self.report({'INFO'}, f"New location of {obj_to_move.name}: {obj_to_move.location}")

        return {'FINISHED'}

class AlignPanel(Panel):
    bl_label = "Align Objects"
    bl_idname = "OBJECT_PT_align_objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene.align_props

        layout.operator("object.set_align_point", text="Set Align Point")
        layout.operator("object.align_objects", text="Align Objects")
        layout.prop(scene, "align_direction", text="Align Direction")
