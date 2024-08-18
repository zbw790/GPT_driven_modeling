# 餐桌生成指南

这段代码专门用于生成餐桌或宴会桌类型的桌子。这类桌子的主要特征包括：

1. 结构简单：主要由桌板和桌腿组成
2. 桌板通常较大：适合多人同时用餐
3. 桌板形状：通常为长方形，也可能是圆形或椭圆形
4. 桌腿位置：通常位于桌板的各个角落
6. 用途：主要用于日常用餐、家庭聚餐或大型宴会

这个生成器创建的是一个基础版本的餐桌，包含一个长方形桌板和四条桌腿。
可以根据需要调整尺寸和比例，以适应不同的用餐场景。

注意：这个代码不适用于生成其他类型的桌子，如书桌、咖啡桌或办公桌等。

## 准备工作
在生成新模型之前，应清空场景中的所有现有对象。这可以通过以下Blender命令实现：
```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

## 基本结构
一个基础的餐桌由以下部分组成:
- 1个桌板 (生成时，可以标注为 `table_top`，或其他的由你选择的名字)
- 4条桌腿 (生成时，可以分别别标注为 `leg1`, `leg2`, `leg3`, `leg4`，或其他的由你选择的名字)

注意：各个部件应保持独立，不需要合并成一个整体模型。

## 尺寸参考
以下是常见餐桌的尺寸参考:

### 桌板
- 长度: 120-180 cm (1.2-1.8 m in Blender)
- 宽度: 75-90 cm (0.75-0.9 m in Blender)
- 厚度: 2-4 cm (0.02-0.04 m in Blender)

### 桌腿
- 高度: 70-75 cm (0.7-0.75 m in Blender)
- 宽度: 5-8 cm (0.05-0.08 m in Blender)
- 厚度: 5-8 cm (0.05-0.08 m in Blender)

注意: Blender使用米作为默认单位,所以在创建模型时,需要将厘米转换为米。例如,180 cm 在 Blender 中应表示为 1.8 m。

## 生成步骤
1. 清空场景中的所有现有对象
4. 创建桌板 (`table_top`)
5. 将桌板添加到主集合 "Dining Table"
6. 创建四条桌腿 (`leg1`, `leg2`, `leg3`, `leg4`)
7. 将每条桌腿添加到 "Legs" 子集合
8. 将桌腿放置在桌板的四个角落
9. 调整桌腿位置，确保与桌板边缘对齐
10. 从场景集合中移除所有对象，确保它们只存在于自定义集合中
11. 更新场景视图

## 注意事项
- 确保所有部件都有适当的标注
- 桌腿应垂直于桌板
- 桌腿应生成于桌板的下面
- 考虑添加细节，如圆角或简单的纹理
- 可以根据需要调整尺寸，但要保持合理的比例
- 生成的模型应尽可能位于场景的中心点附近 (0, 0, 0)
- 保持各个部件独立，不要合并成一个整体模型
- 在脚本结束时更新场景视图，以确保所有更改都被正确应用
- 考虑为不同类型的部件（如桌面、桌腿）创建单独的函数，以提高代码的可重用性和可读性

## Blender操作提示
- 使用 `bpy.ops.object.select_all(action='SELECT')` 和 `bpy.ops.object.delete()` 清空场景
- 使用 `bpy.ops.mesh.primitive_cube_add()` 创建基本形状
- 使用 `bpy.ops.transform.resize()` 调整大小
- 使用 `bpy.ops.transform.translate()` 移动物体
- 使用 `obj.location = (0, 0, 0)` 将物体移动到中心点
- 使用 `obj.name = "部件名"` 为物体命名
- 使用 `bpy.context.view_layer.objects.active = object` 设置活动对象
- 使用 `bpy.context.active_object` 获取当前活动对象
- 使用 `bpy.context.view_layer.update()` 更新场景视图
- 使用 `bpy.ops.object.select_all(action='DESELECT')` 取消选择所有对象
- 使用 `object.select_set(True)` 选择特定对象

## 示例代码

```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建桌板
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.scale = (1.5, 0.9, 0.03)  # 调整尺寸：长1.5m，宽0.9m，厚0.03m
tabletop.name = "table_top"

# 创建桌腿
def create_leg(name, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    leg = bpy.context.active_object
    leg.scale = (0.05, 0.05, 0.75)  # 调整尺寸：宽0.05m，厚0.05m，高0.75m
    leg.name = name
    return leg

# 创建四条桌腿
leg1 = create_leg("leg1", (0.7, 0.4, 0.375))
leg2 = create_leg("leg2", (-0.7, 0.4, 0.375))
leg3 = create_leg("leg3", (0.7, -0.4, 0.375))
leg4 = create_leg("leg4", (-0.7, -0.4, 0.375))

# 更新场景
bpy.context.view_layer.update()
```
## 高级生成技巧：2D到3D

除了使用基本的立方体并调整其尺寸外，还可以使用更高级的技巧来创建复杂的形状，如六边形桌面。这种方法首先创建一个2D形状，然后将其挤出成3D对象。以下是创建六边形桌面的步骤：

1. 创建一个圆形
2. 将圆形转换为六边形
3. 挤出六边形以创建厚度

### 示例代码：创建六边形桌面

```python
import bpy
import bmesh
import math

def create_hexagonal_table_top(radius=1.0, thickness=0.03):
    # 创建一个新的网格
    mesh = bpy.data.meshes.new(name="HexagonalTableTop")
    obj = bpy.data.objects.new("table_top", mesh)

    # 将对象链接到场景
    bpy.context.collection.objects.link(obj)

    # 创建一个新的 BMesh
    bm = bmesh.new()

    # 添加一个圆形
    bmesh.ops.create_circle(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=6,
        radius=radius
    )

    # 挤出面以创建厚度
    bmesh.ops.extrude_face_region(bm, geom=bm.faces)
    bmesh.ops.translate(bm, vec=(0, 0, thickness), verts=bm.verts[-6:])

    # 将 BMesh 数据更新到网格
    bm.to_mesh(mesh)
    bm.free()

    # 更新网格
    mesh.update()

    return obj

# 使用函数创建六边形桌面
hexagonal_table_top = create_hexagonal_table_top(radius=0.75, thickness=0.03)

# 将桌面移动到适当的位置
hexagonal_table_top.location = (0, 0, 0.75)

# 更新场景
bpy.context.view_layer.update()
```

这个示例展示了如何创建一个六边形的桌面。你可以通过调整 `radius` 参数来改变桌面的大小，通过 `thickness` 参数来改变桌面的厚度。

这种方法的优点是：
1. 可以创建更复杂的形状，不限于简单的立方体。
2. 提供了更多的控制，可以精确地定义形状的每个方面。
3. 可以轻松地创建具有特定边数的多边形形状。

注意事项：
- 这种方法需要更多的几何知识和编程技巧。
- 对于简单的形状，使用基本的立方体可能更快、更简单。
- 在使用这种方法时，确保正确处理了所有的几何细节，如面的法线方向等。

注意该代码仅为示例使用，实际的物品名称可能有所变化，请根据物品名称进行适当的改动，实际的餐桌生成需要最大程度的参考用户提供的要求


