```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建主集合
main_collection = bpy.data.collections.new("ToyCar")
bpy.context.scene.collection.children.link(main_collection)

# 创建车身
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
car_body = bpy.context.active_object
car_body.name = "CarBody"
bpy.ops.transform.resize(value=(2, 1, 0.5))

# 确保车身只在主集合中
for coll in car_body.users_collection:
    if coll != main_collection:
        coll.objects.unlink(car_body)

# 创建车轮
def create_wheel(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.4, location=location)
    wheel = bpy.context.active_object
    wheel.name = name

    # 确保车轮只在主集合中
    for coll in wheel.users_collection:
        if coll != main_collection:
            coll.objects.unlink(wheel)
    
    return wheel

# 创建四个车轮
wheel1 = create_wheel("Wheel1", (1.5, 0.8, 0.2))
wheel2 = create_wheel("Wheel2", (-1.5, 0.8, 0.2))
wheel3 = create_wheel("Wheel3", (1.5, -0.8, 0.2))
wheel4 = create_wheel("Wheel4", (-1.5, -0.8, 0.2))

# 创建车轴
def create_axle(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2.8, location=location)
    axle = bpy.context.active_object
    axle.name = name
    bpy.ops.transform.rotate(value=1.5708, orient_axis='X')

    # 确保车轴只在主集合中
    for coll in axle.users_collection:
        if coll != main_collection:
            coll.objects.unlink(axle)

    return axle

# 创建两个车轴
axle1 = create_axle("Axle1", (0, 0.8, 0.2))
axle2 = create_axle("Axle2", (0, -0.8, 0.2))

# 创建车窗
def create_window(name, location, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    window = bpy.context.active_object
    window.name = name
    bpy.ops.transform.resize(value=size)

    # 确保车窗只在主集合中
    for coll in window.users_collection:
        if coll != main_collection:
            coll.objects.unlink(window)

    return window

# 创建四个车窗
window1 = create_window("Window1", (0, 0.6, 1), (1.6, 0.1, 0.4))
window2 = create_window("Window2", (0, -0.6, 1), (1.6, 0.1, 0.4))
window3 = create_window("Window3", (1.9, 0, 1), (0.1, 0.9, 0.4))
window4 = create_window("Window4", (-1.9, 0, 1), (0.1, 0.9, 0.4))

# 更新场景
bpy.context.view_layer.update()
```