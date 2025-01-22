# 金属材质 (Metal Material)

金属是一种常用于工业、建筑和设计的材料。它具有独特的光泽、反射性和导热性，使其在许多应用中不可或缺。金属材质可以呈现出从哑光到高度抛光的各种外观。

## 特征

1. 反射性：金属通常具有高反射性，能够反射周围环境。
2. 颜色：从银白色（如铝）到金黄色（如黄铜），颜色范围广泛。
3. 光泽：可以从哑光到高度抛光，影响其反射特性。
4. 导电性和导热性：这些特性虽然在视觉上不直接可见，但会影响材质的整体感觉。

## 在Blender中创建金属材质

要在Blender中创建逼真的金属材质，我们主要使用Principled BSDF着色器，并可能结合程序化纹理来模拟微小的划痕或不均匀性。

### 参数示例

以下是不锈钢材质的参数示例：

```json
{
    "material_type": "metal",
    "base_color": [0.8, 0.8, 0.8, 1.0],
    "metallic": 1.0,
    "roughness": 0.2,
    "ior": 2.5,
    "alpha": 1.0,
    "normal": [0.0, 0.0, 1.0],
    "specular_ior_level": 0.5,
    "specular_tint": [1.0, 1.0, 1.0, 1.0],
    "anisotropic": 0.1,
    "anisotropic_rotation": 0.0,
    "transmission_weight": 0.0,
    "coat_weight": 0.0,
    "coat_roughness": 0.0,
    "coat_ior": 1.5,
    "coat_tint": [1.0, 1.0, 1.0, 1.0],
    "metal_texture": {
        "noise_scale": 50,
        "noise_detail": 2,
        "noise_roughness": 0.7,
        "color_ramp": [
            {"position": 0.4, "color": [0.75, 0.75, 0.75, 1.0]},
            {"position": 0.6, "color": [0.85, 0.85, 0.85, 1.0]}
        ],
        "mix_blend_type": "OVERLAY",
        "mix_factor": 0.05
    }
}
```

### 生成代码

以下是在Blender中创建金属材质的Python代码：

```python
import bpy

def create_metal_texture(material):
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
    noise_texture.inputs['Scale'].default_value = 50
    noise_texture.inputs['Detail'].default_value = 2
    noise_texture.inputs['Roughness'].default_value = 0.7

    # 设置颜色渐变
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.75, 0.75, 0.75, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.6
    color_ramp.color_ramp.elements[1].color = (0.85, 0.85, 0.85, 1.0)

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

# 创建金属材质
metal_material = bpy.data.materials.new(name="Metal_Material")
metal_material.use_nodes = True
nodes = metal_material.node_tree.nodes
principled = nodes["Principled BSDF"]
principled.inputs["Base Color"].default_value = [0.8, 0.8, 0.8, 1.0]
principled.inputs["Metallic"].default_value = 1.0
principled.inputs["Roughness"].default_value = 0.2
principled.inputs["IOR"].default_value = 2.5
principled.inputs["Alpha"].default_value = 1.0
principled.inputs["Normal"].default_value = [0.0, 0.0, 1.0]
principled.inputs["Specular IOR Level"].default_value = 0.5
principled.inputs["Specular Tint"].default_value = [1.0, 1.0, 1.0, 1.0]
principled.inputs["Anisotropic"].default_value = 0.1
principled.inputs["Anisotropic Rotation"].default_value = 0.0
principled.inputs["Transmission Weight"].default_value = 0.0
principled.inputs["Coat Weight"].default_value = 0.0
principled.inputs["Coat Roughness"].default_value = 0.0
principled.inputs["Coat IOR"].default_value = 1.5
principled.inputs["Coat Tint"].default_value = [1.0, 1.0, 1.0, 1.0]

create_metal_texture(metal_material)

# 将材质应用到Cube对象
cube = bpy.data.objects["Cube"]
if cube.data.materials:
    cube.data.materials[0] = metal_material
else:
    cube.data.materials.append(metal_material)
```

这段代码创建了一个基于Principled BSDF的金属材质，并使用噪波纹理来模拟微小的表面变化。你可以通过调整参数来创建不同类型和外观的金属材质，如黄铜、铝、钢等。