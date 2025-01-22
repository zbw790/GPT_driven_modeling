# 画框生成指南

这个指南提供了生成各种画框的方法。画框是艺术品展示的重要组成部分，可以增强艺术品的视觉效果并提供保护。

## 主要特征

1. 形状：可以是矩形、正方形、椭圆形或其他自定义形状
2. 尺寸：可调整宽度、高度和厚度
3. 边缘处理：可以有直边、斜角或装饰性边缘
4. 材质：可以模拟木材、金属、塑料等
5. 图片：可以在画框中添加自定义图片

## 尺寸参考

- 宽度: 0.2-2.0 m
- 高度: 0.2-2.0 m
- 厚度: 0.02-0.1 m
- 框架宽度: 0.02-0.15 m

## 准备工作

在生成新模型之前,应清空场景中的所有现有对象。这可以通过以下Blender命令实现:

```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

## 带图片的矩形画框生成代码

以下是生成带图片的矩形画框的示例代码：

```python
import bpy
import os
import random

def create_picture_frame(width, height, depth, frame_thickness, image_folder):
    # 创建外框
    bpy.ops.mesh.primitive_cube_add(size=1)
    outer_frame = bpy.context.active_object
    outer_frame.scale = (width, height, depth)

    # 创建内框
    bpy.ops.mesh.primitive_cube_add(size=1)
    inner_frame = bpy.context.active_object
    inner_frame.scale = (width - frame_thickness*2, height - frame_thickness*2, depth*2)
    inner_frame.location = (0, 0, depth)

    # 添加布尔修改器
    bool_mod = outer_frame.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = inner_frame
    bool_mod.operation = 'DIFFERENCE'

    # 应用布尔修改器
    bpy.context.view_layer.objects.active = outer_frame
    bpy.ops.object.modifier_apply(modifier="Boolean")

    # 删除内框对象
    bpy.data.objects.remove(inner_frame, do_unlink=True)

    # 重命名最终对象
    outer_frame.name = "Picture Frame"

    # 创建图片平面
    bpy.ops.mesh.primitive_plane_add(size=1)
    image_plane = bpy.context.active_object
    image_plane.scale = (width - frame_thickness*2, height - frame_thickness*2, 1)
    image_plane.location = (0, 0, depth/2)  # 将图片放在框架中间

    # 创建图片材质
    image_material = bpy.data.materials.new(name="Image Material")
    image_material.use_nodes = True
    nodes = image_material.node_tree.nodes
    nodes.clear()

    # 创建图片纹理节点
    texture_node = nodes.new(type='ShaderNodeTexImage')
    texture_node.location = (-300, 0)

    # 从文件夹中随机选择一张图片
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
    if image_files:
        random_image = random.choice(image_files)
        image_path = os.path.join(image_folder, random_image)
        img = bpy.data.images.load(image_path)
        texture_node.image = img
        print(f"Loaded image: {image_path}")
    else:
        print(f"No image files found in {image_folder}")

    # 创建漫反射 BSDF 节点
    diffuse_node = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse_node.location = (0, 0)

    # 创建输出节点
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (300, 0)

    # 连接节点
    links = image_material.node_tree.links
    links.new(texture_node.outputs['Color'], diffuse_node.inputs['Color'])
    links.new(diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])

    # 将材质分配给图片平面
    image_plane.data.materials.append(image_material)

    # 创建一个集合来包含画框和图片
    frame_collection = bpy.data.collections.new("Picture Frame with Image")
    bpy.context.scene.collection.children.link(frame_collection)

    # 将画框和图片添加到集合中
    frame_collection.objects.link(outer_frame)
    frame_collection.objects.link(image_plane)

    # 从主场景集合中移除对象（可选）
    bpy.context.scene.collection.objects.unlink(outer_frame)
    bpy.context.scene.collection.objects.unlink(image_plane)

    return frame_collection

# 使用函数创建画框和图片
image_folder = r"C:\Users\Bowen\Pictures"  # 使用原始字符串表示法，请务必使用这个路径
frame = create_picture_frame(width=2, height=1.5, depth=0.1, frame_thickness=0.1, image_folder=image_folder)

```

## 使用说明

1. 将此脚本复制到Blender的文本编辑器中。
2. 修改 `image_folder` 变量，指向您本地的图片文件夹。
3. 运行脚本以创建一个带随机图片的画框模型。
4. 可以通过修改 `create_picture_frame()` 函数的参数来调整画框的尺寸和细节。

## 注意事项

- 确保指定的图片文件夹中包含支持的图片格式（.png, .jpg, .jpeg, .bmp, .tiff）。
- 根据具体需求调整参数，如尺寸、边框宽度等。
- 生成后可能需要添加额外的材质或进行其他修改以增加细节和真实感。
- 考虑添加装饰性元素，如雕刻或纹理，以增强画框的美观性。
- 确保画框尺寸与预期展示的艺术品尺寸相匹配。

## 高级技巧

- 使用贝塞尔曲线创建更复杂的框架形状。
- 添加凹槽或卡槽以便于插入画布或玻璃。
- 实现不同的边角处理方式，如斜角或圆角。
- 创建多层次的框架设计，增加深度感和复杂性。
- 添加选项来指定特定的图片，而不是随机选择。
- 实现图片缩放和裁剪功能，以确保图片正确填充画框。
- 添加画框材质选项，如木纹、金属或彩色涂料。