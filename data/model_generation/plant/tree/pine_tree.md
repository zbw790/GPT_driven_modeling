# 低多边形松树生成指南

这段代码专门用于生成低多边形风格的松树模型:

## 准备工作

在生成新模型之前,应清空场景中的所有现有对象。这可以通过以下Blender命令实现:

```python
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

## 基本结构

一个基础的低多边形松树由以下部分组成:
- 1个树干 (生成时,标注为 `Tree Trunk`)
- 多个圆锥体树冠 (生成时,标注为 `Pine Cone 1`, `Pine Cone 2`, 等)

## 尺寸参考

以下是常见低多边形松树的尺寸参考:

- 树干高度: 1.5 m
- 树干半径: 0.1 m
- 基础圆锥体半径: 0.6 m
- 基础圆锥体高度: 0.5 m

注意: Blender使用米作为默认单位。

## 生成步骤

1. 清空场景中的所有现有对象
2. 创建树干 (`Tree Trunk`)
3. 创建多个圆锥体树冠 (`Pine Cone`)
4. 创建一个新的集合 "Low Poly Pine Tree" 并将所有部件添加到这个集合中
5. 从场景集合中移除所有对象,确保它们只存在于自定义集合中
6. 创建并应用材质
7. 更新场景视图

## 注意事项

- 确保所有部件都有适当的标注
- 圆锥体树冠应堆叠在树干顶部
- 使用随机化来增加树木的自然感
- 保持低多边形风格,避免过多的细节
- 生成的模型应位于场景的中心点附近 (0, 0, 0)
- 保持各个部件独立,不要合并成一个整体模型

## Blender操作提示

- 使用 `bpy.ops.mesh.primitive_cylinder_add()` 创建树干
- 使用 `bpy.ops.mesh.primitive_cone_add()` 创建圆锥体树冠
- 使用 `bmesh` 模块进行几何操作
- 使用 `obj.location = (x, y, z)` 定位物体
- 使用 `obj.rotation_euler = (x, y, z)` 旋转物体
- 使用 `bpy.data.collections.new()` 创建新集合
- 使用 `collection.objects.link(obj)` 将对象添加到集合
- 使用 `bpy.context.scene.collection.children.link(collection)` 将集合添加到场景
- 使用 `bpy.context.scene.collection.objects.unlink(obj)` 从场景集合中移除对象

## 材质创建

为树干和树冠创建不同的材质,使用节点系统来实现更复杂的效果:

- 树干材质: 使用噪波纹理创建木纹效果
- 树冠材质: 使用噪波纹理创建针叶的变化效果

## 示例代码

```python
import bpy
import bmesh
import math
import random

def create_tree_trunk(height=1.5, radius=0.1):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, vertices=8)
    trunk = bpy.context.active_object
    trunk.name = "Tree Trunk"
    
    bm = bmesh.new()
    bm.from_mesh(trunk.data)
    for v in bm.verts:
        v.co.x += random.uniform(-0.02, 0.02)
        v.co.y += random.uniform(-0.02, 0.02)
    bm.to_mesh(trunk.data)
    bm.free()
    
    return trunk

def create_pine_cone(radius, height, vertices=8):
    bpy.ops.mesh.primitive_cone_add(radius1=radius, radius2=0, depth=height, vertices=vertices)
    cone = bpy.context.active_object
    
    bm = bmesh.new()
    bm.from_mesh(cone.data)
    
    # Add random displacement to vertices
    for v in bm.verts:
        if v.co.z < height:  # Don't move the top vertex
            v.co.x += random.uniform(-0.1, 0.1) * radius
            v.co.y += random.uniform(-0.1, 0.1) * radius
            v.co.z += random.uniform(-0.05, 0.05) * height
    
    bm.to_mesh(cone.data)
    bm.free()
    
    return cone

