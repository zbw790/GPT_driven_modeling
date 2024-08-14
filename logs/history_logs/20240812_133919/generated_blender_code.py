```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建桌面
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.scale = (1.5, 0.9, 0.03)
tabletop.name = "桌面"

# 桌腿位置和尺寸
leg_positions = [
    (1.45, 0.85, 0.36),
    (-1.45, 0.85, 0.36),
    (1.45, -0.85, 0.36),
    (-1.45, -0.85, 0.36)
]
leg_radius = 0.04
leg_height = 0.72

# 创建桌腿
for i, pos in enumerate(leg_positions, start=1):
    bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=pos)
    leg = bpy.context.active_object
    leg.name = f"桌腿{i}"
```