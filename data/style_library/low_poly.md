# 低多边形（Low Poly）风格生成指南

低多边形风格是一种以使用较少的多边形来创建3D模型的技术，通常用于创建简化但富有艺术感的3D图形。这种风格在游戏开发、动画和图形设计中广泛使用。

## 特征

1. 几何简化：使用较少的多边形来表示物体。
2. 平面着色：通常使用平面着色而非平滑着色。
3. 锐利边缘：物体之间的边缘通常保持锐利。
4. 抽象表现：细节被简化，强调整体形状和轮廓。
5. 颜色使用：常使用简单的颜色方案，有时会使用渐变。

## 核心技术

### 1. 几何简化

```python
def simplify_geometry(obj, target_faces):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.decimate(ratio=target_faces / len(obj.data.polygons))
    bpy.ops.object.mode_set(mode='OBJECT')
```

### 2. 添加随机变形

```python
def add_random_displacement(obj, strength=0.1):
    for v in obj.data.vertices:
        v.co += Vector((random.uniform(-strength, strength),
                        random.uniform(-strength, strength),
                        random.uniform(-strength, strength)))
```

### 3. 设置平面着色

```python
def set_flat_shading(obj):
    for face in obj.data.polygons:
        face.use_smooth = False
```

### 4. 创建低多边形材质

```python
def create_low_poly_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_principled.inputs['Base Color'].default_value = color
    node_principled.inputs['Roughness'].default_value = 0.8
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])
    return mat
```

## 应用低多边形风格

```python
def apply_low_poly_style(obj, target_faces=100, displace_strength=0.05, color=(0.8, 0.4, 0.2, 1)):
    simplify_geometry(obj, target_faces)
    add_random_displacement(obj, displace_strength)
    set_flat_shading(obj)
    mat = create_low_poly_material(f"{obj.name}_material", color)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
```

## 使用说明

1. 将上述函数复制到你的Blender Python脚本中。
2. 选择要应用低多边形风格的对象。
3. 调用 `apply_low_poly_style` 函数，传入选中的对象和所需的参数。

示例：
```python
selected_obj = bpy.context.active_object
apply_low_poly_style(selected_obj, target_faces=200, displace_strength=0.03, color=(0.2, 0.8, 0.4, 1))
```

## 参数说明

- `obj`: 要应用低多边形风格的Blender对象。
- `target_faces`: 简化后的目标面数。
- `displace_strength`: 随机位移的强度。
- `color`: 材质的基础颜色。

## 注意事项

1. 几何简化可能会显著改变模型的形状，特别是对于复杂模型。
2. 随机位移可能会导致模型表面不规则，这通常是低多边形风格所需要的效果。
3. 平面着色会使模型看起来更加"硬朗"，这是低多边形风格的典型特征。
4. 材质的选择对最终效果有重要影响，可以尝试不同的颜色和材质设置。

## 优化建议

1. 对于不同类型的模型，可能需要调整简化和位移参数以获得最佳效果。
2. 考虑为不同部分的模型使用不同的颜色，以增加视觉趣味。
3. 可以尝试添加简单的纹理或渐变来增强低多边形效果。
4. 对于某些模型，可能需要手动调整顶点位置以获得理想的形状