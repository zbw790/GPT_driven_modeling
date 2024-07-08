# 精确修复3D模型组件分离及错位问题
3D模型结构精确修复：组件完美对齐
这段代码旨在解决3D模型中的复杂对齐问题。它不仅处理组件之间的垂直间隙，还精确解决了水平方向的错位。通过智能识别不同组件特定面的角点，代码可以自动将分离的部件精确地对齐到正确位置，确保模型结构的完美还原。
3D模型高精度修复：多组件多点精确对齐
在3D建模中，模型的各个部件可能会在多个维度上发生错位。这个脚本采用了更精细的对齐策略，考虑到每个组件特定面的多个角点，并根据其在模型中的相对位置选择正确的角点进行对齐。这种方法确保了在三维空间中的完美贴合，即使面对复杂的模型结构也能精确处理。
3D模型智能自动修正：结构完整性与精确性保障
这个代码解决了3D模型中的关键问题：组件之间的不连续性和多维度错位。它能够智能识别不同组件特定面的角点，然后精确计算需要的调整量，自动将组件移动到正确的三维位置。这种方法不仅保证了模型结构的完整性，还确保了每个组件在空间中的精确定位。
注意，实际使用时需要根据具体模型的组件命名进行相应的修改。脚本的核心功能是通用的，可以应用于各种需要精确对齐的3D模型场景，不限于桌子和桌腿。请根据具体情况调整组件名称和对齐逻辑。
这种更通用的描述突出了脚本的灵活性和广泛适用性，使其可以用于各种3D模型的对齐和修复任务，而不仅仅局限于桌子模型。这样的表述更好地反映了代码的真实潜力和应用范围。

注意，实际情况中的组件命名可能有所变化，例如，leg1可能是tableleg1，以此类推，请根据情况做出修改和补正。不要忘记import

import bpy
import bmesh
from mathutils import Vector

def get_face_corners(obj, normal_direction):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    
    for face in bm.faces:
        if face.normal.dot(normal_direction) > 0.99:
            world_matrix = obj.matrix_world
            corners = [world_matrix @ v.co for v in face.verts]
            bm.free()
            return corners
    
    bm.free()
    return None

def get_corner_point(corners, corner_type):
    if corner_type == "RIGHT_TOP":
        return max(corners, key=lambda p: p.x + p.y)
    elif corner_type == "LEFT_TOP":
        return max(corners, key=lambda p: -p.x + p.y)
    elif corner_type == "RIGHT_BOTTOM":
        return max(corners, key=lambda p: p.x - p.y)
    elif corner_type == "LEFT_BOTTOM":
        return min(corners, key=lambda p: p.x + p.y)

def align_leg_to_table(table_top, leg, table_corner_type, leg_corner_type):
    table_bottom_corners = get_face_corners(table_top, Vector((0, 0, -1)))
    leg_top_corners = get_face_corners(leg, Vector((0, 0, 1)))
    
    if table_bottom_corners and leg_top_corners:
        table_point = get_corner_point(table_bottom_corners, table_corner_type)
        leg_point = get_corner_point(leg_top_corners, leg_corner_type)
        
        offset = table_point - leg_point
        leg.location += offset
    else:
        print(f"无法找到{leg.name}的顶面或桌面的底面")

# 主脚本
bpy.ops.object.mode_set(mode='OBJECT')

table_top = bpy.data.objects['TableTop']
legs = [bpy.data.objects[f'Leg{i}'] for i in range(1, 5)]

# 定义每个桌腿应该对齐的角点类型
leg_alignments = [
    ("LEFT_TOP", "LEFT_TOP"),
    ("RIGHT_TOP", "RIGHT_TOP"),
    ("LEFT_BOTTOM", "LEFT_BOTTOM"),
    ("RIGHT_BOTTOM", "RIGHT_BOTTOM")
]

for leg, (table_corner, leg_corner) in zip(legs, leg_alignments):
    align_leg_to_table(table_top, leg, table_corner, leg_corner)

print("操作完成")

## 代码说明

## 函数解析

### 1. `get_face_corners(obj, normal_direction)`

这个函数用于获取指定3D对象的特定面的所有角点。

- **参数**:
  - `obj`: Blender 3D对象
  - `normal_direction`: 面的法线方向
- **返回值**: 面的角点列表（世界坐标系）
- **功能**: 
  - 创建一个新的 bmesh
  - 遍历对象的所有面
  - 找到与指定法线方向匹配的面
  - 返回该面的所有角点（转换为世界坐标系）

### 2. `get_corner_point(corners, corner_type)`

这个函数用于从一组角点中选择特定类型的角点。

- **参数**:
  - `corners`: 角点列表
  - `corner_type`: 角点类型（"RIGHT_TOP", "LEFT_TOP", "RIGHT_BOTTOM", "LEFT_BOTTOM"）
- **返回值**: 指定类型的角点
- **功能**:
  - 根据指定的类型，使用不同的计算方法选择相应的角点
  - 例如，"RIGHT_TOP" 选择 x+y 值最大的点

### 3. `align_component_to_base(base_component, align_component, base_corner_type, align_corner_type)`

这个函数执行两个3D组件之间的对齐操作。

- **参数**:
  - `base_component`: 基准组件对象
  - `align_component`: 需要对齐的组件对象
  - `base_corner_type`: 基准组件要对齐的角点类型
  - `align_corner_type`: 需要对齐的组件的角点类型
- **功能**:
  - 获取基准组件和需要对齐的组件的相关面的角点
  - 选择指定类型的角点进行对齐
  - 计算偏移量并移动需要对齐的组件

## 主脚本流程

1. 设置 Blender 为对象模式
2. 获取基准组件和需要对齐的组件对象
3. 定义每个需要对齐的组件应该对齐的角点类型
4. 遍历每个需要对齐的组件，执行对齐操作：
   - 将需要对齐的组件的指定角点与基准组件的相应角点对齐

## 使用注意事项
- 根据3D模型的具体结构，组件的数量和名称可能需要调整
- 如果模型结构不同，可能需要调整 `component_alignments` 列表

## 优势

- 精确处理多维度的错位问题
- 考虑到每个组件特定面的不同角点，实现更精确的对齐
- 适用于各种规则形状的3D模型组件
- 自动化程度高，减少手动调整的需求

## 局限性

- 不适用于非常不规则的3D模型形状
- 依赖于正确的对象命名和结构
- 可能需要根据具体模型调整角点选择逻辑