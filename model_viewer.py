
import bpy
import os
import time
import math
import csv 
import mathutils
bl_info = {
    "name": "Model Viewer",
    "author": "Lockliu",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > UI > Item",
    "description": "A simple model viewer for importing and exporting 3D models.",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

# 全局变量,用于记录当前路径状态
current_path = ""
# 返回上一级文件夹的图标
ICON_BACK = 'BACK'
# 文件夹的图标
ICON_FOLDER = 'FILE_FOLDER'
# 支持的文件类型和对应的导入/导出函数及图标
FILE_TYPES = {
    ".fbx": {
        "import_func": lambda filepath: bpy.ops.import_scene.fbx(filepath=filepath, axis_forward='-Z', axis_up='Y'),
        "export_func": lambda filepath: bpy.ops.export_scene.fbx(filepath=filepath, axis_forward="-Z", axis_up="Y",object_types={"MESH"},path_mode="COPY",embed_textures=True),
        "icon": 'META_CUBE'
    },
    ".obj": {
        "import_func": lambda filepath: bpy.ops.import_scene.obj(filepath=filepath),
        "export_func": lambda filepath: bpy.ops.export_scene.obj(filepath=filepath),
        "icon": 'MESH_CUBE'
    },
    ".glb": {
        "import_func": lambda filepath: bpy.ops.import_scene.gltf(filepath=filepath),
        "export_func": lambda filepath: bpy.ops.export_scene.gltf(filepath=filepath),
        "icon": 'MESH_MONKEY'
    },
    ".gltf": {
        "import_func": lambda filepath: bpy.ops.import_scene.gltf(filepath=filepath),
        "export_func": lambda filepath: bpy.ops.export_scene.gltf(filepath=filepath),
        "icon": 'SCENE_DATA'
    }
}
class RenderAllItems(bpy.types.Operator):
    bl_idname = "model_viewer.render_all_items"
    bl_label = "Render All Items"

    def execute(self, context):
        scene = context.scene
        original_index = scene.model_viewer_index

        for i, item in enumerate(scene.model_viewer_items):
            if not item.is_folder:
                scene.model_viewer_index = i
                execute_action(context)

                # 渲染当前场景并保存为PNG图片
                render_and_save_image(context, item.name)

        scene.model_viewer_index = original_index
        return {'FINISHED'}
class ExportToCSV(bpy.types.Operator):
    bl_idname = "model_viewer.export_to_csv"
    bl_label = "Export to CSV"

    def execute(self, context):
        scene = context.scene
        csv_file_path = scene.csv_file_path

        if not csv_file_path:
            csv_file_path = "./temp.csv"  # 默认创建"./temp.csv"文件

        with open(csv_file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['id', 'name_en', 'bbx', 'vertex_polygon_count', 'caption', 'class_cn'])

            for i, item in enumerate(scene.model_viewer_items):
                if not item.is_folder:
                    file_path = os.path.join(current_path, item.name)
                    file_ext = os.path.splitext(item.name)[1].lower()
                    if file_ext in FILE_TYPES:
                        delete_all()
                        FILE_TYPES[file_ext]["import_func"](file_path)
                        merge_selected_meshes()

                        if bpy.context.selected_objects:
                            obj = bpy.context.selected_objects[0]
                            dimensions = obj.dimensions
                            vertex_count = len(obj.data.vertices)
                            polygon_count = len(obj.data.polygons)

                            csv_writer.writerow([
                                i,
                                f"{os.path.splitext(item.name)[0]}",
                                f"{dimensions.x:.3f},{dimensions.y:.3f},{dimensions.z:.3f}",
                                f"{vertex_count},{polygon_count}"
                            ])

        self.report({'INFO'}, "Export to CSV completed.")
        return {'FINISHED'}
def render_and_save_image(context, item_name):
    scene = context.scene
    render_path = os.path.join(current_path, f"{os.path.splitext(item_name)[0]}.png")

    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
def merge_selected_meshes():
    # 获取所有选中的网格对象
    selected_meshes = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

    if len(selected_meshes) > 1:
        # 设置活动对象为第一个选中的网格
        bpy.context.view_layer.objects.active = selected_meshes[0]

        # 合并网格
        bpy.ops.object.join()
        bpy.context.view_layer.objects.active = selected_meshes[0]

def move_camera_backwards_by_percentage(percentage):
    # 获取当前场景和相机
    scene = bpy.context.scene
    camera = scene.camera

    # 获取选中物体
    selected_obj = bpy.context.selected_objects[0]

    # 计算物体的包围盒半径（假设bbx是指包围盒的最大尺寸）
    bbx_radius = max(selected_obj.dimensions) / 2
#    bbx_radius_min =  min(selected_obj.dimensions) / 2
    print(selected_obj,bbx_radius)
    # 计算向后移动的距离
    move_distance = bbx_radius * percentage

    # 获取相机的方向
    camera_direction = camera.matrix_world.to_quaternion() @ mathutils.Vector((0.0, 0.0, -1.0))

    # 计算新的相机位置
    # camera.location += camera_direction * move_distance
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs['Color'].default_value = (1, 1, 1, 1)
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs['Strength'].default_value = 1
    camera.data.clip_start = bbx_radius * 0.1
    camera.data.clip_end = bbx_radius * 100
    camera.data.lens = 100

def delete_all():
#    bpy.ops.object.select_all(action='SELECT')
#    bpy.ops.object.delete(use_global=False)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material, do_unlink=True)
    for texture in bpy.data.textures:
        bpy.data.textures.remove(texture, do_unlink=True)
    for image in bpy.data.images:
        bpy.data.images.remove(image, do_unlink=True)
#    for collection in bpy.data.collections:
#        bpy.data.collections.remove(collection, do_unlink=True)
#    for light in bpy.data.lights:
#        bpy.data.lights.remove(light, do_unlink=True)
    for curve in bpy.data.curves:
        bpy.data.curves.remove(curve, do_unlink=True)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for node_group in bpy.data.node_groups:
        bpy.data.node_groups.remove(node_group, do_unlink=True)
    for particle_settings in bpy.data.particles:
        bpy.data.particles.remove(particle_settings, do_unlink=True)
#    for world in bpy.data.worlds:
#        bpy.data.worlds.remove(world, do_unlink=True)

def reset_camera(objects, camera):
    # 将视图切换到相机视图
    bpy.context.scene.camera = camera
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            # 在相机视图下锁定到视图
            area.spaces[0].lock_camera = True
            break

    # 将相机视图对准所选物体的中心
    bpy.ops.view3d.camera_to_view_selected()
    move_camera_backwards_by_percentage(-0.1)

class ModelViewerPanel(bpy.types.Panel):
    bl_label = "Model Viewer"
    bl_idname = "OBJECT_PT_model_viewer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.operator("model_viewer.delete_current_asset", text="Delete")
        row.operator("model_viewer.render_all_items", text="Render All Items")
        row = layout.row()
        row.prop(scene, "model_viewer_path", text="")

        row = layout.row()
        row.prop(scene, "csv_file_path", text="CSV File")
        row.operator("model_viewer.export_to_csv", text="Export to CSV")

        layout.template_list("MODEL_VIEWER_UL_items", "", scene, "model_viewer_items", scene, "model_viewer_index")

        # 添加按钮
        if scene.model_viewer_items:
            selected_item = scene.model_viewer_items[scene.model_viewer_index]
            if not selected_item.is_folder:
                row = layout.row()
                row.operator("model_viewer.rotate_object_cw_z", text="顺时针90 (Z)")
                row.operator("model_viewer.rotate_object_cw_x", text="顺时针90 (X)")
                row.operator("model_viewer.rotate_object_cw_y", text="顺时针90 (Y)")
                layout.operator("model_viewer.reset_object_location", text="重置中心")    #重置，底面中心-零点

                row = layout.row()
                row.prop(scene, "model_scale_percentage", text="Scale (%)")

                row = layout.row()
                row.label(text=f"Dimensions: {scene.model_dimensions}")

                row = layout.row()
                row.operator("model_viewer.apply_scale", text="Apply Scale")
                save_button = layout.operator("model_viewer.save_current_asset", text="保存")
                save_button.filepath = os.path.join(current_path, selected_item.name)
            else:
                layout.operator("model_viewer.save_current_asset", text="Save", emboss=False).filepath = ""

def update_list_items(context):
    global current_path
    scene = context.scene
    scene.model_viewer_items.clear()
    if current_path:
        # 添加返回上一级文件夹的item
        item = scene.model_viewer_items.add()
        item.name = ".."
        item.is_folder = True
        # 遍历当前路径下的文件和文件夹
        for entry in os.listdir(current_path):
            if os.path.isdir(os.path.join(current_path, entry)) or os.path.splitext(entry)[1].lower() in FILE_TYPES:
                item = scene.model_viewer_items.add()
                item.name = entry
                item.is_folder = os.path.isdir(os.path.join(current_path, entry))

def on_path_updated(self, context):
    global current_path
    new_path = self.model_viewer_path
    if new_path != current_path:
        if os.path.exists(new_path):
            current_path = new_path
            update_list_items(context)
        else:
            context.scene.model_viewer_items.clear()
    

class MODEL_VIEWER_UL_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item.name == "..":
            layout.label(text=item.name, icon=ICON_BACK)
        elif item.is_folder:
            layout.label(text=item.name, icon=ICON_FOLDER)
        else:
            file_ext = os.path.splitext(item.name)[1].lower()
            if file_ext in FILE_TYPES:
                layout.label(text=item.name, icon=FILE_TYPES[file_ext]["icon"])

class ListItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="Untitled")
    is_folder: bpy.props.BoolProperty(name="Is Folder", default=False)

