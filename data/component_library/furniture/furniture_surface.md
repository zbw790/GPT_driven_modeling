# 家具表面组件生成指南

这段代码用于生成各种家具的表面组件。家具表面是家具的主要功能区域，决定了家具的使用方式和美观度。主要包括：

1. 桌面：用于各种类型的桌子，如办公桌、餐桌、书桌等。可能是平面、弧形或带有特殊设计（如升降功能）。

2. 柜面：应用于各种柜子，如衣柜顶部、橱柜台面、边柜表面等。可能需要考虑防水、耐磨等特性。

3. 架子：用于书架、展示架等。可能是固定的或可调节的。

4. 座面：椅子或凳子的坐垫部分。可能是硬质材料或带有软垫。

5. 床板：支撑床垫的平面。可能是实木板、板条或其他材质。

家具表面的设计考虑因素包括：
- 尺寸：根据家具类型和用途确定适当的长度、宽度和厚度。
- 材质：可以是木材、金属、玻璃、石材等，影响外观、耐用性和功能性。
- 形状：可以是矩形、圆形、不规则形状等，影响美观和实用性。
- 边缘处理：可能有直边、圆角、斜角等不同处理方式，影响安全性和美观。
- 表面处理：可能需要涂漆、上漆、抛光等处理，影响外观和耐用性。
- 功能性设计：可能包含线缆孔、嵌入式插座、可折叠部分等特殊功能。
## 主要特征

1. 形状多样：可以是长方形、正方形、圆形或其他自定义形状
2. 尺寸可调：根据家具类型和用途调整长度、宽度和厚度
3. 边缘处理：可以有直边、圆角或斜角等不同处理方式
4. 材质丰富：可以模拟木材、金属、玻璃等多种材质
5. 功能性：可能包含孔洞（如线缆管理孔）或其他功能性设计

## 尺寸参考

以下是常见家具表面的尺寸参考：

- 长度: 60-200 cm (0.6-2.0 m in Blender)
- 宽度: 40-100 cm (0.4-1.0 m in Blender)
- 厚度: 1.5-5 cm (0.015-0.05 m in Blender)

注意: Blender使用米作为默认单位，所以在创建模型时，需要将厘米转换为米。

## 生成步骤

1. 创建基本形状（通常是一个立方体）
2. 调整表面的尺寸（长度、宽度、厚度）
3. 应用边缘处理（如倒角或圆角）
4. 添加材质或纹理
5. 根据需要添加功能性元素（如线缆孔）
6. 正确命名和标注表面组件

## 示例代码

以下是一个生成简单长方形表面的示例代码：

```python
import bpy
import bmesh

def create_surface(name, length=1.2, width=0.8, thickness=0.03, corner_radius=0.02):
    # 创建网格和物体
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # 链接物体到场景
    bpy.context.collection.objects.link(obj)

    # 创建bmesh
    bm = bmesh.new()

    # 创建立方体
    bmesh.ops.create_cube(bm, size=1)

    # 缩放到所需尺寸
    bmesh.ops.scale(bm, vec=(length, width, thickness), verts=bm.verts)

    # 添加倒角
    bmesh.ops.bevel(bm,
                    geom=[v for v in bm.verts if v.is_boundary] + [e for e in bm.edges if e.is_boundary],
                    offset=corner_radius,
                    offset_type='OFFSET',
                    segments=16,
                    profile=0.5)

    # 更新bmesh
    bm.to_mesh(mesh)
    bm.free()

    # 更新网格
    mesh.update()

    return obj

# 使用示例
surface = create_surface("table_top")