```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建圣诞树主集合
main_collection = bpy.data.collections.new("ChristmasTree")
bpy.context.scene.collection.children.link(main_collection)

# 设置主集合为活动集合
layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

# 创建树干
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(0, 0, 1))
trunk = bpy.context.active_object
trunk.name = "TreeTrunk"

# 创建树枝和树叶（简化为一个锥形）
bpy.ops.mesh.primitive_cone_add(radius1=1.5, depth=3, location=(0, 0, 3))
branches = bpy.context.active_object
branches.name = "TreeBranches"
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=5)
bpy.ops.object.mode_set(mode='OBJECT')

# 创建树顶装饰
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 5))
top_decor = bpy.context.active_object
top_decor.name = "TreeTopDecor"

# 创建装饰球
for i in range(20):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0.5 - (i % 5) * 0.2, -0.5 + (i // 5) * 0.2, 1.5 + (i % 3) * 0.6))
    ball = bpy.context.active_object
    ball.name = f"DecorBall_{i+1}"

# 创建彩灯串（简化为缠绕的线）
bpy.ops.curve.primitive_bezier_circle_add(radius=1.5, location=(0, 0, 3))
lights = bpy.context.active_object
lights.name = "Lights"
bpy.ops.object.convert(target='MESH')

# 创建礼物盒
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(1 - (i % 3) * 0.4, -1 + (i // 3) * 0.4, 0.15))
    gift = bpy.context.active_object
    gift.name = f"GiftBox_{i+1}"

# 更新场景
bpy.context.view_layer.update()
```