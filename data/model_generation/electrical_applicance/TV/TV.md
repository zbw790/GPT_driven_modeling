import bpy
import math

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 删除所有集合（除了场景的主集合）
for collection in bpy.data.collections:
    bpy.data.collections.remove(collection)
# 创建电视机集合
tv_collection = bpy.data.collections.new("TV")
bpy.context.scene.collection.children.link(tv_collection)

# 创建屏幕
bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, location=(0, 0, 0.35))
screen = bpy.context.active_object
screen.name = "Screen"
screen.scale = (1.1, 0.02, 0.62)
tv_collection.objects.link(screen)
bpy.context.collection.objects.unlink(screen)

# 创建机身
bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, location=(0, 0.05, 0.35))
body = bpy.context.active_object
body.name = "Body"
body.scale = (1.2, 0.08, 0.7)
tv_collection.objects.link(body)
bpy.context.collection.objects.unlink(body)

# 创建底座支撑柱
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.3, enter_editmode=False, location=(0, 0, 0.15))
stand = bpy.context.active_object
stand.name = "Stand"
tv_collection.objects.link(stand)
bpy.context.collection.objects.unlink(stand)

# 创建底座底板
bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, location=(0, 0, 0.01))
base = bpy.context.active_object
base.name = "Base"
base.scale = (0.6, 0.3, 0.02)
tv_collection.objects.link(base)
bpy.context.collection.objects.unlink(base)

# 创建材质
material = bpy.data.materials.new(name="TV_Material")
material.use_nodes = True
material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.1, 0.1, 0.1, 1)  # 深灰色

# 应用材质到所有对象
for obj in tv_collection.objects:
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

bpy.ops.object.select_all(action='DESELECT')