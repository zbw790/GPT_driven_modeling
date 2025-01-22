# 低多边形树木生成指南

这段代码专门用于生成低多边形风格的树木模型:

## 准备工作

在生成新模型之前,应清空场景中的所有现有对象。这可以通过以下Blender命令实现:

```python
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

## 基本结构

一个基础的低多边形树木由以下部分组成:
- 1个树干 (生成时,标注为 `Tree Trunk`)
- 1个树冠 (生成时,标注为 `Tree Crown`)
- 多个树枝 (生成时,标注为 `Tree Branch`)

## 尺寸参考

以下是常见低多边形树木的尺寸参考:

- 树干高度: 1 m
- 树干半径: 0.1 m
- 树冠半径: 0.5 m
- 树枝长度: 0.4 m
- 树枝基部半径: 0.05 m

注意: Blender使用米作为默认单位。

## 生成步骤

1. 清空场景中的所有现有对象
2. 创建树干 (`Tree Trunk`)
3. 创建树冠 (`Tree Crown`)
4. 创建多个树枝 (`Tree Branch`)
5. 创建一个新的集合 "Low Poly Tree" 并将所有部件添加到这个集合中
6. 从场景集合中移除所有对象,确保它们只存在于自定义集合中
7. 创建并应用材质
8. 更新场景视图

## 注意事项

- 确保所有部件都有适当的标注
- 树冠应位于树干顶部
- 树枝应均匀分布在树干周围
- 使用随机化来增加树木的自然感
- 保持低多边形风格,避免过多的细节
- 生成的模型应位于场景的中心点附近 (0, 0, 0)
- 保持各个部件独立,不要合并成一个整体模型

## Blender操作提示

- 使用 `bpy.ops.mesh.primitive_cylinder_add()` 创建树干
- 使用 `bpy.ops.mesh.primitive_ico_sphere_add()` 创建树冠
- 使用 `bpy.ops.mesh.primitive_cone_add()` 创建树枝
- 使用 `bmesh` 模块进行几何操作
- 使用 `obj.location = (x, y, z)` 定位物体
- 使用 `obj.rotation_euler = (x, y, z)` 旋转物体
- 使用 `bpy.data.collections.new()` 创建新集合
- 使用 `collection.objects.link(obj)` 将对象添加到集合
- 使用 `bpy.context.scene.collection.children.link(collection)` 将集合添加到场景
- 使用 `bpy.context.scene.collection.objects.unlink(obj)` 从场景集合中移除对象

## 材质创建

为树干、树冠和树枝创建不同的材质,使用节点系统来实现更复杂的效果:

- 树干材质: 使用噪波纹理创建木纹效果
- 树冠材质: 使用噪波纹理创建叶子的变化效果
- 树枝材质: 使用简单的褐色材质

## 示例代码

```python
import bpy
import bmesh
import math
import random

def create_tree_trunk():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1, vertices=8)
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

def create_tree_crown():
    # 创建一个新的网格
    mesh = bpy.data.meshes.new(name="Tree Crown")
    crown = bpy.data.objects.new("Tree Crown", mesh)

    # 将对象链接到场景
    bpy.context.collection.objects.link(crown)

    # 创建bmesh
    bm = bmesh.new()

    # 调整顶点分布，避免过于集中在极点
    latitudes = 8  # 纬度方向的细分数量
    longitudes = 8  # 经度方向的细分数量
    base_radius = 0.5

    # 引入不规则缩放，随机拉伸树冠
    scale_x = random.uniform(0.8, 2)
    scale_y = random.uniform(0.8, 2)
    scale_z = random.uniform(0.7, 1.3)

    for i in range(latitudes):
        phi = math.pi * i / (latitudes - 1)  # 从0到π的角度
        for j in range(longitudes):
            theta = 2 * math.pi * j / longitudes  # 从0到2π的角度
            
            # 球体坐标转换为直角坐标并引入不同方向的随机缩放
            x = base_radius * math.sin(phi) * math.cos(theta) * scale_x
            y = base_radius * math.sin(phi) * math.sin(theta) * scale_y
            z = base_radius * math.cos(phi) * scale_z
            
            # 轻微调整随机性
            x += random.uniform(0, 0.12)
            y += random.uniform(0, 0.15)
            z += random.uniform(0, 0.17)
            
            bm.verts.new((x, y, z))

    # 更新bmesh
    bm.verts.ensure_lookup_table()

    # 创建面，随机生成三角形或四边形面
    for i in range(latitudes - 1):
        for j in range(longitudes):
            v1 = bm.verts[i * longitudes + j]
            v2 = bm.verts[i * longitudes + (j + 1) % longitudes]
            v3 = bm.verts[(i + 1) * longitudes + (j + 1) % longitudes]
            v4 = bm.verts[(i + 1) * longitudes + j]

            # 随机决定创建四边形还是三角形
            if random.choice([True, False]):
                bm.faces.new((v1, v2, v3, v4))  # 创建四边形
            else:
                bm.faces.new((v1, v2, v3))     # 创建两个三角形
                bm.faces.new((v1, v3, v4))

    # 将bmesh应用到网格
    bm.to_mesh(mesh)
    bm.free()

    # 更新网格
    mesh.update()

    return crown

    
