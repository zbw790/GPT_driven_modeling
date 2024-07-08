# 餐桌生成指南

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
2. 创建主集合 "Dining Table"
3. 创建子集合 "Legs"，并将其链接到主集合
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
- 正确管理集合，确保部件被添加到适当的集合中
- 主集合应命名为物品名称（例如 "Dining Table"）
- 创建子集合来组织相似的部件（例如 "Legs" 子集合）
- 确保所有对象都从场景集合中移除，只存在于自定义集合中
- 在创建新对象后，始终检查并更新其所属的集合
- 在脚本结束时更新场景视图，以确保所有更改都被正确应用
- 考虑为不同类型的部件（如桌面、桌腿）创建单独的函数，以提高代码的可重用性和可读性
- 在添加或移除对象到/从集合时，始终检查对象是否已经在该集合中，以避免错误

## Blender操作提示
- 使用 `bpy.ops.object.select_all(action='SELECT')` 和 `bpy.ops.object.delete()` 清空场景
- 使用 `bpy.ops.mesh.primitive_cube_add()` 创建基本形状
- 使用 `bpy.ops.transform.resize()` 调整大小
- 使用 `bpy.ops.transform.translate()` 移动物体
- 使用 `obj.location = (0, 0, 0)` 将物体移动到中心点
- 使用 `obj.name = "部件名"` 为物体命名
- 使用 `bpy.data.collections.new("集合名")` 创建新集合
- 使用 `bpy.context.scene.collection.children.link(collection)` 将集合链接到场景
- 使用 `collection.objects.link(object)` 将对象添加到集合
- 使用 `bpy.context.scene.collection.objects.unlink(object)` 从场景集合中移除对象
- 使用 `bpy.context.view_layer.objects.active = object` 设置活动对象
- 使用 `bpy.context.active_object` 获取当前活动对象
- 使用 `if object.name in collection.objects:` 检查对象是否在集合中
- 使用 `parent_collection.children.link(child_collection)` 创建集合层级
- 使用 `bpy.context.view_layer.update()` 更新场景视图
- 使用 `bpy.ops.object.select_all(action='DESELECT')` 取消选择所有对象
- 使用 `object.select_set(True)` 选择特定对象
- 使用 `bpy.context.collection` 获取当前活动集合
- 使用 `for obj in collection.objects:` 遍历集合中的所有对象
- 使用 `bpy.data.objects.remove(object, do_unlink=True)` 完全删除对象（包括从所有集合中移除）

## 示例代码

```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 删除所有多余的集合
for collection in bpy.data.collections:
    bpy.data.collections.remove(collection)
    
# 创建主集合
main_collection = bpy.data.collections.new("Dining Table")
bpy.context.scene.collection.children.link(main_collection)

# 创建子集合
legs_collection = bpy.data.collections.new("Legs")
main_collection.children.link(legs_collection)

# 设置主集合为活动集合
layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

# 创建桌板
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.scale = (1.5, 0.9, 0.03)
tabletop.name = "table_top"

# 确保桌板只在主集合中
for coll in tabletop.users_collection:
    if coll != main_collection:
        coll.objects.unlink(tabletop)

# 创建桌腿
def create_leg(name, location):
    # 临时将活动集合设置为legs_collection
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[main_collection.name].children[legs_collection.name]
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    leg = bpy.context.active_object
    leg.scale = (0.05, 0.05, 0.75)
    leg.name = name
    
    # 确保桌腿只在legs集合中
    for coll in leg.users_collection:
        if coll != legs_collection:
            coll.objects.unlink(leg)
    
    # 恢复主集合为活动集合
    bpy.context.view_layer.active_layer_collection = layer_collection
    
    return leg

# 创建四条桌腿
leg1 = create_leg("leg1", (0.7, 0.4, 0.375))
leg2 = create_leg("leg2", (-0.7, 0.4, 0.375))
leg3 = create_leg("leg3", (0.7, -0.4, 0.375))
leg4 = create_leg("leg4", (-0.7, -0.4, 0.375))

# 更新场景
bpy.context.view_layer.update()
```
注意该代码仅为示例使用，实际的物品名称可能有所变化，请根据物品名称进行适当的改动，实际的餐桌生成需要最大程度的参考用户提供的要求


