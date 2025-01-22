# 吧凳生成指南

这段代码专门用于在Blender中生成一个简单的吧凳模型。

## 基本结构

生成的吧凳由以下部分组成:
- 1个座面 (生成时,标注为 `seat_1`)
- 4个椅腿 (生成时,标注为 `leg_1_1`, `leg_1_2`, `leg_1_3`, `leg_1_4`)
- 1个脚踏环 (生成时,标注为 `footrest_1`)

## 尺寸参考

代码中使用的尺寸如下:

- 座面: 半径20cm, 厚度5cm (radius=0.2m, depth=0.05m in Blender)
- 椅腿: 半径2cm, 高70cm (radius=0.02m, depth=0.7m in Blender)
- 脚踏环: 主半径15cm, 次半径1cm (major_radius=0.15m, minor_radius=0.01m in Blender)
- 吧凳总高: 72.5cm (0.725m in Blender)

注意: Blender使用米作为默认单位,所以在创建模型时,代码中的数值已经是米为单位。

## 生成步骤

1. 创建一个名为 "bar_stools" 的主集合
2. 创建一个名为 "bar_stool_1" 的子集合
3. 创建座面并添加到子集合中
4. 创建四个椅腿并添加到子集合中
5. 创建脚踏环并添加到子集合中
6. 从场景集合中移除所有对象,确保它们只存在于自定义集合中

## 主要函数

代码中定义了一个主要函数 `create_bar_stool(index, x, y)`:

- `index`: 吧凳的编号
- `x`, `y`: 吧凳在场景中的x和y坐标

这个函数负责创建吧凳的所有部件,并将它们组织到适当的集合中。

## 示例代码
```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create bar_stools collection
bar_stools_coll = bpy.data.collections.new("bar_stools")
bpy.context.scene.collection.children.link(bar_stools_coll)

def create_bar_stool(index, x, y):
    stool_coll = bpy.data.collections.new(f"bar_stool_{index}")
    bar_stools_coll.children.link(stool_coll)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.05, location=(x, y, 0.725))
    seat = bpy.context.active_object
    seat.name = f"seat_{index}"
    stool_coll.objects.link(seat)
    bpy.context.collection.objects.unlink(seat)
    
    leg_positions = [(-0.15, -0.15), (0.15, -0.15), (0.15, 0.15), (-0.15, 0.15)]
    for i, (dx, dy) in enumerate(leg_positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.7, location=(x + dx, y + dy, 0.35))
        leg = bpy.context.active_object
        leg.name = f"leg_{index}_{i+1}"
        stool_coll.objects.link(leg)
        bpy.context.collection.objects.unlink(leg)
    
    bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.01, location=(x, y, 0.3))
    footrest = bpy.context.active_object
    footrest.name = f"footrest_{index}"
    stool_coll.objects.link(footrest)
    bpy.context.collection.objects.unlink(footrest)

create_bar_stool(1, -0.5, -0.8)
```


## 注意事项

- 所有部件都有适当的标注
- 吧凳模型的位置可以通过函数参数 `x` 和 `y` 来调整
- 各个部件保持独立,没有合并成一个整体模型
- 椅腿的位置是预先计算好的,确保它们正确地支撑座面

## 使用说明

1. 将此脚本复制到Blender的文本编辑器中。
2. 如果只需要一个吧凳,可以删除或注释掉最后一行 `create_bar_stool(2, 0.5, -0.8)`。
3. 运行脚本以创建一个基础的吧凳模型。
4. 可以通过修改 `create_bar_stool(1, -0.5, -0.8)` 中的坐标值来调整吧凳的位置。

## 扩展思路

- 可以添加更多细节,如座面的纹理或椅腿的造型。
- 可以创建不同样式的吧凳,如带靠背的吧凳或可旋转的吧凳。
- 可以添加材质和纹理来增强模型的视觉效果。
- 可以调整各部件的尺寸参数来创建不同高度或样式的吧凳。