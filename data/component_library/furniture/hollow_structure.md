# 家具挖空技术指南

这个指南介绍了在Blender中为家具模型创建挖空结构的技术。这种方法主要用于生成如抽屉、柜门、凹槽等需要内部空间的家具组件。

## 主要应用

1. 抽屉：创建抽屉外壳和内部空间
2. 柜门：制作带有内部空间的柜门
3. 书柜/衣柜：为柜体创建内部存储空间
4. 桌面：制作带有线缆管理孔或其他凹槽的桌面
5. 沙发/椅子：创建带有软垫凹槽的框架结构

## 基本原理

挖空技术的核心是使用布尔差运算。这个过程包括:
1. 创建主要物体（如抽屉外壳）
2. 创建一个稍小的内部物体
3. 使用布尔差运算从主要物体中减去内部物体，形成空腔

## 关键参数

- 外壳厚度：决定了结构的强度和重量
- 内部尺寸：影响可用空间大小
- 布尔精度：影响操作的精确度和最终模型的质量

## 实现步骤

1. 创建外部物体
2. 创建内部物体（尺寸略小于外部物体）
3. 正确定位内部物体
4. 应用布尔差运算
5. 清理和优化结果模型

## 示例代码

以下是一个创建简单挖空立方体的函数示例：

```python
import bpy

def create_hollow_cube(name, outer_dimensions, thickness):
    # 创建外部立方体
    bpy.ops.mesh.primitive_cube_add(size=1)
    outer_cube = bpy.context.active_object
    outer_cube.name = name
    outer_cube.scale = outer_dimensions

    # 创建内部立方体
    inner_dimensions = [
        outer_dimensions[0] - 2 * thickness,
        outer_dimensions[1] - 2 * thickness,
        outer_dimensions[2] - 2 * thickness
    ]
    bpy.ops.mesh.primitive_cube_add(size=1)
    inner_cube = bpy.context.active_object
    inner_cube.scale = inner_dimensions

    # 应用布尔差运算
    bool_modifier = outer_cube.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_modifier.object = inner_cube
    bool_modifier.operation = 'DIFFERENCE'

    # 应用修改器
    bpy.context.view_layer.objects.active = outer_cube
    bpy.ops.object.modifier_apply(modifier="Boolean")

    # 删除内部立方体
    bpy.data.objects.remove(inner_cube, do_unlink=True)

    return outer_cube

# 使用示例
hollow_cube = create_hollow_cube("HollowCube", (0.5, 0.3, 0.2), 0.02)
```

## 注意事项

1. 确保内部物体完全包含在外部物体内
2. 避免非常薄的壁厚，可能导致渲染问题
3. 复杂形状可能需要多个布尔运算
4. 布尔运算后检查并清理网格拓扑
5. 考虑使用细分曲面修改器来平滑边缘

## 高级技巧

1. 使用阵列修改器创建多个挖空
2. 结合倒角或圆角修改器改善外观
3. 使用曲线变形创建非直线的挖空形状
4. 应用材质来区分内外表面