```python
import bpy
import random

# 删除所有对象
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 创建树干
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=50, depth=200, location=(0, 0, 100))
trunk = bpy.context.object
trunk.name = "树干"

# 创建树枝（一个大的圆锥来表示针叶树）
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=150, depth=300, location=(0, 0, 250))
branches = bpy.context.object
branches.name = "树枝"

# 创建树顶装饰（星形）
bpy.ops.mesh.primitive_star_add(radius1=10, radius2=5, number_of_points=5, location=(0, 0, 450))
topper = bpy.context.object
topper.name = "树顶装饰"
bpy.ops.transform.rotate(value=1.5708, orient_axis='X')  # 旋转90度

# 创建装饰球
for _ in range(20):
    x = random.uniform(-125, 125)
    y = random.uniform(-125, 125)
    z = random.uniform(100, 400)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=5, location=(x, y, z))
    ball = bpy.context.object
    ball.name = "装饰球"

# 创建灯串（用贝塞尔曲线表示）
bpy.ops.curve.primitive_bezier_circle_add(radius=2)
curve = bpy.context.object
curve.name = "灯串"
bpy.ops.object.convert(target='MESH')  # 转换为网格

# 将灯串缠绕在树上
for i in range(500):
    bpy.ops.object.duplicate()
    bpy.ops.transform.translate(value=(random.uniform(-150, 150), random.uniform(-150, 150), random.uniform(100, 400)))

# 集合所有对象到树的集合
tree_collection = bpy.data.collections.new('ChristmasTree')
bpy.context.scene.collection.children.link(tree_collection)
tree_objects = [trunk, branches, topper] + [obj for obj in bpy.context.selected_objects]
for obj in tree_objects:
    tree_collection.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)
```