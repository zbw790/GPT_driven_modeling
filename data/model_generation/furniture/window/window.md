# 窗户生成指南

这个指南包含了生成椭圆形和长方形窗户的代码和说明。

## 准备工作

在生成新模型之前，应清空场景中的所有现有对象：

```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

## 基本结构

一个基础的窗户由以下部分组成：
- 1个窗框 (生成时，标注为 `Window Frame`)
- 1个玻璃面板 (生成时，标注为 `Window Glass`)

## 尺寸参考

以下是常见窗户的尺寸参考：

- 宽度：1-3 m
- 高度：0.75-2.25 m
- 深度：0.1-0.2 m
- 框架厚度：0.05-0.15 m
- 玻璃厚度：0.01-0.03 m

注意：Blender使用米作为默认单位。

## 椭圆形窗户代码

```python
import bpy
import math

def create_oval_window(width, height, depth, frame_thickness, glass_thickness=0.01, segments=64):
    # 创建外框
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=depth, vertices=segments)
    outer_frame = bpy.context.active_object
    outer_frame.scale = (width/2, height/2, 1)
    outer_frame.name = "Window Frame"

    # 创建内框
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=depth*2, vertices=segments)
    inner_frame = bpy.context.active_object
    inner_frame.scale = ((width-frame_thickness*2)/2, (height-frame_thickness*2)/2, 1)
    inner_frame.location = (0, 0, 0)

    # 添加布尔修改器
    bool_mod = outer_frame.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = inner_frame
    bool_mod.operation = 'DIFFERENCE'

    # 应用布尔修改器
    # 注意这个步骤非常重要，若不进行挖空，什么都看不到
    bpy.context.view_layer.objects.active = outer_frame
    bpy.ops.object.modifier_apply(modifier="Boolean")

    # 删除内框对象
    bpy.data.objects.remove(inner_frame, do_unlink=True)

    # 创建玻璃
    # 注意玻璃的生成位置应该正好在外框中间
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=glass_thickness, vertices=segments)
    glass = bpy.context.active_object
    glass.scale = ((width-frame_thickness*2)/2, (height-frame_thickness*2)/2, 1)
    glass.location = (0, 0, 0)
    glass.name = "Window Glass"

    # 创建玻璃材质
    glass_material = bpy.data.materials.new(name="Glass Material")
    glass_material.use_nodes = True
    nodes = glass_material.node_tree.nodes
    nodes.clear()
    
    # 创建玻璃 BSDF 节点
    glass_node = nodes.new(type='ShaderNodeBsdfGlass')
    glass_node.location = (0, 0)
    
    # 创建输出节点
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (200, 0)
    
    # 连接节点
    links = glass_material.node_tree.links
    links.new(glass_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    # 将材质分配给玻璃对象
    glass.data.materials.append(glass_material)

    # 创建一个集合来包含窗户的所有部分
    window_collection = bpy.data.collections.new("Oval Window")
    bpy.context.scene.collection.children.link(window_collection)
    
    # 将框架和玻璃添加到集合中
    window_collection.objects.link(outer_frame)
    window_collection.objects.link(glass)
    
    # 从主场景集合中移除对象（可选）
    bpy.context.scene.collection.objects.unlink(outer_frame)
    bpy.context.scene.collection.objects.unlink(glass)

    return window_collection

# 使用函数创建椭圆窗户
oval_window = create_oval_window(width=2, height=1.5, depth=0.1, frame_thickness=0.1, glass_thickness=0.02)
```

## 长方形窗户代码

```python
import bpy

def create_rectangular_window(width, height, depth, frame_thickness, glass_thickness=0.01):
    # 创建外框
    bpy.ops.mesh.primitive_cube_add(size=1)
    outer_frame = bpy.context.active_object
    outer_frame.scale = (width, height, depth)
    outer_frame.name = "Window Frame"

    # 创建内框
    bpy.ops.mesh.primitive_cube_add(size=1)
    inner_frame = bpy.context.active_object
    inner_frame.scale = (width - frame_thickness*2, height - frame_thickness*2, depth*2)
    inner_frame.location = (0, 0, 0)

    # 添加布尔修改器
    bool_mod = outer_frame.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = inner_frame
    bool_mod.operation = 'DIFFERENCE'

    # 应用布尔修改器
    bpy.context.view_layer.objects.active = outer_frame
    bpy.ops.object.modifier_apply(modifier="Boolean")

    # 删除内框对象
    bpy.data.objects.remove(inner_frame, do_unlink=True)

    # 创建玻璃
    bpy.ops.mesh.primitive_plane_add(size=1)
    glass = bpy.context.active_object
    glass.scale = (width - frame_thickness*2, height - frame_thickness*2, 1)
    glass.location = (0, 0, 0)
    glass.name = "Window Glass"

    # 创建玻璃材质
    glass_material = bpy.data.materials.new(name="Glass Material")
    glass_material.use_nodes = True
    nodes = glass_material.node_tree.nodes
    nodes.clear()
    
    # 创建玻璃 BSDF 节点
    glass_node = nodes.new(type='ShaderNodeBsdfGlass')
    glass_node.location = (0, 0)
    
    # 创建输出节点
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (200, 0)
    
    # 连接节点
    links = glass_material.node_tree.links
    links.new(glass_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    # 将材质分配给玻璃对象
    glass.data.materials.append(glass_material)

    # 创建一个集合来包含窗户的所有部分
    window_collection = bpy.data.collections.new("Rectangular Window")
    bpy.context.scene.collection.children.link(window_collection)
    
    # 将框架和玻璃添加到集合中
    window_collection.objects.link(outer_frame)
    window_collection.objects.link(glass)
    
    # 从主场景集合中移除对象（可选）
    bpy.context.scene.collection.objects.unlink(outer_frame)
    bpy.context.scene.collection.objects.unlink(glass)

    return window_collection

# 使用函数创建长方形窗户
rectangular_window = create_rectangular_window(width=1.5, height=1, depth=0.1, frame_thickness=0.05, glass_thickness=0.01)
```

## 使用说明

1. 将所需的代码复制到Blender的文本编辑器中。
2. 运行脚本以创建所需类型的窗户模型。
3. 可以通过修改函数的参数来调整窗户的尺寸和细节。

## 注意事项

- 确保所有部件都有适当的标注
- 玻璃面板应位于窗框内部
- 可以根据需要调整尺寸，但要保持合理的比例
- 生成的模型应尽可能位于场景的中心点附近 (0, 0, 0)
- 保持窗框和玻璃独立，不要合并成一个整体模型

## 扩展思路

- 可以添加更多细节，如窗框装饰或纹理
- 可以创建不同形状的窗户，如圆形或拱形窗户
- 可以添加窗帘、百叶窗或窗格等附加组件
- 可以调整玻璃材质以创建不同类型的玻璃效果，如磨砂玻璃或彩色玻璃
- 可以创建更复杂的窗户类型，如滑动窗或双层窗