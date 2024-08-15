# 家具腿部组件生成指南

这段代码用于生成各种家具的腿部组件。家具腿是支撑家具主体的重要结构，可以应用于多种家具类型。主要包括：

1. 桌腿：支撑各种类型的桌子，如办公桌、餐桌、咖啡桌等。通常为直筒状或略有弧度，可能带有调节功能。

2. 椅腿：用于各种椅子，包括餐椅、办公椅、休闲椅等。形状多样，可能是直的、弯曲的或带有特殊设计。

3. 沙发腿：支撑沙发，通常较短且坚固。可能是木质、金属或塑料材质，设计上可能更注重装饰性。

4. 柜子腿：用于衣柜、书柜、边柜等。可能较为隐蔽，有时采用整体底座设计。

5. 床腿：支撑床架，通常较为粗壮，可能带有滚轮设计。

家具腿的设计考虑因素包括：
- 承重能力：需要根据家具类型和尺寸确定适当的强度。
- 高度：影响家具的整体高度和使用舒适度。
- 材质：常见有木质、金属、塑料等，影响外观和耐用性。
- 样式：可以是现代简约、古典雕花、工业风等不同风格。
- 调节功能：某些家具腿可能需要高度调节或防滑设计。

## 主要特征

1. 结构简单：通常是长方体或圆柱体，但也可根据需求替换成其他形状
2. 尺寸可调：可以根据不同家具的需求调整高度和粗细
3. 位置灵活：可以根据家具类型调整腿部的位置和数量
4. 材质多样：可以是木质、金属或其他材料

## 尺寸参考

以下是常见家具腿的尺寸参考：

- 高度: 15-75 cm (0.3-0.75 m in Blender)
- 宽度: 3-7 cm (0.03-0.07 m in Blender)
- 厚度: 3-7 cm (0.03-0.07 m in Blender)

注意: Blender使用米作为默认单位，所以在创建模型时，需要将厘米转换为米。

## 生成步骤

1. 创建一个长方体或圆柱体作为腿部的基本形状
2. 调整腿部的尺寸（高度、宽度、厚度）
3. 根据需要添加细节，如倒角或简单的纹理
4. 正确命名和标注腿部组件

## 示例代码

以下是一个生成简单长方体腿部的示例代码：

```python
import bpy

def create_leg(name, location, height=0.75, width=0.05, depth=0.05):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    leg = bpy.context.active_object
    leg.scale = (width, depth, height)
    leg.name = name
    
    # 添加倒角修改器
    bevel_modifier = leg.modifiers.new(name="Bevel", type='BEVEL')
    bevel_modifier.width = 0.002
    bevel_modifier.segments = 5
    bevel_modifier.limit_method = 'ANGLE'
    bevel_modifier.angle_limit = 1.15  # 约66度
    
    return leg

# 使用示例
leg = create_leg("table_leg", location=(0, 0, 0.375))