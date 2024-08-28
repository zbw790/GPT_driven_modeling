# 家具表面组件生成指南

这段代码用于生成各种家具的表面组件。家具表面是家具的主要功能区域，决定了家具的使用方式和美观度。主要包括：

## 主要特征

1. 形状：可以是长方形、正方形、圆形或多边形
2. 尺寸：可调整长度、宽度和厚度
3. 边缘处理：可以有直边、圆角或斜角
4. 材质：可以模拟木材、金属、玻璃等

## 尺寸参考

- 长度: 0.6-2.0 m
- 宽度: 0.4-1.0 m
- 厚度: 0.015-0.05 m

## 基本生成代码

以下是一个生成简单长方形表面的示例代码：

```python
import bpy
import bmesh

def create_surface(name, length=1.2, width=0.8, thickness=0.03, corner_radius=0.02):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(length, width, thickness), verts=bm.verts)
    
    if corner_radius > 0:
        bmesh.ops.bevel(bm,
                        geom=[v for v in bm.verts if v.is_boundary] + [e for e in bm.edges if e.is_boundary],
                        offset=corner_radius,
                        offset_type='OFFSET',
                        segments=16,
                        profile=0.5)
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    return obj

# 使用示例
surface = create_surface("table_top")
```

## 多边形表面生成

对于多边形表面（如六边形桌面），可以使用以下代码：

```python
import bpy
import bmesh
from mathutils import Vector

def create_polygon_surface(name, sides=6, radius=0.75, thickness=0.03):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    bm = bmesh.new()
    bmesh.ops.create_circle(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=sides,
        radius=radius
    )
    
    # 确保查找表是最新的
    bm.faces.ensure_lookup_table()
    
    # 获取顶面
    top_face = bm.faces[0]
    
    # 挤出整个顶面
    ret = bmesh.ops.extrude_face_region(bm, geom=[top_face])
    extruded_verts = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
    
    # 移动挤出的顶点
    bmesh.ops.translate(bm, vec=Vector((0, 0, thickness)), verts=extruded_verts)
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    return obj

# 使用示例
hexagon_surface = create_polygon_surface("hexagon_table_top", sides=6)
```

## 注意事项

- 根据具体需求调整参数，如尺寸、边数等。
- 生成后可能需要添加材质或进行其他修改以满足特定要求。
- 确保生成的表面组件与其他家具部件协调一致。

