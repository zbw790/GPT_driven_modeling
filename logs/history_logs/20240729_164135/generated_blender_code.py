```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 创建主集合
main_collection = bpy.data.collections.new("ChristmasTree")
bpy.context.scene.collection.children.link(main_collection)

# 创建树干
bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=2, location=(0, 0, 1))
tree_trunk = bpy.context.active_object
tree_trunk.name = "TreeTrunk"

# 把树干添加到主集合
main_collection.objects.link(tree_trunk)
bpy.context.scene.collection.objects.unlink(tree_trunk)

# 创建树枝（用多个圆锥体表示）
for i in range(3):
    bpy.ops.mesh.primitive_cone_add(radius1=1.5 - i*0.5, radius2=0, depth=3, location=(0, 0, 3 + i*1.5))
    tree_branch = bpy.context.active_object
    tree_branch.name = f"TreeBranch_{i+1}"
    main_collection.objects.link(tree_branch)
    bpy.context.scene.collection.objects.unlink(tree_branch)

# 创建树顶装饰
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 7))
top_decoration = bpy.context.active_object
top_decoration.name = "TopDecoration"
main_collection.objects.link(top_decoration)
bpy.context.scene.collection.objects.unlink(top_decoration)

# 创建装饰球
for i in range(20):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(1.5*(i%2)-0.75, 1.5*((i//2)%2)-0.75, 3 + (i//4)*1.5))
    decoration_ball = bpy.context.active_object
    decoration_ball.name = f"DecorationBall_{i+1}"
    main_collection.objects.link(decoration_ball)
    bpy.context.scene.collection.objects.unlink(decoration_ball)

# 创建礼物盒
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(i-2, -2, 0.5))
    gift_box = bpy.context.active_object
    gift_box.name = f"GiftBox_{i+1}"
    main_collection.objects.link(gift_box)
    bpy.context.scene.collection.objects.unlink(gift_box)

# 更新场景
bpy.context.view_layer.update()
```