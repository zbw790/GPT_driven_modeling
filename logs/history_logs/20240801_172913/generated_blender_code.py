```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建主集合
main_collection = bpy.data.collections.new("Car")
bpy.context.scene.collection.children.link(main_collection)

# 创建车身
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
car_body = bpy.context.active_object
car_body.scale = (4.25 / 2, 1.75 / 2, 1.5 / 2)
car_body.name = "Car_Body"
main_collection.objects.link(car_body)

# 创建车轮
def create_wheel(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.325, depth=0.2, location=location)
    wheel = bpy.context.active_object
    wheel.rotation_euler[0] = 1.5708  # Rotate 90 degrees to align properly
    wheel.name = name
    main_collection.objects.link(wheel)
    return wheel

wheel_locations = [(1.5, 1.0, 0.325), (-1.5, 1.0, 0.325), (1.5, -1.0, 0.325), (-1.5, -1.0, 0.325)]
for i, loc in enumerate(wheel_locations):
    create_wheel(f"Wheel_{i+1}", loc)

# 创建发动机舱
bpy.ops.mesh.primitive_cube_add(size=1, location=(1.625, 0, 0.75))
engine_compartment = bpy.context.active_object
engine_compartment.scale = (1.0 / 2, 1.5 / 2, 0.6 / 2)
engine_compartment.name = "Engine_Compartment"
main_collection.objects.link(engine_compartment)

# 创建座椅
seat_locations = [(0, 0.5, 1.25), (0, -0.5, 1.25), (-1, 0.5, 1.25), (-1, -0.5, 1.25), (-2, 0, 1.25)]
for i, loc in enumerate(seat_locations):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    seat = bpy.context.active_object
    seat.scale = (0.5 / 2, 0.5 / 2, 1.0 / 2)
    seat.name = f"Seat_{i+1}"
    main_collection.objects.link(seat)

# 创建前大灯
headlight_locations = [(2.1, 0.75, 1.1), (2.1, -0.75, 1.1)]
for i, loc in enumerate(headlight_locations):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    headlight = bpy.context.active_object
    headlight.scale = (0.3 / 2, 0.2 / 2, 0.15 / 2)
    headlight.name = f"Headlight_{i+1}"
    main_collection.objects.link(headlight)

# 创建后尾灯
taillight_locations = [(-2.1, 0.75, 1.1), (-2.1, -0.75, 1.1)]
for i, loc in enumerate(taillight_locations):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    taillight = bpy.context.active_object
    taillight.scale = (0.25 / 2, 0.15 / 2, 0.1 / 2)
    taillight.name = f"Taillight_{i+1}"
    main_collection.objects.link(taillight)

# 创建后视镜
mirror_locations = [(1.9, 1.05, 1.25), (1.9, -1.05, 1.25)]
for i, loc in enumerate(mirror_locations):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    mirror = bpy.context.active_object
    mirror.scale = (0.2 / 2, 0.1 / 2, 0.15 / 2)
    mirror.name = f"Mirror_{i+1}"
    main_collection.objects.link(mirror)

# 确保所有对象只在主集合中
for obj in bpy.data.objects:
    if obj not in main_collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)

# 更新场景
bpy.context.view_layer.update()
```