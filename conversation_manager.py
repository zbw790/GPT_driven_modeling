import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy.types import PropertyGroup, Operator, Panel

class Message(PropertyGroup):
    role: StringProperty(name="Role")
    content: StringProperty(name="Content")

class ConversationManager(PropertyGroup):
    messages: CollectionProperty(type=Message)

    def add_message(self, role, content):
        message = self.messages.add()
        message.role = role
        message.content = content

    def get_conversation_history(self):
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

    def clear_history(self):
        self.messages.clear()

class CONVERSATION_OT_print_all(Operator):
    bl_idname = "conversation.print_all"
    bl_label = "Print All Messages"
    bl_description = "Print all messages in the conversation history"

    def execute(self, context):
        conversation_manager = context.scene.conversation_manager
        history = conversation_manager.get_conversation_history()
        for msg in history:
            print(f"{msg['role']}: {msg['content']}")
        self.report({'INFO'}, f"Printed {len(history)} messages")
        return {'FINISHED'}

class CONVERSATION_OT_print_latest(Operator):
    bl_idname = "conversation.print_latest"
    bl_label = "Print Latest Messages"
    bl_description = "Print the latest two messages in the conversation history"

    def execute(self, context):
        conversation_manager = context.scene.conversation_manager
        history = conversation_manager.get_conversation_history()
        latest = history[-2:] if len(history) >= 2 else history
        for msg in latest:
            print(f"{msg['role']}: {msg['content']}")
        self.report({'INFO'}, f"Printed {len(latest)} messages")
        return {'FINISHED'}

class CONVERSATION_PT_panel(Panel):
    bl_label = "Conversation History"
    bl_idname = "CONVERSATION_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("conversation.print_all")
        layout.operator("conversation.print_latest")
