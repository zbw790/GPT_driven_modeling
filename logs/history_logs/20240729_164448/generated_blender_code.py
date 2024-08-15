```python
import bpy
import random

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建主集合
main_collection = bpy.data.collections.new("ChristmasTree")
bpy.context.scene.collection.children.link(main_collection)

# 创建树干
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.5, depth=2, location=(0, 0, 1))
trunk = bpy.context.active_object
trunk.name = "TreeTrunk"
bpy.ops.transform.resize(value=(1, 1, 5))

# 创建树枝
bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=5, radius2=0, depth=10, location=(0, 0, 6))
branches = bpy.context.active_object
branches.name = "TreeBranches"

# 创建树顶装饰
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 12))
top_decor = bpy.context.active_object
top_decor.name = "TopDecoration"
bpy.ops.transform.resize(value=(0.5, 0.5, 0.5))
bpy.ops.object.shade_smooth()

# 创建装饰球
for i in range(20):
    x = random.uniform(-3, 3)
    y = random.uniform(-3, 3)
    z = random.uniform(1, 10)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(x, y, z))
    ball = bpy.context.active_object
    ball.name = f"DecorationBall{i + 1}"
    bpy.ops.object.shade_smooth()

# 创建礼物盒
for i in range(5):
    x = random.uniform(-5, 5)
    y = random.uniform(-5, 5)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.5))
    present = bpy.context.active_object
    present.name = f"PresentBox{i + 1}"
    bpy.ops.transform.resize(value=(0.3, 0.2, 0.15))

# 更新场景
bpy.context.view_layer.update()
```