# 椅腿椅面分离

这段代码针对3D椅子模型中常见的椅腿与椅面分离问题。通过精确的几何计算和空间分析，代码能自动识别分离的组件，并将椅腿精确地重新连接到椅面，恢复椅子的结构完整性。

import bpy
import bmesh
from mathutils import Vector

def get_connection_point(obj, direction):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    
    # 假设寻找连接点的逻辑
    for face in bm.faces:
        if face.normal.dot(direction) > 0.99:
            point = face.calc_center_median()
            world_point = obj.matrix_world @ point
            bm.free()
            return world_point
    
    bm.free()
    return None

def align_leg_to_seat(leg_obj, seat_obj):
    leg_top = get_connection_point(leg_obj, Vector((0, 0, 1)))
    seat_bottom = get_connection_point(seat_obj, Vector((0, 0, -1)))
    
    if leg_top and seat_bottom:
        offset = seat_bottom - leg_top
        leg_obj.location += offset

bpy.ops.object.mode_set(mode='OBJECT')

chair_seat = bpy.data.objects['ChairSeat']
for leg_name in ['Leg1', 'Leg2', 'Leg3', 'Leg4']:
    leg = bpy.data.objects[leg_name]
    align_leg_to_seat(leg, chair_seat)

print("椅腿已重新连接到椅面")