def execute_action(context):
    global current_path
    scene = context.scene
    if scene.model_viewer_items:
        selected_item = scene.model_viewer_items[scene.model_viewer_index]
        if selected_item.is_folder:
            if selected_item.name == "..":
                # 返回上一级文件夹
                current_path = os.path.abspath(os.path.join(current_path, ".."))
            else:
                # 进入选中的文件夹
                current_path = os.path.join(current_path, selected_item.name)
            update_list_items(context)
            scene.model_viewer_path = current_path
        else:
            # 导入选中的文件
            file_path = os.path.join(current_path, selected_item.name)
            file_ext = os.path.splitext(selected_item.name)[1].lower()
            if file_ext in FILE_TYPES:
                delete_all()
                FILE_TYPES[file_ext]["import_func"](file_path)
                merge_selected_meshes()
                # 获取导入的物体
                imported_objects = bpy.context.selected_objects

                # 创建相机
                # camera_data = bpy.data.cameras.new(name="Camera")
                camera_object = bpy.data.objects["Camera"]

                bpy.context.scene.render.engine = 'CYCLES'

                bpy.context.scene.render.film_transparent = True

                bpy.context.scene.render.resolution_x = 500
                bpy.context.scene.render.resolution_y = 500
                reset_camera(imported_objects, camera_object)

                imported_objects = bpy.context.selected_objects

                if imported_objects:
                    # 获取模型的尺寸
                    dimensions = imported_objects[0].dimensions
                    context.scene.model_dimensions = f"{dimensions.x:.2f} x {dimensions.y:.2f} x {dimensions.z:.2f}"

