# 书架生成指南

这段代码专门用于生成标准书架:


## 准备工作

在生成新模型之前,应清空场景中的所有现有对象。这可以通过以下Blender命令实现:

```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

## 基本结构

一个基础的书架由以下部分组成:
- 1个框架 (生成时,标注为 `Frame`)
- 2个侧板 (生成时,分别标注为 `SidePanelLeft`, `SidePanelRight`)
- 1个背板 (生成时,标注为 `BackPanel`)
- 1个顶板 (生成时,标注为 `TopPanel`)
- 1个底板 (生成时,标注为 `BottomPanel`)
- 多个搁板 (生成时,标注为 `Shelf_1`, `Shelf_2`, 等)

## 尺寸参考

以下是常见书架的尺寸参考:

- 宽度: 80-120 cm (0.8-1.2 m in Blender)
- 深度: 30-40 cm (0.3-0.4 m in Blender)
- 高度: 180-240 cm (1.8-2.4 m in Blender)
- 板材厚度: 1.5-2.5 cm (0.015-0.025 m in Blender)

注意: Blender使用米作为默认单位,所以在创建模型时,需要将厘米转换为米。

## 生成步骤

1. 清空场景中的所有现有对象
2. 创建框架 (`Frame`)
3. 创建左右侧板 (`SidePanelLeft`, `SidePanelRight`)
4. 创建背板 (`BackPanel`)
5. 创建顶板和底板 (`TopPanel`, `BottomPanel`)
6. 创建多个搁板 (`Shelf_1`, `Shelf_2`, 等)
7. 创建一个新的集合 "Bookshelf" 并将所有部件添加到这个集合中
8. 从场景集合中移除所有对象,确保它们只存在于自定义集合中
9. 更新场景视图

## 注意事项

- 确保所有部件都有适当的标注
- 侧板和背板应紧贴框架内侧
- 搁板应均匀分布在框架内
- 考虑添加细节,如圆角或简单的纹理
- 可以根据需要调整尺寸,但要保持合理的比例
- 生成的模型应尽可能位于场景的中心点附近 (0, 0, 0)
- 保持各个部件独立,不要合并成一个整体模型

## Blender操作提示

- 使用 `bpy.ops.mesh.primitive_cube_add()` 创建基本形状
- 使用 `obj.scale = (x, y, z)` 调整大小
- 使用 `obj.location = (x, y, z)` 定位物体
- 使用 `bpy.data.collections.new()` 创建新集合
- 使用 `collection.objects.link(obj)` 将对象添加到集合
- 使用 `bpy.context.scene.collection.children.link(collection)` 将集合添加到场景
- 使用 `bpy.context.scene.collection.objects.unlink(obj)` 从场景集合中移除对象

## 示例代码

```python
import bpy

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

def create_cuboid(name, dimensions, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = dimensions
    return obj

shelf_width = 1
shelf_depth = 0.3
shelf_height = 1.8
shelf_thickness = 0.02

side_panel_left = create_cuboid("SidePanelLeft", (shelf_thickness, shelf_depth, shelf_height), (-shelf_width/2 + shelf_thickness/2, 0, shelf_height/2))
side_panel_right = create_cuboid("SidePanelRight", (shelf_thickness, shelf_depth, shelf_height), (shelf_width/2 - shelf_thickness/2, 0, shelf_height/2))

back_panel = create_cuboid("BackPanel", (shelf_width, shelf_thickness, shelf_height), (0, -shelf_depth/2 + shelf_thickness/2, shelf_height/2))

top_panel = create_cuboid("TopPanel", (shelf_width, shelf_depth, shelf_thickness), (0, 0, shelf_height - shelf_thickness/2))
bottom_panel = create_cuboid("BottomPanel", (shelf_width, shelf_depth, shelf_thickness), (0, 0, shelf_thickness/2))

shelf_count = 5
shelf_spacing = (shelf_height - 2*shelf_thickness) / (shelf_count + 1)

for i in range(shelf_count):
    shelf_z = shelf_thickness + (i + 1) * shelf_spacing
    shelf = create_cuboid(f"Shelf_{i+1}", (shelf_width - 2*shelf_thickness, shelf_depth - shelf_thickness, shelf_thickness), (0, shelf_thickness/2, shelf_z))

bookshelf_collection = bpy.data.collections.new("Bookshelf")
bpy.context.scene.collection.children.link(bookshelf_collection)

for obj in bpy.data.objects:
    bpy.context.scene.collection.objects.unlink(obj)
    bookshelf_collection.objects.link(obj)

bpy.context.view_layer.update()
```

## 更加美观的书架
```python
import bpy
import bmesh

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建书架集合
collection = bpy.data.collections.new("Bookshelf")
bpy.context.scene.collection.children.link(collection)

# 创建侧板
def create_side_panel(x_pos):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, 0, 90))
    side_panel = bpy.context.active_object
    side_panel.scale = (1.5, 30, 180)
    side_panel.name = f"Side_Panel_{x_pos}"
    collection.objects.link(side_panel)
    bpy.context.collection.objects.unlink(side_panel)

create_side_panel(-40)
create_side_panel(40)

# 创建搁板
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * 40 + 20))
    shelf = bpy.context.active_object
    shelf.scale = (80, 30, 2)
    shelf.name = f"Shelf_{i}"
    collection.objects.link(shelf)
    bpy.context.collection.objects.unlink(shelf)

# 创建顶板
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 181.5))
top_panel = bpy.context.active_object
top_panel.scale = (82, 32, 3)
top_panel.name = "Top_Panel"
collection.objects.link(top_panel)
bpy.context.collection.objects.unlink(top_panel)

# 创建底板
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.5))
bottom_panel = bpy.context.active_object
bottom_panel.scale = (82, 32, 3)
bottom_panel.name = "Bottom_Panel"
collection.objects.link(bottom_panel)
bpy.context.collection.objects.unlink(bottom_panel)

# 创建抽屉
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 10.5))
drawer = bpy.context.active_object
drawer.scale = (76, 28, 15)
drawer.name = "Drawer"
collection.objects.link(drawer)
bpy.context.collection.objects.unlink(drawer)

# 设置材质
material = bpy.data.materials.new(name="Wood")
material.use_nodes = True
nodes = material.node_tree.nodes
nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.4, 0.2, 1)

for obj in collection.objects:
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

bpy.context.view_layer.update()
```
## 使用说明

1. 将此脚本复制到Blender的文本编辑器中。
2. 运行脚本以创建一个基础的书架模型。
3. 可以通过修改变量 `shelf_width`, `shelf_depth`, `shelf_height`, `shelf_thickness` 和 `shelf_count` 来调整书架的尺寸和搁板数量。

## 扩展思路

- 可以添加更多细节,如装饰性边框或背板图案。
- 可以创建不同形状的书架,如角落书架或梯形书架。
- 可以添加材质和纹理来增强模型的视觉效果。
- 可以添加可选的门板或抽屉来创建更复杂的储物单元。