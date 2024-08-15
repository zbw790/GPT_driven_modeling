import bpy
import mathutils
from bpy.types import Operator, Panel

class ResetObjectLocation(Operator):
    bl_idname = "model_viewer.reset_object_location"
    bl_label = "Reset Object Location"

    def execute(self, context):
        # 调用函数
        reset_mesh_origin_to_bbx_center()
        return {'FINISHED'}

def reset_mesh_origin_to_bbx_center():
    # 获取所有选中的物体
    selected_objects = bpy.context.selected_objects

    for obj in selected_objects:
        # 设定当前物体为活动物体
        bpy.context.view_layer.objects.active = obj

        # 清空物体的位置
        bpy.ops.object.location_clear()

        # 计算物体的包围盒中心点
        bbx_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        bbx_center = sum(bbx_corners, mathutils.Vector()) / 8

        # 设置CURSOR到包围盒中心点
        bpy.context.scene.cursor.location = bbx_center

        # 设置物体原点到CURSOR
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')

        # 把网格的中心点移动到原点，但不移动网格
        obj.location = (0, 0, 0)

    # 重置CURSOR
    bpy.context.scene.cursor.location = (0, 0, 0)

class LocationPanel(Panel):
    bl_label = "Location Operations"
    bl_idname = "OBJECT_PT_location_operations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("model_viewer.reset_object_location", text="Reset Object Location")