class ModalTimerOperator(bpy.types.Operator):
    """Operator which runs itself from a timer"""
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Modal Timer Operator"
    last_click = time.time()
    click = False

    def modal(self, context, event):
        loop_time = time.time()
        delta = loop_time - self.last_click
        if delta > 0.3:
            self.click = False
        # if event.type in {'RET'}:
        #     if event.value in {'RELEASE'}:
        #         execute_action(context)
        if event.type in {'LEFTMOUSE'}:
            if event.value in {'RELEASE'}:
                if not self.click:
                    self.click = True
                    self.last_click = time.time()
                elif delta < 0.3 and self.click:
                    execute_action(context)
                    self.click = False
        if event.type in {'ESC'}:
            self.cancel(context)
        if event.type in {'TIMER'}:
            pass
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        self.last_click = time.time()
        self.execute(context)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)



class SaveCurrentAsset(bpy.types.Operator):
    bl_idname = "model_viewer.save_current_asset"
    bl_label = "Save Current Asset"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return bool(context.scene.model_viewer_items and not context.scene.model_viewer_items[context.scene.model_viewer_index].is_folder)

    def execute(self, context):
        if self.filepath:
            for obj in bpy.context.selected_objects:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            file_ext = os.path.splitext(self.filepath)[1].lower()
            if file_ext in FILE_TYPES:
                reset_mesh_origin_to_bbx_center()
                FILE_TYPES[file_ext]["export_func"](self.filepath)

        return {'FINISHED'}



