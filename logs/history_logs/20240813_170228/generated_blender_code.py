```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建主集合
main_collection = bpy.data.collections.new("Dining Table")
bpy.context.scene.collection.children.link(main_collection)

# 设置主集合为活动集合
layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

# 创建桌面
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.name = "table_top"
bpy.ops.transform.resize(value=(1.35, 0.9, 0.03))

# 确保桌面只在主集合中
for coll in tabletop.users_collection:
    if coll != main_collection:
        coll.objects.unlink(tabletop)

# 创建桌腿
def create_leg(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.72, location=location)
    leg = bpy.context.active_object
    leg.name = name
    
    # 确保桌腿只在主集合中
    for coll in leg.users_collection:
        if coll != main_collection:
            coll.objects.unlink(leg)
    
    return leg

# 创建四条桌腿
leg1 = create_leg("leg1", (1.2, 0.75, 0.36))  # 位置 120cm右, 75cm上, 高度一半
leg2 = create_leg("leg2", (-1.2, 0.75, 0.36))  # 位置 120cm左, 75cm上, 高度一半
leg3 = create_leg("leg3", (1.2, -0.75, 0.36))  # 位置 120cm右, 75cm下, 高度一半
leg4 = create_leg("leg4", (-1.2, -0.75, 0.36))  # 位置 120cm左, 75cm下, 高度一半

# 更新场景
bpy.context.view_layer.update()
```