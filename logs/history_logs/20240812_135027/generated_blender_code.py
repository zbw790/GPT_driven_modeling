```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建桌面
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.name = "table_top"
tabletop.scale[0] = 1.5  # 长度：150 cm
tabletop.scale[1] = 0.9  # 宽度：90 cm
tabletop.scale[2] = 0.03  # 高度：3 cm

# 创建桌腿
def create_leg(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.72, location=location)
    leg = bpy.context.active_object
    leg.name = name
    return leg

# 创建四条桌腿
leg1 = create_leg("leg1", (0.7, 0.4, 0.36))
leg2 = create_leg("leg2", (-0.7, 0.4, 0.36))
leg3 = create_leg("leg3", (0.7, -0.4, 0.36))
leg4 = create_leg("leg4", (-0.7, -0.4, 0.36))
```