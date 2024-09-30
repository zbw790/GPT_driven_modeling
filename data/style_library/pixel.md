# 体素化风格生成指南

体素化是一种将3D模型转换为由小立方体（体素）组成的风格。这种风格常用于创建像素艺术风格的3D模型，特别适合复古游戏或简约设计。

## 特征

1. 由小立方体组成：整个模型由大小相等的小立方体构成。
2. 像素化外观：从远处看，模型呈现出像素化的外观。
3. 简化细节：复杂的曲面和细节被简化为方块状结构。
4. 可调整分辨率：通过改变体素大小，可以调整模型的"分辨率"。

## 参数示例

以下是体素化函数的参数示例：

```json
{
    "voxel_size": 0.02,
    "gap": 0.002,
    "collection_name": "Voxelized_Model"
}
```

## 核心函数：voxelize_object

这个函数接受一个Blender对象，并将其转换为体素化版本。

```python
import bpy
import bmesh
from mathutils import Vector

def voxelize_object(obj, voxel_size=0.05, gap=0.005):
    # 获取对象的边界框
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    bbox_min = Vector(map(min, zip(*bbox_corners)))
    bbox_max = Vector(map(max, zip(*bbox_corners)))

    # 计算体素网格的维度
    dimensions = bbox_max - bbox_min
    voxels_x = int(dimensions.x / voxel_size) + 1
    voxels_y = int(dimensions.y / voxel_size) + 1
    voxels_z = int(dimensions.z / voxel_size) + 1

    # 创建一个新的集合来存放体素
    voxel_collection = bpy.data.collections.new(f"{obj.name}_Voxels")
    bpy.context.scene.collection.children.link(voxel_collection)

    # 创建体素
    for x in range(voxels_x):
        for y in range(voxels_y):
            for z in range(voxels_z):
                voxel_center = bbox_min + Vector((x + 0.5, y + 0.5, z + 0.5)) * voxel_size
                
                # 检查体素中心是否在原始对象内部
                hit, loc, norm, face = obj.closest_point_on_mesh(obj.matrix_world.inverted() @ voxel_center)
                if hit and (obj.matrix_world @ loc - voxel_center).length <= voxel_size / 2:
                    bpy.ops.mesh.primitive_cube_add(size=voxel_size-gap, location=voxel_center)
                    voxel = bpy.context.active_object
                    voxel_collection.objects.link(voxel)
                    bpy.context.collection.objects.unlink(voxel)

    # 隐藏原始对象
    obj.hide_set(True)
    obj.hide_render = True

    return voxel_collection
```

## 使用说明

1. 将 `voxelize_object` 函数复制到你的Blender Python脚本中。
2. 选择要体素化的对象。
3. 调用函数，传入选中的对象和所需的参数。

示例：
```python
selected_obj = bpy.context.active_object
voxelized_collection = voxelize_object(selected_obj, voxel_size=0.02, gap=0.002)
```

## 参数说明

- `obj`: 要体素化的Blender对象。
- `voxel_size`: 每个体素的大小。较小的值会产生更精细的结果，但也会增加处理时间和生成的对象数量。
- `gap`: 体素之间的间隙。这有助于区分各个体素。

## 注意事项

1. 处理时间：对于复杂或大型的模型，体素化过程可能需要较长时间。
2. 性能影响：生成的体素数量可能很大，这可能会影响Blender的性能。
3. 内存使用：大量的体素可能会占用大量内存。
4. 原始模型：原始模型会被隐藏，但不会被删除。
5. 新集合：体素化的结果会被放置在一个新的集合中，以便于管理。

## 自定义

你可以通过调整以下方面来自定义体素化效果：

1. 改变 `voxel_size` 来调整体素的大小和模型的整体分辨率。
2. 修改 `gap` 参数来调整体素之间的间隙。
3. 在体素创建过程中添加随机偏移，以创造更有机的外观。
4. 为体素添加材质或颜色变化，以增加视觉趣味。

## 优化建议

1. 对于大型模型，考虑使用八叉树或其他空间分割技术来优化体素生成过程。
2. 使用实例化而不是单独的立方体对象来减少内存使用和提高渲染性能。
3. 对于动画，考虑使用粒子系统或其他技术来实现更高效的体素化效果。