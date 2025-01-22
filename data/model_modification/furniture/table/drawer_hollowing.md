# 抽屉挖空指南

本指南介绍了如何在 Blender 中使用 Python 脚本创建中空的抽屉模型。这种技术通常用于创建更真实的家具模型，如办公桌或衣柜的抽屉。

## 原理

创建中空抽屉的基本原理是：
1. 创建一个实心的立方体作为抽屉的外壳。
2. 创建一个稍小的立方体作为内部空间。
3. 使用布尔差运算从外壳中减去内部立方体，形成中空结构。

## 关键函数

### 创建抽屉

```python
def create_drawer(length, width, height, thickness, location):
    # 创建抽屉外壳
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    drawer = bpy.context.active_object
    drawer.scale = (length, width, height)
    drawer.name = f"drawer_{bpy.context.scene.objects.find(drawer.name)}"

    inner_cube = create_drawer_inner_cube(length, width, height, thickness, location)

    # 执行布尔差运算
    boolean_difference(drawer, inner_cube)

    return drawer
```

这个函数创建抽屉的外壳，然后调用 `create_drawer_inner_cube` 函数创建内部立方体，最后使用布尔差运算挖空抽屉。

### 创建内部立方体

```python
def create_drawer_inner_cube(length, width, height, thickness, drawer_location):
    inner_length = length - 2 * thickness
    inner_width = width - 2 * thickness
    inner_height = height - thickness
    
    # 计算inner_cube的位置
    inner_x = drawer_location[0]
    inner_y = drawer_location[1]
    inner_z = drawer_location[2] + (thickness/2 + 0.001)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(inner_x, inner_y, inner_z))
    inner_cube = bpy.context.active_object
    inner_cube.scale = (inner_length, inner_width, inner_height)
    inner_cube.name = f"drawer_inner_{bpy.context.scene.objects.find(inner_cube.name)}"
    
    return inner_cube
```

这个函数创建一个稍小的内部立方体，用于从抽屉外壳中挖空。注意内部立方体的尺寸和位置计算，确保留下适当的壁厚。

### 布尔差运算

```python
def boolean_difference(obj1, obj2):
    bpy.ops.object.select_all(action='DESELECT')
    obj1.select_set(True)
    bpy.context.view_layer.objects.active = obj1
    obj2.select_set(True)
    bpy.ops.object.boolean_difference()
```

这个函数执行布尔差运算，从 obj1（抽屉外壳）中减去 obj2（内部立方体）。

## 使用方法

1. 在 Blender 中打开 Python 控制台或文本编辑器。
2. 复制并粘贴上述函数。
3. 调用 `create_drawer` 函数，指定所需的尺寸和位置。

例如：

```python
drawer = create_drawer(length=0.5, width=0.4, height=0.2, thickness=0.01, location=(0, 0, 0))
```

这将创建一个长 50cm、宽 40cm、高 20cm，壁厚 1cm 的中空抽屉。

## 注意事项

- 确保 `thickness` 参数不要太大，否则可能导致抽屉内部空间过小。
- 可以根据需要调整内部立方体的位置和大小，以创建不同类型的抽屉（如带有前板的抽屉）。
- 这个方法创建的是简单的矩形抽屉，如需更复杂的形状，可能需要修改代码或使用其他建模技术。

```