def save_current_asset(context):
    scene = context.scene
    if scene.model_viewer_items:
        selected_item = scene.model_viewer_items[scene.model_viewer_index]
        if not selected_item.is_folder:
            file_path = os.path.join(current_path, selected_item.name)
            file_ext = os.path.splitext(selected_item.name)[1].lower()
            if file_ext in FILE_TYPES:
                FILE_TYPES[file_ext]["export_func"](file_path)

class RotateObjectCW_Z(bpy.types.Operator):
    bl_idname = "model_viewer.rotate_object_cw_z"
    bl_label = "Rotate Object CW (Z)"

    def execute(self, context):
        for obj in context.selected_objects:
            obj.rotation_euler.z += math.radians(90)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

class RotateObjectCW_X(bpy.types.Operator):
    bl_idname = "model_viewer.rotate_object_cw_x"
    bl_label = "Rotate Object CW (X)"

    def execute(self, context):
        for obj in context.selected_objects:
            obj.rotation_euler.x += math.radians(90)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

class RotateObjectCW_Y(bpy.types.Operator):
    bl_idname = "model_viewer.rotate_object_cw_y"
    bl_label = "Rotate Object CW (Y)"

    def execute(self, context):
        for obj in context.selected_objects:
            obj.rotation_euler.y += math.radians(90)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}



def reset_mesh_origin_to_bbx_center():
    # 获取所有选中的物体
    selected_objects = bpy.context.selected_objects

    for obj in selected_objects:
        # 设定当前物体为活动物体
        bpy.context.view_layer.objects.active = obj

        # 清空物体的位置
        bpy.ops.object.location_clear()

        # 计算物体的包围盒中心点
        bbx_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        bbx_center = sum(bbx_corners, mathutils.Vector()) / 8

        # 设置CURSOR到包围盒中心点
        bpy.context.scene.cursor.location = bbx_center

        # 设置物体原点到CURSOR
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')

        # 把网格的中心点移动到原点，但不移动网格
        obj.location = (0, 0, 0)

    # 重置CURSOR
    bpy.context.scene.cursor.location = (0, 0, 0)

class DeleteCurrentAsset(bpy.types.Operator):
    bl_idname = "model_viewer.delete_current_asset"
    bl_label = "Delete Current Asset"

    def execute(self, context):
        scene = context.scene
        if scene.model_viewer_items:
            selected_item = scene.model_viewer_items[scene.model_viewer_index]
            if not selected_item.is_folder:
                file_path = os.path.join(current_path, selected_item.name)
                try:
                    os.remove(file_path)
                    update_list_items(context)
                    if scene.model_viewer_index < len(scene.model_viewer_items) - 1:
                        scene.model_viewer_index = scene.model_viewer_index
                    else:
                        scene.model_viewer_index = max(0, len(scene.model_viewer_items) - 1)
                    execute_action(context)  # 直接调用函数
                except Exception as e:
                    self.report({'ERROR'}, f"Error deleting file: {str(e)}")
        return {'FINISHED'}


class ResetObjectLocation(bpy.types.Operator):
    bl_idname = "model_viewer.reset_object_location"
    bl_label = "Reset Object Location"

    def execute(self, context):
        # 调用函数
        reset_mesh_origin_to_bbx_center()
        return {'FINISHED'}
