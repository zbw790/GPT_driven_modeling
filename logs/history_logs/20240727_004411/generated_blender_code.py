bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=50, radius2=5, depth=200, location=(0, 0, 100))
bpy.context.active_object.name = "树干"

# 创建树枝层函数
def create_branches():
    for i in range(6):
        depth = 30 - i * 4  # 每一层的树枝高度
        radius1 = 55 - i * 8  # 每一层的基底半径
        radius2 = 48 - i * 8  # 每一层的顶部半径
        z_offset = 100 + (i * 30) + (depth / 2)  # 计算每层的位置
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radius1, radius2=radius2, depth=depth, location=(0, 0, z_offset))
        bpy.context.active_object.name = f"树枝层_{i+1}"

create_branches()

bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=5, radius2=1, depth=20, location=(0, 0, 280))
bpy.context.active_object.name = "树顶尖端"

# 给所有组件设置绿色材质
green_material = bpy.data.materials.new(name="GreenMaterial")
green_material.diffuse_color = (0, 1, 0, 1)  # 深绿色

for obj in bpy.context.scene.objects:
    if obj.name.startswith("树干") or obj.name.startswith("树枝层") or obj.name == "树顶尖端":
        if obj.data.materials:
            obj.data.materials[0] = green_material
        else:
            obj.data.materials.append(green_material)