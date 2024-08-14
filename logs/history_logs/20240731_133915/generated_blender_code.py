```python
import bpy
import math
import random

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建主集合
main_collection = bpy.data.collections.new("ChristmasTree")
bpy.context.scene.collection.children.link(main_collection)

# 创建树干
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(0, 0, 1))
trunk = bpy.context.active_object
trunk.name = "Trunk"
main_collection.objects.link(trunk)

# 创建树冠
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=1.8, location=(0, 0, 2.9))
crown = bpy.context.active_object
crown.name = "Crown"
main_collection.objects.link(crown)

# 创建树枝
for i in range(50):
    angle = random.uniform(0, 2 * math.pi)
    height = random.uniform(0.5, 2.5)
    length = (2.5 - height) / 2 + 0.5
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=length, depth=0.05, location=(length/2 * math.cos(angle), length/2 * math.sin(angle), height))
    branch = bpy.context.active_object
    branch.name = f"Branch_{i + 1}"
    branch.rotation_euler = (0, math.radians(90), angle)
    main_collection.objects.link(branch)

# 创建树顶装饰
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 3.7))
top_decor = bpy.context.active_object
top_decor.name = "Top_Decoration"
main_collection.objects.link(top_decor)

# 创建树底座
bpy.ops.mesh.primitive_cube_add(size=0.8, location=(0, 0, 0.05))
base = bpy.context.active_object
base.name = "Base"
main_collection.objects.link(base)

# 随机创建一些装饰品
for i in range(20):
    angle = random.uniform(0, 2 * math.pi)
    height = random.uniform(0.5, 3.5)
    dist = random.uniform(0.2, 1)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(dist * math.cos(angle), dist * math.sin(angle), height))
    decor = bpy.context.active_object
    decor.name = f"Decoration_{i + 1}"
    main_collection.objects.link(decor)

bpy.context.view_layer.update()
```