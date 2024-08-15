```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 删除所有多余的集合
for collection in bpy.data.collections:
    bpy.data.collections.remove(collection)

# 创建主集合
main_collection = bpy.data.collections.new("Toy Car")
bpy.context.scene.collection.children.link(main_collection)

# 设置主集合为活动集合
layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

# 创建车身
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.4))
car_body = bpy.context.active_object
car_body.name = "car_body"
bpy.ops.transform.resize(value=(2, 1, 0.4))

# 确保车身只在主集合中
for coll in car_body.users_collection:
    if coll != main_collection:
        coll.objects.unlink(car_body)

# 创建车轮
def create_wheel(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.1, location=location)
    wheel = bpy.context.active_object
    wheel.name = name
    
    # 确保车轮只在主集合中
    for coll in wheel.users_collection:
        if coll != main_collection:
            coll.objects.unlink(wheel)
    
    return wheel

# 创建四个车轮
wheel1 = create_wheel("wheel1", (1.5, -0.5, 0.2))
wheel2 = create_wheel("wheel2", (1.5, 0.5, 0.2))
wheel3 = create_wheel("wheel3", (-1.5, -0.5, 0.2))
wheel4 = create_wheel("wheel4", (-1.5, 0.5, 0.2))

# 创建车窗
def create_window(name, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    window = bpy.context.active_object
    window.name = name
    bpy.ops.transform.resize(value=(0.4, 0.1, 0.3))
    
    # 确保车窗只在主集合中
    for coll in window.users_collection:
        if coll != main_collection:
            coll.objects.unlink(window)
    
    return window

# 创建四个车窗
window1 = create_window("window1", (0.8, 0.55, 0.8))
window2 = create_window("window2", (-0.8, 0.55, 0.8))
window3 = create_window("window3", (0.8, -0.55, 0.8))
window4 = create_window("window4", (-0.8, -0.55, 0.8))

# 创建车门
def create_door(name, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    door = bpy.context.active_object
    door.name = name
    bpy.ops.transform.resize(value=(0.6, 0.1, 0.7))
    
    # 确保车门只在主集合中
    for coll in door.users_collection:
        if coll != main_collection:
            coll.objects.unlink(door)
    
    return door

# 创建两个车门
door1 = create_door("door1", (0.5, 0.6, 0.4))
door2 = create_door("door2", (-0.5, 0.6, 0.4))

# 更新场景
bpy.context.view_layer.update()
```