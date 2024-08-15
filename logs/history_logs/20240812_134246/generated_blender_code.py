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

# 创建桌面
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0.75))
table_top = bpy.context.active_object
table_top.name = "table_top"
table_top.scale = (1.5, 0.9, 0.03)

# 确保桌面只在主集合中
for coll in table_top.users_collection:
    if coll != main_collection:
        coll.objects.unlink(table_top)

# 创建桌腿
def create_leg(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.72, location=location)
    leg = bpy.context.active_object
    leg.name = name
    
    # 确保桌腿只在legs集合中
    for coll in leg.users_collection:
        if coll != legs_collection:
            coll.objects.unlink(leg)
    
    return leg

# 创建四条桌腿
leg1 = create_leg("leg1", (0.7, 0.4, 0.36))
leg2 = create_leg("leg2", (-0.7, 0.4, 0.36))
leg3 = create_leg("leg3", (0.7, -0.4, 0.36))
leg4 = create_leg("leg4", (-0.7, -0.4, 0.36))

# 更新场景
bpy.context.view_layer.update()
```