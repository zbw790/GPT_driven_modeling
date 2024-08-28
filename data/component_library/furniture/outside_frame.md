# Blender 画框生成指南

这个指南提供了使用 Blender 的 Python API 生成外部框架的方法。

## 主要特征

1. 形状：可以是矩形、正方形、椭圆形或其他自定义形状
2. 尺寸：可调整宽度、高度和厚度
3. 边缘处理：可以有直边、斜角或装饰性边缘
4. 材质：可以模拟木材、金属、塑料等

## 尺寸参考

- 宽度: 0.2-2.0 m
- 高度: 0.2-2.0 m
- 厚度: 0.02-0.1 m
- 框架宽度: 0.02-0.15 m

## 椭圆形框架生成

对于椭圆形框架，可以使用以下代码：

```python
import bpy
import math

def create_oval_frame(width, height, depth, frame_thickness, segments=64):
    # 创建外框
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=depth, vertices=segments)
    outer_frame = bpy.context.active_object
    outer_frame.scale = (width/2, height/2, 1)

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
    bpy.context.view_layer.objects.active = outer_frame
    bpy.ops.object.modifier_apply(modifier="Boolean")

    # 删除内框对象
    bpy.data.objects.remove(inner_frame, do_unlink=True)

    # 重命名最终对象
    outer_frame.name = "Oval Picture Frame"

    return outer_frame

# 使用函数创建椭圆框架
oval_frame = create_oval_frame(width=2, height=1.5, depth=0.1, frame_thickness=0.1)

# 将视图聚焦到新创建的对象
bpy.context.view_layer.objects.active = oval_frame
oval_frame.select_set(True)
bpy.ops.view3d.view_selected(use_all_regions=False)
```

## 生成只挖空部分内胆而不挖穿的外框

下面的代码和上面的区别在于上面会直接挖穿中间，而这个代码只会往下挖一定深度

```python
import bpy
import bmesh

def create_picture_frame(width, height, depth, frame_thickness):
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

    return outer_frame

# 使用函数创建画框
frame = create_picture_frame(width=2, height=1.5, depth=0.1, frame_thickness=0.1)
```

## 注意事项

- 根据具体需求调整参数，如尺寸、边框宽度等。
- 生成后可能需要添加材质或进行其他修改以增加细节和真实感。
- 考虑添加装饰性元素，如雕刻或纹理，以增强画框的美观性。
- 确保画框尺寸与预期展示的艺术品尺寸相匹配。

## 高级技巧

- 使用贝塞尔曲线创建更复杂的框架形状。
- 添加凹槽或卡槽以便于插入画布或玻璃。
- 实现不同的边角处理方式，如斜角或圆角。
- 创建多层次的框架设计，增加深度感和复杂性。
