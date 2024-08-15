```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建树干
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.5, depth=2, location=(0, 0, 1))
tree_trunk = bpy.context.active_object
tree_trunk.name = "树干"

# 创建树枝和树叶
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.5, radius2=0, depth=4, location=(0, 0, 3))
tree_leaves = bpy.context.active_object
tree_leaves.name = "树枝和树叶"

# 创建树顶装饰物
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 5))
tree_top_decoration = bpy.context.active_object
tree_top_decoration.name = "树顶装饰"

# 创建装饰球
for i in range(20):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(i * 0.1 - 1, i * 0.1 - 1, 2 + i * 0.1))
    decoration_ball = bpy.context.active_object
    decoration_ball.name = f"装饰球_{i+1}"

# 创建彩灯串（简单模拟）
for i in range(50):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=(i * 0.05 - 1.25, i * 0.05 - 1.25, 1 + i * 0.05))
    light_bulb = bpy.context.active_object
    light_bulb.name = f"彩灯_{i+1}"

# 创建礼物盒
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 0.5 - 1, -1.5, 0.5))
    gift_box = bpy.context.active_object
    gift_box.scale = (0.3, 0.2, 0.15)
    gift_box.name = f"礼物盒_{i+1}"
```