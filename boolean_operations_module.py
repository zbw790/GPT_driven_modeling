import bpy
from bpy.types import Operator, Panel

class BooleanUnionOperator(Operator):
    bl_idname = "object.boolean_union"
    bl_label = "布尔联合"

    def execute(self, context):
        """
        布尔联合操作将选中的多个对象合并成一个对象。
        例如，选中两个立方体后执行此操作，将这两个立方体合并为一个。
        """
        objects = context.selected_objects
        if len(objects) < 2:
            self.report({'WARNING'}, "请至少选择两个对象进行布尔联合操作")
            return {'CANCELLED'}

        base_obj = objects[0]
        bpy.context.view_layer.objects.active = base_obj

        for obj in objects[1:]:
            mod = base_obj.modifiers.new(name="Boolean", type='BOOLEAN')
            mod.operation = 'UNION'
            mod.object = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(obj)

        return {'FINISHED'}

class BooleanDifferenceOperator(Operator):
    bl_idname = "object.boolean_difference"
    bl_label = "布尔差集"

    def execute(self, context):
        """
        布尔差集操作将从基对象中减去切割对象部分。
        例如，选中一个立方体和一个球体，执行此操作，将从立方体中减去球体的部分。
        """
        objects = context.selected_objects
        if len(objects) != 2:
            self.report({'WARNING'}, "请确保选中两个对象进行布尔差集操作")
            return {'CANCELLED'}

        base_obj = bpy.context.view_layer.objects.active
        cutter_obj = [obj for obj in objects if obj != base_obj][0]

        mod = base_obj.modifiers.new(name="Boolean", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cutter_obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter_obj)

        return {'FINISHED'}

class BooleanIntersectOperator(Operator):
    bl_idname = "object.boolean_intersect"
    bl_label = "布尔交集"

    def execute(self, context):
        """
        布尔交集操作将保留选中对象的重叠部分，并删除其他部分。
        例如，选中两个相交的球体，执行此操作，将只保留球体的相交部分。
        """
        objects = context.selected_objects
        if len(objects) < 2:
            self.report({'WARNING'}, "请至少选择两个对象进行布尔交集操作")
            return {'CANCELLED'}

        base_obj = objects[0]
        bpy.context.view_layer.objects.active = base_obj

        for obj in objects[1:]:
            mod = base_obj.modifiers.new(name="Boolean", type='BOOLEAN')
            mod.operation = 'INTERSECT'
            mod.object = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(obj)

        return {'FINISHED'}

class BooleanPanel(Panel):
    bl_label = "布尔运算"
    bl_idname = "OBJECT_PT_boolean_operations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.boolean_union", text="布尔联合")
        layout.operator("object.boolean_difference", text="布尔差集")
        layout.operator("object.boolean_intersect", text="布尔交集")
