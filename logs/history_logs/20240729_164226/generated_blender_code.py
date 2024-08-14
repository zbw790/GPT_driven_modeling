```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 创建主集合
main_collection = bpy.data.collections.new("ToyCar")
bpy.context.scene.collection.children.link(main_collection)

# 创建车身
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
car_body = bpy.context.active_object
car_body.scale = (2, 1, 0.5)
car_body.name = "CarBody"
main_collection.objects.link(car_body)
bpy.context.scene.collection.objects.unlink(car_body)

# 创建车轮
for i in range(4):
    x = 1.2 if i % 2 == 0 else -1.2
    y = 0.9 if i < 2 else -0.9
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.5, location=(x, y, 0.2))
    car_wheel = bpy.context.active_object
    car_wheel.rotation_euler = (1.5708, 0, 0) # 90 degrees rotation on X-axis
    car_wheel.name = f"CarWheel_{i+1}"
    main_collection.objects.link(car_wheel)
    bpy.context.scene.collection.objects.unlink(car_wheel)

# 创建车窗
def create_window(name, location, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    car_window = bpy.context.active_object
    car_window.scale = size
    car_window.name = name
    main_collection.objects.link(car_window)
    bpy.context.scene.collection.objects.unlink(car_window)
    
create_window("FrontWindow", (0, 0.5, 1), (0.5, 0.05, 0.3))
create_window("BackWindow", (0, -0.5, 1), (0.5, 0.05, 0.3))
create_window("LeftWindow", (-1, 0, 1), (0.05, 0.5, 0.3))
create_window("RightWindow", (1, 0, 1), (0.05, 0.5, 0.3))

# 更新场景
bpy.context.view_layer.update()
```