def create_pine_tree_crown(num_cones=5, base_radius=0.6, base_height=0.5):
    crown_collection = bpy.data.collections.new("Pine Tree Crown")
    bpy.context.scene.collection.children.link(crown_collection)
    
    total_height = 0
    for i in range(num_cones):
        radius = base_radius * (1 - i/num_cones) * random.uniform(0.8, 1.2)
        height = base_height * (1 - i/(2*num_cones)) * random.uniform(0.8, 1.2)
        
        cone = create_pine_cone(radius, height)
        cone.name = f"Pine Cone {i+1}"
        cone.location = (0, 0, total_height)
        
        crown_collection.objects.link(cone)
        bpy.context.collection.objects.unlink(cone)
        
        total_height += height * 0.7  # Overlap cones slightly
    
    return crown_collection

def create_low_poly_pine_tree():
    # 删除所有现有对象
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    tree_collection = bpy.data.collections.new("Low Poly Pine Tree")
    bpy.context.scene.collection.children.link(tree_collection)
    
    trunk_height = 1.5
    trunk = create_tree_trunk(height=trunk_height)
    crown = create_pine_tree_crown(num_cones=5, base_radius=0.6, base_height=0.5)
    
    for obj in [trunk] + list(crown.objects):
        if obj.name not in tree_collection.objects:
            tree_collection.objects.link(obj)
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)
    
    # 创建材质
    trunk_material = create_trunk_material()
    crown_material = create_crown_material()
    
    # 应用材质
    trunk.data.materials.append(trunk_material)
    for obj in crown.objects:
        obj.data.materials.append(crown_material)
    
    return tree_collection

def create_trunk_material():
    material = bpy.data.materials.new(name="Trunk Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    nodes.clear()
    
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_tex_coord = nodes.new(type='ShaderNodeTexCoord')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_noise = nodes.new(type='ShaderNodeTexNoise')
    node_color_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    
    node_principled.inputs['Roughness'].default_value = 0.7
    node_noise.inputs['Scale'].default_value = 5
    node_noise.inputs['Detail'].default_value = 10
    node_color_ramp.color_ramp.elements[0].color = (0.2, 0.1, 0.05, 1)
    node_color_ramp.color_ramp.elements[1].color = (0.4, 0.2, 0.1, 1)
    
    links.new(node_tex_coord.outputs['Generated'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_noise.inputs['Vector'])
    links.new(node_noise.outputs['Fac'], node_color_ramp.inputs['Fac'])
    links.new(node_color_ramp.outputs['Color'], node_principled.inputs['Base Color'])
    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])
    
    return material

def create_crown_material():
    material = bpy.data.materials.new(name="Crown Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    nodes.clear()
    
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_tex_coord = nodes.new(type='ShaderNodeTexCoord')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_noise = nodes.new(type='ShaderNodeTexNoise')
    node_color_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    
    node_principled.inputs['Roughness'].default_value = 0.5
    node_noise.inputs['Scale'].default_value = 3
    node_noise.inputs['Detail'].default_value = 8
    node_color_ramp.color_ramp.elements[0].color = (0.05, 0.2, 0.05, 1)
    node_color_ramp.color_ramp.elements[1].color = (0.1, 0.4, 0.1, 1)
    
    links.new(node_tex_coord.outputs['Generated'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_noise.inputs['Vector'])
    links.new(node_noise.outputs['Fac'], node_color_ramp.inputs['Fac'])
    links.new(node_color_ramp.outputs['Color'], node_principled.inputs['Base Color'])
    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])
    
    return material

# 创建松树
low_poly_pine_tree = create_low_poly_pine_tree()

# 更新视图
bpy.context.view_layer.update()
```

## 使用说明

1. 将此脚本复制到Blender的文本编辑器中。
2. 运行脚本以创建一个低多边形松树模型。
3. 可以通过修改 `create_low_poly_pine_tree()` 函数中的参数来调整松树的尺寸和形状。

## 自定义

你可以通过调整以下参数来自定义松树的外观:

- 在 `create_tree_trunk()` 中修改 `height` 和 `radius` 来改变树干的大小。
- 在 `create_pine_tree_crown()` 中修改 `num_cones`, `base_radius`, 和 `base_height` 来改变树冠的形状和大小。
- 调整 `create_pine_cone()` 中的随机变形参数来改变每个圆锥体的不规则程度。
- 在材质创建函数中修改颜色和纹理参数来改变树的外观。