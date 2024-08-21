# 玻璃材质 (Glass Material)

玻璃是一种透明或半透明的材料，广泛应用于建筑、家居和工业设计中。它具有独特的光学特性，包括透明度、折射和反射，使其成为创造视觉效果的理想材料。

## 特征

1. 透明度：从完全透明到半透明，取决于玻璃的类型和处理方式。
2. 折射：光线通过玻璃时会发生弯曲，产生独特的视觉效果。
3. 反射：玻璃表面会反射部分光线，尤其是在特定角度下。
4. 色彩：可以是无色的，也可以添加各种颜色。
5. 表面质感：可以是光滑的，也可以是磨砂或纹理化的。

## 在Blender中创建玻璃材质

要在Blender中创建逼真的玻璃材质，我们主要使用Principled BSDF着色器，并调整其透明度、折射率和粗糙度等参数。

### 参数示例

以下是清玻璃材质的参数示例：

```json
{
    "material_type": "glass",
    "base_color": [0.95, 0.95, 0.95, 1.0],
    "metallic": 0.0,
    "roughness": 0.05,
    "ior": 1.52,
    "alpha": 0.05,
    "normal": [0.0, 0.0, 1.0],
    "specular_ior_level": 0.5,
    "specular_tint": [1.0, 1.0, 1.0, 1.0],
    "anisotropic": 0.0,
    "anisotropic_rotation": 0.0,
    "transmission_weight": 0.95,
    "coat_weight": 0.1,
    "coat_roughness": 0.01,
    "coat_ior": 1.5,
    "coat_tint": [1.0, 1.0, 1.0, 1.0],
    "glass_texture": {
        "noise_scale": 100,
        "noise_detail": 2,
        "noise_roughness": 0.5,
        "color_ramp": [
            {"position": 0.4, "color": [0.95, 0.95, 0.95, 1.0]},
            {"position": 0.6, "color": [1.0, 1.0, 1.0, 1.0]}
        ],
        "mix_blend_type": "OVERLAY",
        "mix_factor": 0.02
    }
}
```

### 生成代码

以下是在Blender中创建玻璃材质的Python代码：

```python
import bpy

def create_glass_texture(material):
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
    noise_texture.inputs['Scale'].default_value = 100
    noise_texture.inputs['Detail'].default_value = 2
    noise_texture.inputs['Roughness'].default_value = 0.5

    # 设置颜色渐变
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.95, 0.95, 0.95, 1.0)
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
    mix_rgb.inputs[0].default_value = 0.02

# 创建玻璃材质
glass_material = bpy.data.materials.new(name="Glass_Material")
glass_material.use_nodes = True
nodes = glass_material.node_tree.nodes
principled = nodes["Principled BSDF"]
principled.inputs["Base Color"].default_value = [0.95, 0.95, 0.95, 1.0]
principled.inputs["Metallic"].default_value = 0.0
principled.inputs["Roughness"].default_value = 0.05
principled.inputs["IOR"].default_value = 1.52
principled.inputs["Alpha"].default_value = 0.05
principled.inputs["Normal"].default_value = [0.0, 0.0, 1.0]
principled.inputs["Specular IOR Level"].default_value = 0.5
principled.inputs["Specular Tint"].default_value = [1.0, 1.0, 1.0, 1.0]
principled.inputs["Anisotropic"].default_value = 0.0
principled.inputs["Anisotropic Rotation"].default_value = 0.0
principled.inputs["Transmission Weight"].default_value = 0.95
principled.inputs["Coat Weight"].default_value = 0.1
principled.inputs["Coat Roughness"].default_value = 0.01
principled.inputs["Coat IOR"].default_value = 1.5
principled.inputs["Coat Tint"].default_value = [1.0, 1.0, 1.0, 1.0]

create_glass_texture(glass_material)

# 将材质应用到Cube对象
cube = bpy.data.objects["Cube"]
if cube.data.materials:
    cube.data.materials[0] = glass_material
else:
    cube.data.materials.append(glass_material)
```

这段代码创建了一个基于Principled BSDF的玻璃材质，并使用噪波纹理来模拟微小的表面变化。你可以通过调整参数来创建不同类型的玻璃效果，如磨砂玻璃、彩色玻璃等。注意，为了获得最佳的玻璃效果，你可能需要在渲染设置中启用屏幕空间反射和折射。