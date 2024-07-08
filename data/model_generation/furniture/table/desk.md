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
cabinet_collection = bpy.data.collections.new("Cabinet")
main_collection.children.link(cabinet_collection)

# 创建抽屉子集合
drawers_collection = bpy.data.collections.new("Drawers")
cabinet_collection.children.link(drawers_collection)

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
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name].children[legs_collection.name]
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    leg = bpy.context.active_object
    leg.scale = (0.05, 0.05, 0.75)
    leg.name = name
    
    for coll in leg.users_collection:
        if coll != legs_collection:
            coll.objects.unlink(leg)
    
    bpy.context.view_layer.active_layer_collection = layer_collection
    
    return leg

# 创建两条桌腿
leg1 = create_leg("leg1", (0.7, 0.4, 0.375))
leg2 = create_leg("leg2", (0.7, -0.4, 0.375))

# 设置柜体厚度（单位：米）
cabinet_thickness = 0.02

# 创建柜子外壳
def create_cabinet_shell(length, width, height, thickness):
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name].children[cabinet_collection.name]

    location = (-length/2, 0, height/2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cabinet = bpy.context.active_object
    cabinet.scale = (length, width, height)
    cabinet.name = "cabinet_shell"

    inner_cube = create_cabinet_inner_cube(length, width, height, thickness, location)

    # 执行布尔差运算
    boolean_difference(cabinet, inner_cube)

    bpy.context.view_layer.active_layer_collection = layer_collection
    
    return cabinet

# 创建用于挖空的内部立方体
def create_cabinet_inner_cube(length, width, height, thickness, cabinet_location):
    inner_length = length - 2 * thickness
    inner_width = width - thickness
    inner_height = height - 2 * thickness
    
    inner_x = cabinet_location[0]
    inner_y = cabinet_location[1] - (thickness/2 + 0.001)
    inner_z = cabinet_location[2]
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(inner_x, inner_y, inner_z))
    inner_cube = bpy.context.active_object
    inner_cube.scale = (inner_length, inner_width, inner_height)
    inner_cube.name = "cabinet_inner_cube"
    return inner_cube

# 执行布尔差运算
def boolean_difference(obj1, obj2):
    bpy.ops.object.select_all(action='DESELECT')
    obj1.select_set(True)
    bpy.context.view_layer.objects.active = obj1
    obj2.select_set(True)
    bpy.ops.object.boolean_difference()

# 创建抽屉
def create_drawer(length, width, height, thickness, location):
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name].children[cabinet_collection.name].children[drawers_collection.name]

    # 创建抽屉外壳
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    drawer = bpy.context.active_object
    drawer.scale = (length, width, height)
    drawer.name = f"drawer_{len(drawers_collection.objects)}"

    inner_cube = create_drawer_inner_cube(length, width, height, thickness, location)

    # 执行布尔差运算
    boolean_difference(drawer, inner_cube)

    bpy.context.view_layer.active_layer_collection = layer_collection

    return drawer

def create_drawer_inner_cube(length, width, height, thickness, drawer_location):
    inner_length = length - 2 * thickness
    inner_width = width - 2 * thickness
    inner_height = height - thickness
    
    # 计算inner_cube的位置
    inner_x = drawer_location[0]
    inner_y = drawer_location[1]
    inner_z = drawer_location[2] + (thickness/2 + 0.001)  # 将inner_cube向上移动thickness/2,这里多加0.001是因为完全贴合的两个模型有时候不能正常移除某一边的面，使得外观看上去没有变化
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(inner_x, inner_y, inner_z))
    inner_cube = bpy.context.active_object
    inner_cube.scale = (inner_length, inner_width, inner_height)
    inner_cube.name = f"drawer_inner_{len(drawers_collection.objects)}"
    
    return inner_cube

# 主函数
def create_cabinet_with_drawers():
    # 获取桌面和桌腿的尺寸
    tabletop = bpy.data.objects["table_top"]
    leg = bpy.data.objects["leg1"]
    
    cabinet_length = 0.36  # 自定义长度
    cabinet_width = tabletop.scale[1] # 与桌面宽度相同
    cabinet_height = leg.scale[2]# 与桌腿高度相同
    
    # 创建柜子外壳
    cabinet_shell = create_cabinet_shell(cabinet_length, cabinet_width, cabinet_height, cabinet_thickness)
    
    # 抽屉参数
    drawer_count = 3
    gap = 0.005
    drawer_thickness = 0.01

    inner_height = cabinet_height - 2 * cabinet_thickness
    drawer_height = (inner_height - ((drawer_count + 1) * gap)) / drawer_count
    drawer_length = cabinet_length - 2 * cabinet_thickness - 2 * gap
    drawer_width = cabinet_width - cabinet_thickness - 2 * gap

    # 创建抽屉
    for i in range(drawer_count):
        drawer_z = (i + 1) * gap + i * drawer_height + drawer_height / 2 + cabinet_thickness
        drawer_location = (-cabinet_length/2 + cabinet_thickness + gap, -cabinet_thickness/2 - gap, drawer_z)
        create_drawer(drawer_length, drawer_width, drawer_height, drawer_thickness, drawer_location)

# 调用主函数
create_cabinet_with_drawers()

# 更新场景
bpy.context.view_layer.update()
```