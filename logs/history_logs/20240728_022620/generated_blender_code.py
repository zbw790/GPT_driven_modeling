```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建桌面
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.765))
tabletop = bpy.context.active_object
tabletop.name = "table_top"
bpy.ops.transform.resize(value=(1.5, 0.9, 0.03))

# 创建桌腿位置列表
leg_positions = [
    (1.45, 0.85, 0.375),
    (-1.45, 0.85, 0.375),
    (1.45, -0.85, 0.375),
    (-1.45, -0.85, 0.375)
]

# 创建桌腿
for i, pos in enumerate(leg_positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.75, location=pos)
    leg = bpy.context.active_object
    leg.name = f"leg_{i+1}"

# 更新场景
bpy.context.view_layer.update()
```