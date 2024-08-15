```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 创建桌面
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.dimensions = (1.5, 0.8, 0.03)
tabletop.name = "table_top"

# 创建桌腿函数
def create_leg(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.72, location=location)
    leg = bpy.context.active_object
    leg.name = name
    return leg

# 创建四条桌腿
leg1 = create_leg("leg1", (0.735, 0.385, 0.375))
leg2 = create_leg("leg2", (-0.735, 0.385, 0.375))
leg3 = create_leg("leg3", (0.735, -0.385, 0.375))
leg4 = create_leg("leg4", (-0.735, -0.385, 0.375))

# 更新场景
bpy.context.view_layer.update()
```