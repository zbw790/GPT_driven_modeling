```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 删除所有多余的集合
for collection in bpy.data.collections:
    bpy.data.collections.remove(collection)

# 创建主集合
main_collection = bpy.data.collections.new("ChristmasTree")
bpy.context.scene.collection.children.link(main_collection)

# 设置主集合为活动集合
layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

# 创建树干
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.5, depth=2, location=(0, 0, 1))
trunk = bpy.context.active_object
trunk.name = "TreeTrunk"

# 确保树干只在主集合中
for coll in trunk.users_collection:
    if coll != main_collection:
        coll.objects.unlink(trunk)

# 创建树枝（锥形状主体）
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1, radius2=0, depth=6, location=(0, 0, 4))
branches = bpy.context.active_object
branches.name = "TreeBranches"

# 确保树枝只在主集合中
for coll in branches.users_collection:
    if coll != main_collection:
        coll.objects.unlink(branches)

# 创建树顶装饰（星星）
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 7))
top_decor = bpy.context.active_object
top_decor.name = "TreeTopDecor"

# 确保树顶装饰只在主集合中
for coll in top_decor.users_collection:
    if coll != main_collection:
        coll.objects.unlink(top_decor)

# 创建装饰球
for i in range(20):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(1.5 * (i % 5 - 2), 1.5 * (i // 5 - 2), 2 + (i % 4)))
    decor_ball = bpy.context.active_object
    decor_ball.name = f"DecorBall{i+1}"
    for coll in decor_ball.users_collection:
        if coll != main_collection:
            coll.objects.unlink(decor_ball)

# 创建礼物盒
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(2 * (i - 2), -2.5, 0.5))
    gift_box = bpy.context.active_object
    gift_box.scale = (0.6, 0.4, 0.3)
    gift_box.name = f"GiftBox{i+1}"
    for coll in gift_box.users_collection:
        if coll != main_collection:
            coll.objects.unlink(gift_box)

# 更新场景
bpy.context.view_layer.update()
```