bl_info = {
    "name": "Text Input Test",
    "blender": (2, 80, 0),
    "category": "3D View",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Tool Shelf",
    "description": "Text Input with Send Button",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

import bpy

class MyProperties(bpy.types.PropertyGroup):
    my_string : bpy.props.StringProperty(name="Input Text", description="Enter some text here")


class OBJECT_OT_send_button(bpy.types.Operator):
    bl_idname = "object.send_button"
    bl_label = "Send"

    def execute(self, context):
        scn = context.scene
        print(scn.my_tool.my_string)
        return {'FINISHED'}


class TEXT_PT_panel(bpy.types.Panel):
    bl_label = "Text Input Panel"
    bl_idname = "TEXT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn.my_tool, "my_string")
        layout.operator(OBJECT_OT_send_button.bl_idname)


classes = (
    MyProperties,
    OBJECT_OT_send_button,
    TEXT_PT_panel,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()