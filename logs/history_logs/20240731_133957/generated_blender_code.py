```python
import bpy
import random
import math

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建主集合
main_collection = bpy.data.collections.new("ChristmasTree")
bpy.context.scene.collection.children.link(main_collection)

# 创建树干
bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=2, location=(0, 0, 1))
trunk = bpy.context.object
trunk.name = "Trunk"
main_collection.objects.link(trunk)
bpy.context.scene.collection.objects.unlink(trunk)

# 创建树枝（使用随机生成）
for i in range(100):
    angle = random.uniform(0, 2 * math.pi)
    height = random.uniform(0.2, 2)
    length = (2.5 - height) / 4 + 0.3
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=length, depth=0.05, location=(length * math.cos(angle), length * math.sin(angle), height + 1))
    branch = bpy.context.object
    branch.name = f"Branch_{i + 1}"
    branch.rotation_euler = (0, math.radians(90), angle)
    main_collection.objects.link(branch)
    bpy.context.scene.collection.objects.unlink(branch)

# 创建树顶装饰（星形）
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 3.2))
top_decor = bpy.context.object
top_decor.name = "Top_Decoration"
main_collection.objects.link(top_decor)
bpy.context.scene.collection.objects.unlink(top_decor)

# 创建底座
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.1, location=(0, 0, 0.05))
base = bpy.context.object
base.name = "Base"
main_collection.objects.link(base)
bpy.context.scene.collection.objects.unlink(base)

# 添加一些装饰品（球形）
for i in range(30):
    angle = random.uniform(0, 2 * math.pi)
    height = random.uniform(0.2, 3)
    dist = random.uniform(0.2, 1)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(dist * math.cos(angle), dist * math.sin(angle), height + 1))
    decor = bpy.context.object
    decor.name = f"Decoration_{i + 1}"
    main_collection.objects.link(decor)
    bpy.context.scene.collection.objects.unlink(decor)

bpy.context.view_layer.update()
```