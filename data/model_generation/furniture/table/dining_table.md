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

# 删除所有集合（除了场景的主集合）
for collection in bpy.data.collections:
    bpy.data.collections.remove(collection)

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
## 生成多边形的桌子

```python
import bpy
import bmesh
import math

def create_2d_pentagon(name, side_length, z_offset):
    """
    创建一个2D五边形
    
    参数:
    name (str): 对象的名称
    side_length (float): 五边形的边长
    z_offset (float): 对象在z轴上的偏移量
    
    返回:
    bpy.types.Object: 创建的2D五边形对象
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    
    # 创建五边形底面
    bmesh.ops.create_circle(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=5,
        radius=side_length/(2*math.sin(math.pi/5))
    )
    
    bm.to_mesh(mesh)
    bm.free()
    obj.location = (0, 0, z_offset)
    return obj

def extrude_2d_shape(obj, thickness):
    """
    将2D形状挤出为3D对象
    
    参数:
    obj (bpy.types.Object): 要挤出的2D对象
    thickness (float): 挤出的厚度
    """
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    bm.faces.ensure_lookup_table()
    top_face = bm.faces[0]
    
    ret = bmesh.ops.extrude_face_region(bm, geom=[top_face])
    extruded_geom = ret['geom']
    
    extruded_verts = [v for v in extruded_geom if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, thickness), verts=extruded_verts)
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

def create_cylinder(name, radius, height, z_offset):
    """
    创建一个圆柱体
    
    参数:
    name (str): 对象的名称
    radius (float): 圆柱体的半径
    height (float): 圆柱体的高度
    z_offset (float): 对象在z轴上的偏移量
    
    返回:
    bpy.types.Object: 创建的圆柱体对象
    """
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=height,
        location=(0, 0, z_offset + height/2)
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建2D五边形（桌面）
table_top_2d = create_2d_pentagon("table_top", 0.8, 0.72)

# 将2D五边形挤出为3D对象
extrude_2d_shape(table_top_2d, 0.03)

# 创建中央支撑柱
central_support = create_cylinder("central_support", 0.1, 0.72, 0)

# 创建2D五边形（底座）
base_2d = create_2d_pentagon("base", 0.5, 0)

# 将底座挤出为3D对象
extrude_2d_shape(base_2d, 0.02)

# 更新场景
bpy.context.view_layer.update()
```

## 使用说明

1. 将此脚本复制到Blender的文本编辑器中。
2. 运行脚本以创建一个五边形桌面、圆柱形支撑柱和五边形底座。
3. 可以通过修改函数参数来调整桌面和底座的大小、厚度，以及支撑柱的尺寸。

## 注意事项

- 运行脚本前，请确保已保存当前场景，因为脚本会清空现有场景中的所有对象。
- 这个脚本创建的是一个简单的桌子模型。根据需要，您可能需要添加更多细节或组件。
- `extrude_2d_shape` 函数可以用于任何2D形状，不仅限于五边形。

## 扩展思路

- 可以修改 `create_2d_pentagon` 函数以创建其他多边形，如六边形或八边形。
- 可以添加材质和纹理来增强模型的视觉效果。
- 可以创建更复杂的桌子结构，如添加抽屉或装饰性元素。


以下为临时代码储存

import bpy
import bmesh
import random
import math

