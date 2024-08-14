```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建主集合
main_collection = bpy.data.collections.new("Toy Car")
bpy.context.scene.collection.children.link(main_collection)

# 设置主集合为活动集合
layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

# 创建车身
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
car_body = bpy.context.active_object
car_body.name = "Car Body"
bpy.ops.transform.resize(value=(2, 1, 0.5))

# 确保车身只在主集合中
for coll in car_body.users_collection:
    if coll != main_collection:
        coll.objects.unlink(car_body)

# 创建轮子
def create_wheel(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.25, location=location)
    wheel = bpy.context.active_object
    wheel.name = name
    wheel.rotation_euler[0] = 1.5708  # 90 degrees in radians
    for coll in wheel.users_collection:
        if coll != main_collection:
            coll.objects.unlink(wheel)
    return wheel

# 创建四个轮子
wheel1 = create_wheel("Wheel 1", (1.5, 0.75, 0.25))
wheel2 = create_wheel("Wheel 2", (-1.5, 0.75, 0.25))
wheel3 = create_wheel("Wheel 3", (1.5, -0.75, 0.25))
wheel4 = create_wheel("Wheel 4", (-1.5, -0.75, 0.25))

# 创建车轴
def create_axle(name, location, length):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.125, depth=length, location=location)
    axle = bpy.context.active_object
    axle.name = name
    axle.rotation_euler[1] = 1.5708  # 90 degrees in radians
    for coll in axle.users_collection:
        if coll != main_collection:
            coll.objects.unlink(axle)
    return axle

# 创建车轴
axle1 = create_axle("Axle 1", (0, 0.75, 0.25), 3)
axle2 = create_axle("Axle 2", (0, -0.75, 0.25), 3)

# 更新场景
bpy.context.view_layer.update()
```