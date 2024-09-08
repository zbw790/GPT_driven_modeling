# 办公桌与学习桌生成指南
这段代码用于生成办公桌、书桌或学习桌类型的桌子。这类桌子的主要特征包括:

1. 结构相对复杂:通常包括桌面、桌腿、抽屉单元和/或搁板
2. 桌面尺寸适中:适合个人工作或学习使用
3. 桌面形状:通常为长方形,可能有圆角设计
4. 功能性强:可能包含抽屉、键盘托盘、线缆管理孔等功能性元素
5. 桌腿设计:可能是传统的四条腿,也可能是L型支架或其他现代设计
7. 用途:主要用于办公、学习、写作或其他需要集中注意力的任务

这个生成器创建的是一个基础版本的办公桌/书桌,包含桌面、抽屉单元和桌腿。
可以根据需要调整尺寸、比例和功能元素,以适应不同的工作或学习环境。

注意:这个代码不适用于生成其他类型的桌子,如餐桌、咖啡桌或会议桌等。

## 准备工作

在生成新模型之前,应清空场景中的所有现有对象。这可以通过以下Blender命令实现:

```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

## 基本结构

一个基础的办公桌/学习桌由以下部分组成:
- 1个桌面 (生成时,可以标注为 `table_top`)
- 2条桌腿 (生成时,可以分别标注为 `leg1`, `leg2`)
- 1个柜体 (生成时,可以标注为 `cabinet_shell`)
- 3个抽屉 (生成时,可以分别标注为 `drawer_0`, `drawer_1`, `drawer_2`)

注意:各个部件应保持独立,不需要合并成一个整体模型。

## 尺寸参考

以下是常见办公桌/学习桌的尺寸参考:

### 桌面
- 长度: 120-180 cm (1.2-1.8 m in Blender)
- 宽度: 60-90 cm (0.6-0.9 m in Blender)
- 厚度: 2-3 cm (0.02-0.03 m in Blender)

### 桌腿
- 高度: 70-75 cm (0.7-0.75 m in Blender)
- 宽度: 5 cm (0.05 m in Blender)
- 厚度: 5 cm (0.05 m in Blender)

### 柜体
- 长度: 36 cm (0.36 m in Blender)
- 宽度: 与桌面宽度相同
- 高度: 与桌腿高度相同

### 抽屉
- 长度: 略小于柜体内部长度
- 宽度: 略小于柜体内部宽度
- 高度: (柜体内部高度 - 间隙) / 抽屉数量

注意: Blender使用米作为默认单位,所以在创建模型时,需要将厘米转换为米。

## 生成步骤

1. 清空场景中的所有现有对象
2. 创建桌面 (`table_top`)
3. 创建两条桌腿 (`leg1`, `leg2`)
4. 创建柜体外壳 (`cabinet_shell`)
5. 创建三个抽屉 (`drawer_0`, `drawer_1`, `drawer_2`)
6. 调整各部件的位置,确保它们正确对齐
7. 更新场景视图

## 注意事项

- 确保所有部件都有适当的标注
- 桌腿应垂直于桌面
- 柜体应紧贴桌面底部
- 抽屉应均匀分布在柜体内
- 考虑添加细节,如圆角或简单的纹理
- 可以根据需要调整尺寸,但要保持合理的比例
- 生成的模型应尽可能位于场景的中心点附近 (0, 0, 0)
- 保持各个部件独立,不要合并成一个整体模型

## Blender操作提示

- 使用 `bpy.ops.mesh.primitive_cube_add()` 创建基本形状
- 使用 `bpy.ops.transform.resize()` 调整大小
- 使用 `bpy.ops.transform.translate()` 移动物体
- 使用 `obj.location = (x, y, z)` 精确定位物体
- 使用 `obj.scale = (x, y, z)` 精确缩放物体
- 使用 `bpy.ops.object.modifier_add(type='BOOLEAN')` 添加布尔修改器
- 使用 `bpy.ops.object.modifier_apply()` 应用修改器

## 示例代码
```python
import bpy
import bmesh

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 删除所有集合（除了场景的主集合）
for collection in bpy.data.collections:
    bpy.data.collections.remove(collection)

# 创建桌面
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75))
tabletop = bpy.context.active_object
tabletop.scale = (1.5, 0.9, 0.03)
tabletop.name = "table_top"

# 创建桌腿
def create_leg(name, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    leg = bpy.context.active_object
    leg.scale = (0.05, 0.05, 0.75)
    leg.name = name
    return leg

# 创建两条桌腿
leg1 = create_leg("leg1", (0.7, 0.4, 0.375))
leg2 = create_leg("leg2", (0.7, -0.4, 0.375))

# 设置柜体厚度（单位：米）
cabinet_thickness = 0.02

# 创建柜子外壳
def create_cabinet_shell(length, width, height, thickness):
    location = (-length/2, 0, height/2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cabinet = bpy.context.active_object
    cabinet.scale = (length, width, height)
    cabinet.name = "cabinet_shell"

    inner_cube = create_cabinet_inner_cube(length, width, height, thickness, location)

    # 执行布尔差运算
    boolean_difference(cabinet, inner_cube)
    
    return cabinet

# 创建用于挖空的内部立方体
def create_cabinet_inner_cube(length, width, height, thickness, cabinet_location):
    inner_length = length - 2 * thickness
    inner_width = width - thickness
    inner_height = height - 2 * thickness
    
    inner_x = cabinet_location[0]
    inner_y = cabinet_location[1] - (thickness/2 + 0.001)
    inner_z = cabinet_location[2]
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(inner_x, inner_y, inner_z))
    inner_cube = bpy.context.active_object
    inner_cube.scale = (inner_length, inner_width, inner_height)
    inner_cube.name = "cabinet_inner_cube"
    return inner_cube

# 执行布尔差运算
def boolean_difference(obj1, obj2):
    bpy.ops.object.select_all(action='DESELECT')
    obj1.select_set(True)
    bpy.context.view_layer.objects.active = obj1
    obj2.select_set(True)
    bpy.ops.object.boolean_difference()

# 创建抽屉
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

# 主函数
def create_cabinet_with_drawers():
    # 获取桌面和桌腿的尺寸
    tabletop = bpy.data.objects["table_top"]
    leg = bpy.data.objects["leg1"]
    
    cabinet_length = 0.36  # 自定义长度
    cabinet_width = tabletop.scale[1] # 与桌面宽度相同
    cabinet_height = leg.scale[2] * 2 # 与桌腿高度相同
    
    # 创建柜子外壳
    cabinet_shell = create_cabinet_shell(cabinet_length, cabinet_width, cabinet_height, cabinet_thickness)
    
    # 抽屉参数
    drawer_count = 3
    gap = 0.005
    drawer_thickness = 0.01

    inner_height = cabinet_height - 2 * cabinet_thickness
    drawer_height = (inner_height - ((drawer_count + 1) * gap)) / drawer_count
    drawer_length = cabinet_length - 2 * cabinet_thickness - 2 * gap
    drawer_width = cabinet_width - cabinet_thickness - 2 * gap

    # 创建抽屉
    for i in range(drawer_count):
        drawer_z = (i + 1) * gap + i * drawer_height + drawer_height / 2 + cabinet_thickness
        drawer_location = (-cabinet_length/2, -cabinet_thickness/2, drawer_z)
        create_drawer(drawer_length, drawer_width, drawer_height, drawer_thickness, drawer_location)

# 调用主函数
create_cabinet_with_drawers()

# 更新场景
bpy.context.view_layer.update()
```