def create_branch(radius, length):
    bpy.ops.mesh.primitive_cone_add(radius1=radius, radius2=radius*0.2, depth=length, vertices=6)
    branch = bpy.context.active_object
    branch.name = "Tree Branch"
    return branch

def create_low_poly_tree():
    # 删除所有现有对象
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    tree_collection = bpy.data.collections.new("Low Poly Tree")
    bpy.context.scene.collection.children.link(tree_collection)
    
    trunk = create_tree_trunk()
    crown = create_tree_crown()
    crown.location = (0, 0, 0.8)
    
    # 添加树枝
    for i in range(3):
        branch = create_branch(0.05, 0.4)
        angle = i * (2 * math.pi / 3)
        branch.location = (0.2 * math.cos(angle), 0.2 * math.sin(angle), 0.6)
        branch.rotation_euler = (0, math.pi/4, angle)
        tree_collection.objects.link(branch)
    
    for obj in [trunk, crown] + [obj for obj in bpy.data.objects if obj.name.startswith("Tree")]:
        if obj.name not in tree_collection.objects:
            tree_collection.objects.link(obj)
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)
    
    # 创建材质
    trunk_material = create_trunk_material()
    crown_material = create_crown_material()
    branch_material = create_branch_material()
    
    # 应用材质
    trunk.data.materials.append(trunk_material)
    crown.data.materials.append(crown_material)
    for obj in bpy.data.objects:
        if obj.name.startswith("Tree Branch"):
            obj.data.materials.append(branch_material)
    
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

def create_branch_material():
    material = bpy.data.materials.new(name="Branch Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    
    node_principled = nodes["Principled BSDF"]
    node_principled.inputs['Base Color'].default_value = (0.25, 0.15, 0.07, 1)
    node_principled.inputs['Roughness'].default_value = 0.8
    
    return material

# 创建树
low_poly_tree = create_low_poly_tree()

# 更新视图
bpy.context.view_layer.update()
```

## 使用说明

1. 将此脚本复制到Blender的文本编辑器中。
2. 运行脚本以创建一个低多边形树木模型。
3. 可以通过修改 `create_low_poly_tree()` 函数中的参数来调整树木的尺寸和形状。

## 树冠生成方法

除了基本的低多边形树冠,我们还提供了一个可以生成更加圆滑树冠的方法:

```python
def create_smooth_tree_crown():
    # 使用UV球体而不是二十面体
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=0.5)
    crown = bpy.context.active_object
    crown.name = "Tree Crown"
    
    bm = bmesh.new()
    bm.from_mesh(crown.data)
    
    # 应用随机变形，但保持整体形状更加圆润
    for v in bm.verts:
        # 计算到中心的距离
        distance = v.co.length
        # 根据距离调整随机程度，使边缘变形更大
        factor = distance * 2
        v.co.x += random.uniform(-0.1, 0.1) * factor
        v.co.y += random.uniform(-0.1, 0.1) * factor
        v.co.z += random.uniform(-0.05, 0.15) * factor  # 稍微向上偏移
    
    # 稍微扁平化树冠
    for v in bm.verts:
        v.co.z *= 0.8
    
    # 应用平滑着色
    for f in bm.faces:
        f.smooth = True
    
    bm.to_mesh(crown.data)
    bm.free()
    
    # 添加细分表面修改器来进一步平滑
    subdivision = crown.modifiers.new(name="Subdivision", type='SUBSURF')
    subdivision.levels = 1
    subdivision.render_levels = 2
    
    return crown
```

这个方法可以生成更加圆滑的树冠,具有以下特点:

1. 使用UV球体作为基础形状,而不是二十面体,提供了更均匀的起始几何形状。
2. 通过随机变形来增加自然感,变形程度根据顶点到中心的距离而变化,使边缘更加不规则。
3. 轻微压扁整体形状,使树冠看起来更自然。
4. 应用平滑着色,使整体看起来更加柔和。
5. 添加细分表面修改器,进一步平滑了整个形状。

## 使用说明

要使用这个更圆滑的树冠生成方法,只需在 `create_low_poly_tree()` 函数中替换原来的 `create_tree_crown()` 调用:

```python
def create_low_poly_tree():
    # ... 其他代码保持不变 ...
    
    trunk = create_tree_trunk()
    crown = create_smooth_tree_crown()  # 使用新的树冠生成方法
    crown.location = (0, 0, 1.0)  # 调整树冠位置
    
    # ... 其他代码保持不变 ...
```
