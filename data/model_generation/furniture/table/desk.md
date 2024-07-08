# 办公桌

```python
import bpy
import bmesh

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 删除所有多余的集合
for collection in bpy.data.collections:
    bpy.data.collections.remove(collection)
    
# 创建主集合
main_collection = bpy.data.collections.new("Dining Table")
bpy.context.scene.collection.children.link(main_collection)

# 创建桌脚子集合
legs_collection = bpy.data.collections.new("Legs")
main_collection.children.link(legs_collection)

# 创建柜子子集合
canbinet_collection = bpy.data.collections.new("Cabinet")
main_collection.children.link(canbinet_collection)

# 设置主集合为活动集合
layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

# 创建桌板
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.scale = (1.5, 0.9, 0.03)
tabletop.name = "table_top"

# 确保桌板只在主集合中
for coll in tabletop.users_collection:
    if coll != main_collection:
        coll.objects.unlink(tabletop)

# 创建桌腿
def create_leg(name, location):
    # 临时将活动集合设置为legs_collection
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name].children[legs_collection.name]
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    leg = bpy.context.active_object
    leg.scale = (0.05, 0.05, 0.75)
    leg.name = name
    
    # 确保桌腿只在legs集合中
    for coll in leg.users_collection:
        if coll != legs_collection:
            coll.objects.unlink(leg)
    
    # 恢复主集合为活动集合
    bpy.context.view_layer.active_layer_collection = layer_collection
    
    return leg

# 创建两条条桌腿
leg1 = create_leg("leg1", (0.7, 0.4, 0.375))
leg2 = create_leg("leg2", (0.7, -0.4, 0.375))

# 设置柜体厚度（单位：米）
cabinet_thickness = 0.02

# 创建柜子外壳
def create_cabinet_shell(length, width, height):
    # 临时将活动集合设置为legs_collection
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name].children[canbinet_collection.name]

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    cabinet = bpy.context.active_object
    cabinet.scale = (length, width, height)
    cabinet.location = (-length/2, 0, height/2)
    cabinet.name = "cabinet_shell"

    # 恢复主集合为活动集合
    bpy.context.view_layer.active_layer_collection = layer_collection
    
    return cabinet

# 创建用于挖空的内部立方体
def create_inner_cube(length, width, height, thickness):
    inner_length = length - 2 * thickness
    inner_width = width - thickness
    inner_height = height - 2 * thickness
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    inner_cube = bpy.context.active_object
    inner_cube.scale = (inner_length, inner_width, inner_height)
    inner_cube.location = (-length/2, -thickness/2, height/2)
    inner_cube.name = "inner_cube"
    return inner_cube

# 执行布尔差运算
def boolean_difference(obj1, obj2):
    bpy.ops.object.select_all(action='DESELECT')
    obj1.select_set(True)
    bpy.context.view_layer.objects.active = obj1
    obj2.select_set(True)
    bpy.ops.object.boolean_difference()

# 主函数
def create_cabinet():
    # 获取桌面和桌腿的尺寸
    tabletop = bpy.data.objects["table_top"]
    leg = bpy.data.objects["leg1"]
    
    cabinet_length = 0.36  # 自定义长度
    cabinet_width = tabletop.scale[1] # 与桌面宽度相同
    cabinet_height = leg.scale[2] # 与桌腿高度相同
    
    # 创建柜子外壳
    cabinet_shell = create_cabinet_shell(cabinet_length, cabinet_width, cabinet_height)
    
    # 创建内部立方体用于挖空
    inner_cube = create_inner_cube(cabinet_length, cabinet_width, cabinet_height, cabinet_thickness)
    
    # 执行布尔差运算
    boolean_difference(cabinet_shell, inner_cube)
    
    # 将柜子移动到适当位置
    cabinet_shell.location = (-cabinet_length/2, 0, cabinet_height/2)
    

# 调用主函数
create_cabinet()

# 更新场景
bpy.context.view_layer.update()
```