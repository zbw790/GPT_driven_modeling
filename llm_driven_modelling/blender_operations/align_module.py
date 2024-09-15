import bpy
import bmesh
from mathutils import *
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import FloatVectorProperty, EnumProperty


class AlignProperties(PropertyGroup):
    align_point_obj1: FloatVectorProperty(
        name="Align Point Obj1", subtype="XYZ", default=(0.0, 0.0, 0.0), precision=4
    )
    align_point_obj2: FloatVectorProperty(
        name="Align Point Obj2", subtype="XYZ", default=(0.0, 0.0, 0.0), precision=4
    )
    align_direction: EnumProperty(
        name="Align Direction",
        items=[
            (
                "OBJ2_TO_OBJ1",
                "Object 2 to Object 1",
                "Move Object 2 to align with Object 1",
            ),
            (
                "OBJ1_TO_OBJ2",
                "Object 1 to Object 2",
                "Move Object 1 to align with Object 2",
            ),
        ],
        default="OBJ2_TO_OBJ1",
    )


class SetAlignPointOperator(Operator):
    bl_idname = "object.set_align_point"
    bl_label = "Set Align Point"

    def execute(self, context):
        obj = context.active_object
        scene = context.scene
        align_props = scene.align_props

        # 确保我们在正确的模式下
        if obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")

        # 获取选中的顶点、边或面的中心位置
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        selected_verts = [v for v in bm.verts if v.select]
        selected_edges = [e for e in bm.edges if e.select]
        selected_faces = [f for f in bm.faces if f.select]

        if len(selected_verts) == 1:
            local_coord = selected_verts[0].co
        elif len(selected_edges) == 1:
            local_coord = (
                selected_edges[0].verts[0].co + selected_edges[0].verts[1].co
            ) / 2
        elif len(selected_faces) == 1:
            local_coord = selected_faces[0].calc_center_median()
        else:
            self.report({"WARNING"}, "Please select one vertex, one edge, or one face")
            return {"CANCELLED"}

        # 转换为全局坐标
        world_coord = obj.matrix_world @ local_coord

        if scene.align_point_set == 1:
            align_props.align_point_obj1 = world_coord
            scene.align_point_set = 2
            self.report({"INFO"}, f"Align point for Object 1 set to {world_coord}")
        else:
            align_props.align_point_obj2 = world_coord
            scene.align_point_set = 1
            self.report({"INFO"}, f"Align point for Object 2 set to {world_coord}")

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode="OBJECT")
        return {"FINISHED"}


class AlignObjectsOperator(bpy.types.Operator):
    bl_idname = "object.align_objects"
    bl_label = "Align Objects"

    def execute(self, context):
        scene = context.scene
        align_props = scene.align_props

        if scene.align_point_set != 1:
            self.report({"WARNING"}, "Please set two align points")
            return {"CANCELLED"}

        selected_objects = context.selected_objects
        if len(selected_objects) != 2:
            self.report({"WARNING"}, "Please select two objects")
            return {"CANCELLED"}

        obj1, obj2 = selected_objects
        point1 = Vector(align_props.align_point_obj1)
        point2 = Vector(align_props.align_point_obj2)

        if align_props.align_direction == "OBJ2_TO_OBJ1":
            obj_to_move = obj2
            obj_target = obj1
            point_target = point1
            point_to_move = point2
        else:
            obj_to_move = obj1
            obj_target = obj2
            point_target = point2
            point_to_move = point1

        # 计算移动向量
        translation_vector = point_target - point_to_move

        # 应用移动
        if point1 > point2:
            obj_to_move.matrix_world.translation -= translation_vector
        else:
            obj_to_move.matrix_world.translation += translation_vector

        # 更新场景
        context.view_layer.update()

        self.report(
            {"INFO"},
            f"New location of {obj_to_move.name}: {obj_to_move.matrix_world.translation}",
        )

        return {"FINISHED"}


class AlignPanel(Panel):
    bl_label = "Align Objects"
    bl_idname = "OBJECT_PT_align_objects"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        scene = context.scene.align_props

        layout.operator("object.set_align_point", text="Set Align Point")
        layout.operator("object.align_objects", text="Align Objects")
        layout.prop(scene, "align_direction", text="Align Direction")
