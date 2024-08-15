```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建桌面
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.object
tabletop.scale[0] = 1.5  # 长度 1.5米
tabletop.scale[1] = 0.9  # 宽度 0.9米
tabletop.scale[2] = 0.03  # 厚度 3厘米
tabletop.name = "桌面"

# 创建桌腿
leg_locations = [(0.7, 0.4, 0.36), (-0.7, 0.4, 0.36), (0.7, -0.4, 0.36), (-0.7, -0.4, 0.36)]
for i, loc in enumerate(leg_locations):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.72, location=loc)
    leg = bpy.context.object
    leg.name = f"桌腿_{i+1}"
```