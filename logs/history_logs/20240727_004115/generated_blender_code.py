```python
import bpy

# 删除所有现有对象
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 创建树干
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=50, radius2=5, depth=200, location=(0, 0, 100))
tree_trunk = bpy.context.object
tree_trunk.name = "Tree_Trunk"

# 创建树枝层
for i in range(6):
    layer_height = 200 - (i * 30)
    radius1 = 50 - (i * 8)
    radius2 = 50 - ((i + 1) * 8)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radius1, radius2=radius2, depth=30, location=(0, 0, layer_height))
    layer = bpy.context.object
    layer.name = f"Tree_Layer_{i+1}"

# 创建树顶尖端
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=5, radius2=1, depth=20, location=(0, 0, 210))
tree_top = bpy.context.object
tree_top.name = "Tree_Top"

# 将所有部分合并为一个对象
bpy.ops.object.select_all(action='DESELECT')
tree_trunk.select_set(True)
for i in range(6):
    bpy.data.objects[f"Tree_Layer_{i+1}"].select_set(True)
tree_top.select_set(True)
bpy.context.view_layer.objects.active = tree_trunk
bpy.ops.object.join()

# 设置树的材质
material = bpy.data.materials.new(name="Tree_Material")
material.diffuse_color = (0.0, 0.5, 0.0, 1.0)  # 深绿色
bpy.context.object.data.materials.append(material)
```