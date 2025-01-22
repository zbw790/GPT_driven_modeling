# 修复桌子腿与桌面分离的问题
桌子结构问题修复：桌面与桌腿分离
这段代码旨在解决一个常见的3D模型问题：桌子的桌面和桌腿之间出现了不自然的间隙。通过精确计算和调整，代码可以自动将分离的桌腿精确地对齐到桌面底部，恢复桌子的正确结构。
家具模型修复：桌子组件对齐
在3D建模中，桌子各部件可能会意外错位。这个脚本专门处理桌面和桌腿之间的垂直间隙问题，通过智能识别桌面底部和桌腿顶部，自动调整它们的相对位置，确保完美贴合。
3D模型自动修正：桌子结构完整性
这个代码解决了3D桌子模型中的一个关键问题：桌腿与桌面之间的不连续性。它能够识别桌面的底部平面和每个桌腿的顶部平面，然后精确计算需要的调整量，自动将桌腿移动到正确的位置，保证桌子结构的完整性。

## 示例代码

```python
import bpy
import bmesh
from mathutils import Vector

def get_face_center_by_normal(obj, normal_direction):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    for face in bm.faces:
        if face.normal.dot(normal_direction) > 0.99:
            center = face.calc_center_median()
            world_center = obj.matrix_world @ center
            bm.free()
            return world_center
    bm.free()
    return None

table_top = bpy.data.objects['TableTop']
bottom_face_center = get_face_center_by_normal(table_top, Vector((0, 0, -1)))

if bottom_face_center is None:
    print("无法找到桌面的底面")
else:
    for leg_name in ['Leg1', 'Leg2', 'Leg3', 'Leg4']:
        leg = bpy.data.objects[leg_name]
        top_face_center = get_face_center_by_normal(leg, Vector((0, 0, 1)))
        if top_face_center is not None:
            z_offset = bottom_face_center.z - top_face_center.z
            leg.location.z += z_offset
        else:
            print(f"无法找到{leg_name}的顶面")

print("操作完成")
```

## 代码说明

1. 首先，我们定义了一个函数 `get_face_center_by_normal`，用于找到指定法向量方向的面的中心点。

2. 然后，我们找到桌面（TableTop）底面的中心点。

3. 接下来，我们遍历每个桌腿（Leg1, Leg2, Leg3, Leg4），找到它们顶面的中心点。

4. 计算每个桌腿需要在 Z 轴上移动的距离，使其顶面与桌面底面对齐。

5. 最后，我们调整每个桌腿的 Z 轴位置。

注意：这段代码假设桌面和桌腿的名称分别为 'TableTop' 和 'Leg1', 'Leg2', 'Leg3', 'Leg4'。如果您的场景中对象名称不同，请相应地修改代码。

## 使用方法

1. 在 Blender 中打开包含桌子模型的场景。
2. 打开 Blender 的文本编辑器。
3. 创建一个新的文本文件，将上述代码粘贴进去。
4. 运行脚本。

脚本执行后，桌腿应该会自动调整到正确的高度，与桌面底部对齐。
```