class ApplyScale(bpy.types.Operator):
    bl_idname = "model_viewer.apply_scale"
    bl_label = "Apply Scale"

    def execute(self, context):
        scale_percentage = context.scene.model_scale_percentage
        scale_factor = scale_percentage / 100

        for obj in context.selected_objects:
            obj.scale = (scale_factor, scale_factor, scale_factor)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # 更新显示的模型尺寸
        if context.selected_objects:
            dimensions = context.selected_objects[0].dimensions
            context.scene.model_dimensions = f"{dimensions.x:.2f} x {dimensions.y:.2f} x {dimensions.z:.2f}"

        # 重置 Scale % 的值为 100
        context.scene.model_scale_percentage = 100

        return {'FINISHED'}

def update_model_dimensions(self, context):
    scale_percentage = context.scene.model_scale_percentage
    scale_factor = scale_percentage / 100

    for obj in context.selected_objects:
        dimensions = obj.dimensions
        scaled_dimensions = dimensions * scale_factor
        context.scene.model_dimensions = f"{scaled_dimensions.x:.2f} x {scaled_dimensions.y:.2f} x {scaled_dimensions.z:.2f}"
def register():
    bpy.utils.register_class(ModelViewerPanel)
    bpy.utils.register_class(MODEL_VIEWER_UL_items)
    bpy.utils.register_class(ListItem)
    bpy.utils.register_class(ModalTimerOperator)
    bpy.utils.register_class(SaveCurrentAsset)
    bpy.utils.register_class(RotateObjectCW_Z)
    bpy.utils.register_class(RotateObjectCW_X)
    bpy.utils.register_class(RotateObjectCW_Y)
    bpy.utils.register_class(ResetObjectLocation)
    bpy.utils.register_class(DeleteCurrentAsset)
    bpy.utils.register_class(RenderAllItems)
    bpy.utils.register_class(ExportToCSV)
    bpy.types.Scene.csv_file_path = bpy.props.StringProperty(
        name="CSV File Path",
        subtype='FILE_PATH'
    )
    bpy.types.Scene.model_viewer_path = bpy.props.StringProperty(
        name="Path",
        subtype='DIR_PATH',
        update=on_path_updated
    )
    bpy.types.Scene.excel_file_path = bpy.props.StringProperty(
        name="Excel File Path",
        subtype='FILE_PATH'
    )
    bpy.types.Scene.model_viewer_items = bpy.props.CollectionProperty(type=ListItem)
    bpy.types.Scene.model_viewer_index = bpy.props.IntProperty()

    bpy.ops.wm.modal_timer_operator()
    bpy.utils.register_class(ApplyScale)

    # ...

    bpy.types.Scene.model_scale_percentage = bpy.props.FloatProperty(
        name="Model Scale Percentage",
        default=100.0,
        min=0.01,
        max=10000.0,
        update=update_model_dimensions
    )
    bpy.types.Scene.model_dimensions = bpy.props.StringProperty(
        name="Model Dimensions",
        default=""
    )
def unregister():
    bpy.utils.unregister_class(ModelViewerPanel)
    bpy.utils.unregister_class(MODEL_VIEWER_UL_items)
    bpy.utils.unregister_class(ListItem)
    bpy.utils.unregister_class(DeleteCurrentAsset)
    bpy.utils.unregister_class(ModalTimerOperator)
    bpy.utils.unregister_class(SaveCurrentAsset)
    bpy.utils.unregister_class(RotateObjectCW_Z)
    bpy.utils.unregister_class(RotateObjectCW_X)
    bpy.utils.unregister_class(RotateObjectCW_Y)
    bpy.utils.unregister_class(ResetObjectLocation)
    bpy.utils.unregister_class(ApplyScale)
    bpy.utils.unregister_class(RenderAllItems)
    bpy.utils.unregister_class(ExportToCSV)
    # ...

    del bpy.types.Scene.csv_file_path
    del bpy.types.Scene.model_scale_percentage
    del bpy.types.Scene.model_dimensions
    del bpy.types.Scene.model_viewer_path
    del bpy.types.Scene.excel_file_path
    del bpy.types.Scene.model_viewer_items
    del bpy.types.Scene.model_viewer_index

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()