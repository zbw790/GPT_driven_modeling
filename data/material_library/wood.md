# 木材材质 (Wood Material)

木材是一种常用于家具、建筑和装饰的天然材料。它具有独特的纹理、颜色变化和温暖的外观，使其成为许多设计中的首选材料。

## 特征

1. 纹理：木材具有独特的纹理模式，包括年轮、节点和木纹。
2. 颜色：从浅色（如枫木）到深色（如黑胡桃木），颜色范围广泛。
3. 反射特性：通常具有低到中等的反射率，取决于表面处理。
4. 次表面散射：木材具有一定程度的次表面散射，使其看起来更自然。

## 在Blender中创建木材材质

要在Blender中创建逼真的木材材质，我们主要使用Principled BSDF着色器，并结合程序化纹理来模拟木纹。

### 参数示例

以下是橡木材质的参数示例：

```json
{
    "material_type": "wood",
    "base_color": [0.8, 0.6, 0.4, 1.0],
    "metallic": 0.0,
    "roughness": 0.7,
    "ior": 1.5,
    "alpha": 1.0,
    "normal": [0.0, 0.0, 1.0],
    "specular_ior_level": 0.5,
    "specular_tint": [1.0, 1.0, 1.0, 1.0],
    "anisotropic": 0.2,
    "anisotropic_rotation": 0.0,
    "transmission_weight": 0.0,
    "coat_weight": 0.1,
    "coat_roughness": 0.1,
    "coat_ior": 1.5,
    "coat_tint": [1.0, 1.0, 1.0, 1.0],
    "wood_grain_texture": {
        "scale": [10, 5, 5],
        "noise_scale": 5,
        "noise_detail": 8,
        "noise_roughness": 0.6,
        "color_ramp": [
            {"position": 0.4, "color": [0.7, 0.5, 0.3, 1.0]},
            {"position": 0.6, "color": [0.9, 0.7, 0.5, 1.0]}
        ],
        "mix_blend_type": "OVERLAY",
        "mix_factor": 0.3
    }
}
```

### 生成代码

以下是在Blender中创建木材材质的Python代码：

```python
import bpy

def create_wood_texture(material):
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
    mapping.inputs['Scale'].default_value = (10, 5, 5)
    noise_texture.inputs['Scale'].default_value = 5
    noise_texture.inputs['Detail'].default_value = 8
    noise_texture.inputs['Roughness'].default_value = 0.6

    # 设置颜色渐变
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.7, 0.5, 0.3, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.6
    color_ramp.color_ramp.elements[1].color = (0.9, 0.7, 0.5, 1.0)

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
    mix_rgb.inputs[0].default_value = 0.3

# 创建木材材质
wood_material = bpy.data.materials.new(name="Wood_Material")
wood_material.use_nodes = True
nodes = wood_material.node_tree.nodes
principled = nodes["Principled BSDF"]
principled.inputs["Base Color"].default_value = [0.8, 0.6, 0.4, 1.0]
principled.inputs["Metallic"].default_value = 0.0
principled.inputs["Roughness"].default_value = 0.7
principled.inputs["IOR"].default_value = 1.5
principled.inputs["Alpha"].default_value = 1.0
principled.inputs["Normal"].default_value = [0.0, 0.0, 1.0]
principled.inputs["Specular IOR Level"].default_value = 0.5
principled.inputs["Specular Tint"].default_value = [1.0, 1.0, 1.0, 1.0]
principled.inputs["Anisotropic"].default_value = 0.2
principled.inputs["Anisotropic Rotation"].default_value = 0.0
principled.inputs["Transmission Weight"].default_value = 0.0
principled.inputs["Coat Weight"].default_value = 0.1
principled.inputs["Coat Roughness"].default_value = 0.1
principled.inputs["Coat IOR"].default_value = 1.5
principled.inputs["Coat Tint"].default_value = [1.0, 1.0, 1.0, 1.0]

create_wood_texture(wood_material)

# 将材质应用到Cube对象
cube = bpy.data.objects["Cube"]
if cube.data.materials:
    cube.data.materials[0] = wood_material
else:
    cube.data.materials.append(wood_material)
```

这段代码创建了一个基于Principled BSDF的木材材质，并使用噪波纹理和颜色渐变来模拟木纹。你可以通过调整参数来创建不同类型和外观的木材材质。