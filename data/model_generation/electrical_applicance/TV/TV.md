# 电视机生成指南

这段代码专门用于生成标准低多边形风格的电视机模型:

## 准备工作

在生成新模型之前,应清空场景中的所有现有对象和集合。这可以通过以下Blender命令实现:

```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

for collection in bpy.data.collections:
    if collection != bpy.context.scene.collection:
        bpy.data.collections.remove(collection)
```

## 基本结构

一个基础的电视机模型由以下部分组成:
- 底座 (生成时,标注为 `Stand`)
- 连接器 (生成时,标注为 `Connector`)
- 主体 (生成时,标注为 `Body`)
- 屏幕 (生成时,标注为 `Screen`)

## 尺寸参考

以下是电视机模型的尺寸参考:

- 底座: 宽度 6, 深度 2, 高度 0.2
- 连接器: 宽度 0.5, 深度 0.5, 高度 0.3
- 主体: 宽度 12, 深度 0.5, 高度 4
- 屏幕: 宽度 11.8, 深度 0.1, 高度 3.8

注意: Blender使用米作为默认单位,所以这些数值直接对应到Blender中的尺寸。

## 生成步骤

1. 清空场景中的所有现有对象和集合
2. 创建新的 "Television" 集合
3. 创建底座 (`Stand`)
4. 创建连接器 (`Connector`)
5. 创建主体 (`Body`)
6. 创建屏幕 (`Screen`)
7. 将所有部件添加到 "Television" 集合中
8. 从场景集合中移除所有对象,确保它们只存在于自定义集合中
9. 更新场景视图

## 注意事项

- 确保所有部件都有适当的标注
- 各部件应紧密贴合,没有间隙
- 屏幕应略微凸出于主体前方
- 保持各个部件独立,不要合并成一个整体模型
- 生成的模型应位于场景的中心点附近 (0, 0, 0)

## Blender操作提示

- 使用 `bpy.ops.mesh.primitive_cube_add()` 创建基本形状
- 使用 `obj.dimensions = (x, y, z)` 设置对象尺寸
- 使用 `obj.location = (x, y, z)` 定位物体
- 使用 `bpy.data.collections.new()` 创建新集合
- 使用 `collection.objects.link(obj)` 将对象添加到集合
- 使用 `bpy.context.scene.collection.children.link(collection)` 将集合添加到场景
- 使用 `bpy.context.scene.collection.objects.unlink(obj)` 从场景集合中移除对象

## 示例代码

```python
import bpy
import math

# Delete all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Delete all collections (except the main scene collection)
for collection in bpy.data.collections:
    if collection != bpy.context.scene.collection:
        bpy.data.collections.remove(collection)

# Create Television Components
tv_collection = bpy.data.collections.new('Television')
bpy.context.scene.collection.children.link(tv_collection)

def add_to_collection(obj, collection):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)

# Constants for precise calculations
STAND_HEIGHT = 0.2
STAND_WIDTH = 6
STAND_DEPTH = 2
BODY_HEIGHT = 4
BODY_WIDTH = 12
BODY_DEPTH = 0.5
SCREEN_INSET = 0.1
CONNECTOR_HEIGHT = 0.3
CONNECTOR_WIDTH = 0.5
CONNECTOR_DEPTH = 0.5

# Add Stand
bpy.ops.mesh.primitive_cube_add(location=(0, 0, STAND_HEIGHT / 2))
stand = bpy.context.active_object
stand.name = 'Stand'
stand.dimensions = (STAND_WIDTH, STAND_DEPTH, STAND_HEIGHT)
add_to_collection(stand, tv_collection)

# Add Connector
connector_z = STAND_HEIGHT + CONNECTOR_HEIGHT / 2
bpy.ops.mesh.primitive_cube_add(location=(0, 0, connector_z))
connector = bpy.context.active_object
connector.name = 'Connector'
connector.dimensions = (CONNECTOR_WIDTH, CONNECTOR_DEPTH, CONNECTOR_HEIGHT)
add_to_collection(connector, tv_collection)

# Add Body
body_z = STAND_HEIGHT + CONNECTOR_HEIGHT + BODY_HEIGHT / 2
bpy.ops.mesh.primitive_cube_add(location=(0, 0, body_z))
body = bpy.context.active_object
body.name = 'Body'
body.dimensions = (BODY_WIDTH, BODY_DEPTH, BODY_HEIGHT)
add_to_collection(body, tv_collection)

# Add Screen
screen_z = body_z
screen_y = (BODY_DEPTH / 2) + (SCREEN_INSET / 2)
bpy.ops.mesh.primitive_cube_add(location=(0, screen_y, screen_z))
screen = bpy.context.active_object
screen.name = 'Screen'
screen.dimensions = (BODY_WIDTH - 0.2, SCREEN_INSET, BODY_HEIGHT - 0.2)
add_to_collection(screen, tv_collection)

# Run the script to generate the TV
bpy.context.view_layer.update()
```

## 使用说明

1. 将此脚本复制到Blender的文本编辑器中。
2. 运行脚本以创建一个低多边形风格的电视机模型。
3. 可以通过修改常量 `STAND_HEIGHT`, `STAND_WIDTH`, `STAND_DEPTH` 等来调整电视机的尺寸和比例。