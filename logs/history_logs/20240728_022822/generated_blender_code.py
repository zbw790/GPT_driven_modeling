```python
import bpy
import random

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建集合
main_collection = bpy.data.collections.new("ChristmasTree")
bpy.context.scene.collection.children.link(main_collection)

# 创建树干
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.5, depth=2, location=(0, 0, 1))
trunk = bpy.context.active_object
trunk.name = "Trunk"
main_collection.objects.link(trunk)

# 创建树枝和树叶
bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=2, depth=4, location=(0, 0, 3))
branches = bpy.context.active_object
branches.name = "Branches"
main_collection.objects.link(branches)

# 创建树顶装饰
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 5))
top_decor = bpy.context.active_object
top_decor.name = "TopStar"
main_collection.objects.link(top_decor)

# 创建装饰球
for i in range(20):
    x = random.uniform(-1.8, 1.8)
    y = random.uniform(-1.8, 1.8)
    z = random.uniform(1, 4.5)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x, y, z))
    ball = bpy.context.active_object
    ball.name = f"Ball_{i+1}"
    main_collection.objects.link(ball)

# 创建礼物盒
for i in range(5):
    x = random.uniform(-1.5, 1.5)
    y = random.uniform(-1.5, 1.5)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.25))
    gift = bpy.context.active_object
    gift.name = f"Gift_{i+1}"
    gift.scale = (0.3, 0.2, 0.15)
    main_collection.objects.link(gift)

# 移除默认集合中的对象
for obj in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.unlink(obj)

# 更新场景
bpy.context.view_layer.update()
```