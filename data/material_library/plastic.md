# 透明塑料材质 (Transparent Plastic Material)

透明塑料是一种常见的合成材料，广泛应用于包装、家居用品、电子产品外壳等领域。它具有轻量、可塑性强、透明度高等特点，同时也可以呈现出不同程度的透明度和颜色。

## 特征

1. 透明度：从完全透明到半透明，可以根据需要调整。
2. 折射：光线通过塑料时会发生轻微弯曲，但不如玻璃明显。
3. 表面光泽：通常有光泽，但可以是哑光的。
4. 颜色：可以是无色的，也可以添加各种颜色。
5. 硬度：比玻璃软，但硬度可以变化。
6. 表面质感：可以是光滑的，也可以有纹理。

## 在Blender中创建透明塑料材质

要在Blender中创建逼真的透明塑料材质，我们主要使用Principled BSDF着色器，并调整其透明度、折射率和粗糙度等参数。

### 参数示例

以下是透明塑料材质的参数示例：

```json
{
    "material_type": "transparent_plastic",
    "base_color": [0.9, 0.9, 0.9, 1.0],
    "metallic": 0.0,
    "roughness": 0.1,
    "ior": 1.45,
    "alpha": 0.2,
    "normal": [0.0, 0.0, 1.0],
    "specular_ior_level": 0.5,
    "specular_tint": [1.0, 1.0, 1.0, 1.0],
    "anisotropic": 0.0,
    "anisotropic_rotation": 0.0,
    "transmission_weight": 0.9,
    "coat_weight": 0.2,
    "coat_roughness": 0.1,
    "coat_ior": 1.5,
    "coat_tint": [1.0, 1.0, 1.0, 1.0],
    "plastic_texture": {
        "noise_scale": 500,
        "noise_detail": 2,
        "noise_roughness": 0.5,
        "color_ramp": [
            {"position": 0.4, "color": [0.9, 0.9, 0.9, 1.0]},
            {"position": 0.6, "color": [1.0, 1.0, 1.0, 1.0]}
        ],
        "mix_blend_type": "OVERLAY",
        "mix_factor": 0.05
    }
}
```

### 生成代码

以下是在Blender中创建透明塑料材质的Python代码：

```python
import bpy

def create_plastic_texture(material):
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # 保留原有的Principled BSDF节点
    principled = nodes["Principled BSDF"]
    
    # 创建新节点
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    mapping = nodes.new(type='ShaderNodeMapping')
    noise_texture = nodes.new(type='ShaderNodeTexNoise')
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')

    # 设置节点
    mapping.inputs['Scale'].default_value = (1, 1, 1)
    noise_texture.inputs['Scale'].default_value = 500
    noise_texture.inputs['Detail'].default_value = 2
    noise_texture.inputs['Roughness'].default_value = 0.5

    # 设置颜色渐变
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.9, 0.9, 0.9, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.6
    color_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # 连接节点
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], noise_texture.inputs['Vector'])
    links.new(noise_texture.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], mix_rgb.inputs[1])
    
    # 安全地处理Base Color连接
    if principled.inputs['Base Color'].links:
        links.new(principled.inputs['Base Color'].links[0].from_socket, mix_rgb.inputs[2])
    else:
        mix_rgb.inputs[2].default_value = principled.inputs['Base Color'].default_value

    links.new(mix_rgb.outputs['Color'], principled.inputs['Base Color'])

    mix_rgb.blend_type = 'OVERLAY'
    mix_rgb.inputs[0].default_value = 0.05

# 创建透明塑料材质
plastic_material = bpy.data.materials.new(name="Transparent_Plastic_Material")
plastic_material.use_nodes = True
nodes = plastic_material.node_tree.nodes
principled = nodes["Principled BSDF"]
principled.inputs["Base Color"].default_value = [0.9, 0.9, 0.9, 1.0]
principled.inputs["Metallic"].default_value = 0.0
principled.inputs["Roughness"].default_value = 0.1
principled.inputs["IOR"].default_value = 1.45
principled.inputs["Alpha"].default_value = 0.2
principled.inputs["Normal"].default_value = [0.0, 0.0, 1.0]
principled.inputs["Specular IOR Level"].default_value = 0.5
principled.inputs["Specular Tint"].default_value = [1.0, 1.0, 1.0, 1.0]
principled.inputs["Anisotropic"].default_value = 0.0
principled.inputs["Anisotropic Rotation"].default_value = 0.0
principled.inputs["Transmission Weight"].default_value = 0.9
principled.inputs["Coat Weight"].default_value = 0.2
principled.inputs["Coat Roughness"].default_value = 0.1
principled.inputs["Coat IOR"].default_value = 1.5
principled.inputs["Coat Tint"].default_value = [1.0, 1.0, 1.0, 1.0]

create_plastic_texture(plastic_material)

# 将材质应用到Cube对象
cube = bpy.data.objects["Cube"]
if cube.data.materials:
    cube.data.materials[0] = plastic_material
else:
    cube.data.materials.append(plastic_material)

# 设置材质为透明
plastic_material.use_nodes = True
plastic_material.blend_method = 'BLEND'
plastic_material.shadow_method = 'HASHED'
```

这段代码创建了一个基于Principled BSDF的透明塑料材质，并使用噪波纹理来模拟微小的表面变化。你可以通过调整参数来创建不同类型的塑料效果，如更透明或更不透明的塑料、有色塑料等。注意，最后几行代码设置了材质的混合方法和阴影方法，这对于正确渲染透明材质很重要。