def create_low_poly_table_top(width=1.5, depth=0.9, height=0.05):
    mesh = bpy.data.meshes.new(name="Table Top Mesh")
    table_top = bpy.data.objects.new("Low Poly Table Top", mesh)
    
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(width, depth, height), verts=bm.verts)
    
    # 确定长边和短边
    long_side = max(width, depth)
    short_side = min(width, depth)
    
    # 对长边进行更多的细分
    long_cuts = 6  # 长边的细分次数
    short_cuts = 2  # 短边的细分次数
    
    if width > depth:
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.verts[0].co.x != e.verts[1].co.x], cuts=long_cuts)
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.verts[0].co.y != e.verts[1].co.y], cuts=short_cuts)
    else:
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.verts[0].co.y != e.verts[1].co.y], cuts=long_cuts)
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.verts[0].co.x != e.verts[1].co.x], cuts=short_cuts)

    # 获取顶面的顶点
    top_verts = [v for v in bm.verts if v.co.z > 0]

    # 对顶面顶点进行排序，以便我们可以按行处理它们
    sorted_verts = sorted(top_verts, key=lambda v: (v.co.y, v.co.x))

    # 计算每行的顶点数
    verts_per_row = long_cuts + 2

    # 处理每一行的顶点
    for i in range(0, len(sorted_verts), verts_per_row):
        row = sorted_verts[i:i+verts_per_row]
        prev_offset_x = 0
        prev_offset_y = 0
        for j, v in enumerate(row):
            # 根据是长边还是短边来决定波动的大小
            if width > depth:
                max_offset = 0.03 if j > 0 and j < len(row) - 1 else 0.01
            else:
                max_offset = 0.03 if i > 0 and i < len(sorted_verts) - verts_per_row else 0.01
            
            # 基于前一个点的偏移来计算新的偏移
            offset_x = prev_offset_x + random.uniform(-max_offset, max_offset)
            offset_y = prev_offset_y + random.uniform(-max_offset, max_offset)
            offset_z = random.uniform(-0.01, 0.01)
            
            v.co.x += offset_x
            v.co.y += offset_y
            v.co.z += offset_z
            
            prev_offset_x = offset_x
            prev_offset_y = offset_y

    # 添加一些控制的切割来模拟木板
    cuts = [
        (0, 1, 0),  # 垂直切割
        (1, 0, 0),  # 水平切割
        (1, 1, 0),  # 对角线切割
    ]

    for cut in cuts:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:]+bm.edges[:]+bm.faces[:], 
                               plane_co=(0, 0, height/2), 
                               plane_no=cut)

    # 添加一些轻微的随机切割
    for _ in range(3):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:]+bm.edges[:]+bm.faces[:], 
                               plane_co=(random.uniform(-width/2, width/2), 
                                         random.uniform(-depth/2, depth/2), 
                                         height/2), 
                               plane_no=(random.uniform(-1, 1), 
                                         random.uniform(-1, 1), 
                                         0))

    bm.to_mesh(mesh)
    bm.free()
    
    table_top.location = (0, 0, 0.75)
    return table_top

def create_table_leg(radius=0.05, height=0.75, location=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name="Table Leg Mesh")
    leg = bpy.data.objects.new("Table Leg", mesh)
    
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6, radius1=radius, radius2=radius, depth=height)
    
    # 添加一些随机变形
    for v in bm.verts:
        v.co.x += random.uniform(-0.01, 0.01)
        v.co.y += random.uniform(-0.01, 0.01)
        v.co.z += random.uniform(-0.01, 0.01)
    
    bm.to_mesh(mesh)
    bm.free()
    
    leg.location = location
    return leg

def create_low_poly_table():
    # 删除所有现有对象
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)

    # 删除所有集合（除了场景的主集合）
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection)

    table_collection = bpy.data.collections.new("Low Poly Table")
    bpy.context.scene.collection.children.link(table_collection)
    
    # 创建低多边形桌面
    table_width, table_depth, table_height = 1.5, 0.9, 0.05
    table_top = create_low_poly_table_top(table_width, table_depth, table_height)
    table_collection.objects.link(table_top)

    # 创建桌腿
    leg_height = 0.75
    leg_radius = 0.05
    leg_positions = [
        (0.7, 0.4, 0.375),
        (-0.7, 0.4, 0.375),
        (0.7, -0.4, 0.375),
        (-0.7, -0.4, 0.375)
    ]
    
    for i, pos in enumerate(leg_positions):
        leg = create_table_leg(leg_radius, leg_height, pos)
        leg.name = f"leg{i+1}"
        table_collection.objects.link(leg)
    
    return table_collection

# 创建低多边形桌子
create_low_poly_table()

# 更新视图
bpy.context.view_layer.update()

