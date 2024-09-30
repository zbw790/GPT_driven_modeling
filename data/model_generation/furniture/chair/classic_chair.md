# 椅子生成指南

这段代码专门用于在Blender中生成一个简单的椅子模型。

## 准备工作

在生成新模型之前,代码会清空场景中的所有现有对象。这通过以下Blender命令实现:

```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

## 基本结构

生成的椅子由以下部分组成:
- 1个座面 (生成时,标注为 `座面`)
- 1个靠背 (生成时,标注为 `靠背`)
- 4个椅腿 (生成时,标注为 `椅腿_1`, `椅腿_2`, `椅腿_3`, `椅腿_4`)

## 尺寸参考

代码中使用的尺寸如下:

- 座面: 45cm x 45cm x 5cm (0.45m x 0.45m x 0.05m in Blender)
- 靠背: 45cm x 5cm x 50cm (0.45m x 0.05m x 0.5m in Blender)
- 椅腿: 半径2cm, 高45cm (radius=0.02m, height=0.45m in Blender)
- 椅子总高: 95cm (0.95m in Blender)

注意: Blender使用米作为默认单位,所以在创建模型时,代码中的数值已经是米为单位。

## 生成步骤

1. 清空场景中的所有现有对象
2. 创建一个新的集合 "椅子"
3. 创建座面
4. 创建靠背
5. 创建四个椅腿
6. 将所有部件添加到 "椅子" 集合中
7. 从场景集合中移除所有对象,确保它们只存在于自定义集合中
8. 更新场景视图

## 生成代码
```python
import bpy
import math

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建集合
main_collection = bpy.data.collections.new("椅子")
bpy.context.scene.collection.children.link(main_collection)

def create_cuboid(name, dimensions, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = dimensions
    main_collection.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)
    return obj

def create_cylinder(name, radius, height, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location)
    obj = bpy.context.active_object
    obj.name = name
    main_collection.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)
    return obj

# 创建座面
seat = create_cuboid("座面", (0.45, 0.45, 0.05), (0, 0, 0.45))

# 创建靠背
backrest = create_cuboid("靠背", (0.45, 0.05, 0.5), (0, -0.2, 0.7))

# 创建椅腿
leg_positions = [
    (0.2, 0.2, 0.225),
    (-0.2, 0.2, 0.225),
    (0.2, -0.2, 0.225),
    (-0.2, -0.2, 0.225)
]

for i, pos in enumerate(leg_positions):
    create_cylinder(f"椅腿_{i+1}", 0.02, 0.45, pos)

# 更新场景
bpy.context.view_layer.update()
```

## 辅助函数

代码中定义了两个辅助函数:

1. `create_cuboid(name, dimensions, location)`: 用于创建立方体形状的对象(如座面和靠背)
2. `create_cylinder(name, radius, height, location)`: 用于创建圆柱体形状的对象(如椅腿)

这些函数负责创建对象,设置其名称、尺寸和位置,并将其添加到 "椅子" 集合中。

## 注意事项

- 所有部件都有适当的标注
- 椅子模型位于场景的中心点附近 (0, 0, 0)
- 各个部件保持独立,没有合并成一个整体模型
- 椅腿的位置是预先计算好的,确保它们正确地支撑座面

## 使用说明

1. 将此脚本复制到Blender的文本编辑器中。
2. 运行脚本以创建一个基础的椅子模型。
3. 可以通过修改代码中的尺寸值来调整椅子的大小和比例。

## 扩展思路

- 可以添加更多细节,如座面的纹理或靠背的曲线。
- 可以创建不同样式的椅子,如扶手椅或办公椅。
- 可以添加材质和纹理来增强模型的视觉效果。
- 可以添加圆角或倒角来使模型看起来更加真实。
