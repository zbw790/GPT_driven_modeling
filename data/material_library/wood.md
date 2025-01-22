# 木材材质 (Wood Material)

木材是一种常用于家具、建筑和装饰的天然材料。它具有独特的纹理、颜色变化和温暖的外观，使其成为许多设计中的首选材料。

## 特征

1. 纹理：木材具有独特的纹理模式，包括年轮、节点和木纹。
2. 颜色：从浅色（如枫木）到深色（如黑胡桃木），颜色范围广泛。
3. 反射特性：通常具有低到中等的反射率，取决于表面处理。
4. 次表面散射：木材具有一定程度的次表面散射，使其看起来更自然。

## 在Blender中创建木材材质

要在Blender中创建逼真的木材材质，我们主要使用Principled BSDF着色器，并结合程序化纹理来模拟木纹。

### 基础木材材质

以下是创建基础木材材质的Python代码：

```python
import bpy

def create_low_poly_wood_material(name="Low Poly Wood"):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # 清除默认节点
    nodes.clear()
    
    # 创建节点
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_tex_coord = nodes.new(type='ShaderNodeTexCoord')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_noise = nodes.new(type='ShaderNodeTexNoise')
    node_color_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    
    # 设置节点参数
    node_principled.inputs['Roughness'].default_value = 0.7
    node_noise.inputs['Scale'].default_value = 5
    node_noise.inputs['Detail'].default_value = 10
    
    # 设置颜色渐变
    node_color_ramp.color_ramp.elements[0].color = (0.2, 0.1, 0.05, 1)
    node_color_ramp.color_ramp.elements[1].color = (0.4, 0.2, 0.1, 1)
    
    # 连接节点
    links.new(node_tex_coord.outputs['Generated'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_noise.inputs['Vector'])
    links.new(node_noise.outputs['Fac'], node_color_ramp.inputs['Fac'])
    links.new(node_color_ramp.outputs['Color'], node_principled.inputs['Base Color'])
    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])
    
    return material
```

### 高级木材材质（带花纹）

以下是创建带有更复杂花纹的木材材质的Python代码：

```python
import bpy

def create_wood_material():
    mat = bpy.data.materials.new(name="Wood_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create nodes
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    texture_coord_node = nodes.new(type='ShaderNodeTexCoord')
    mapping_node = nodes.new(type='ShaderNodeMapping')
    wave_texture_node = nodes.new(type='ShaderNodeTexWave')
    color_ramp_node = nodes.new(type='ShaderNodeValToRGB')

    # Set parameters
    base_color = [139/255, 69/255, 19/255, 1.0]
    principled_node.inputs['Base Color'].default_value = base_color
    principled_node.inputs['Metallic'].default_value = 0.0
    principled_node.inputs['Roughness'].default_value = 0.6

    wave_texture_node.inputs['Scale'].default_value = 5.0
    wave_texture_node.inputs['Distortion'].default_value = 10.0

    color_ramp_node.color_ramp.elements[0].position = 0.4
    color_ramp_node.color_ramp.elements[0].color = [0.2, 0.1, 0.05, 1.0]
    color_ramp_node.color_ramp.elements[1].position = 0.6
    color_ramp_node.color_ramp.elements[1].color = base_color

    # Connect nodes
    links.new(texture_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
    links.new(mapping_node.outputs['Vector'], wave_texture_node.inputs['Vector'])
    links.new(wave_texture_node.outputs['Fac'], color_ramp_node.inputs['Fac'])
    links.new(color_ramp_node.outputs['Color'], principled_node.inputs['Base Color'])
    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

    return mat
```

这个高级木材材质使用了波纹纹理（Wave Texture）来创建更复杂的木纹图案，结合颜色渐变来模拟木材的自然变化。你可以通过调整波纹纹理的参数和颜色渐变来创建不同类型和外观的木材材质。

使用这些材质时，你可以根据需要调整参数，如基础颜色、粗糙度、纹理比例等，以创建各种不同类型的木材外观。