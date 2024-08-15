```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建主集合
main_collection = bpy.data.collections.new("Dining Table")
bpy.context.scene.collection.children.link(main_collection)

# 创建子集合
legs_collection = bpy.data.collections.new("Legs")
main_collection.children.link(legs_collection)

# 设置主集合为活动集合
layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

# 创建桌面
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.name = "table_top"
tabletop.scale = (1.5, 0.9, 0.03)  # 长度150cm, 宽度90cm, 厚度3cm
for coll in tabletop.users_collection:
    if coll != main_collection:
        coll.objects.unlink(tabletop)

# 桌腿位置
leg_positions = [(0.73, 0.43, 0.36), (-0.73, 0.43, 0.36), (0.73, -0.43, 0.36), (-0.73, -0.43, 0.36)]  # 每条腿的位置

# 创建桌腿
for i, pos in enumerate(leg_positions):
    bpy.context.view_layer.active_layer_collection = layer_collection.children[legs_collection.name]
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.72, location=pos)
    leg = bpy.context.active_object
    leg.name = f"leg{i+1}"
    for coll in leg.users_collection:
        if coll != legs_collection:
            coll.objects.unlink(leg)
    bpy.context.view_layer.active_layer_collection = layer_collection

# 更新场景
bpy.context.view_layer.update()
```