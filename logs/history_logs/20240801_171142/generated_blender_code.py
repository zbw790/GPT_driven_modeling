```python
import bpy
import math

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建集合
main_collection = bpy.data.collections.new("ChristmasTree")
bpy.context.scene.collection.children.link(main_collection)

def create_cone(name, base_radius, top_radius, height, location):
    bpy.ops.mesh.primitive_cone_add(
        vertices=32, 
        radius1=base_radius, 
        radius2=top_radius, 
        depth=height, 
        location=location
    )
    cone = bpy.context.active_object
    cone.name = name
    main_collection.objects.link(cone)
    bpy.context.scene.collection.objects.unlink(cone)
    return cone

# 树干
trunk = create_cone("树干", 0.1, 0.05, 2, (0, 0, 1))

# 树冠
tree_height = 2
tree_radius_base = 0.75
tree_radius_top = 0.05
tree_top_offset = tree_height / 2
crown = create_cone("树冠", tree_radius_base, tree_radius_top, tree_height, (0, 0, tree_top_offset + 1))

def create_branches(name, base_radius, top_radius, height, num_branches, z_offset):
    for i in range(num_branches):
        angle = i * math.radians(360 / num_branches)
        x = base_radius * math.cos(angle)
        y = base_radius * math.sin(angle)
        create_cone(f"{name}_{i+1}", base_radius, top_radius, height, (x, y, z_offset + 1))

# 树枝
create_branches("树枝", 0.35, 0.025, 1.5, 8, 0.5)

# 树顶尖端
tip = create_cone("树顶尖端", 0.05, 0.01, 0.2, (0, 0, 3))

# 底座
bpy.ops.mesh.primitive_cube_add(size=0.8, location=(0, 0, 0.1))
base = bpy.context.active_object
base.dimensions = (0.8, 0.8, 0.1)
base.name = "底座"
main_collection.objects.link(base)
bpy.context.scene.collection.objects.unlink(base)

# 更新场景
bpy.context.view_layer.update()
```