"""
This module implements a conversation history management system for Blender.
It provides functionality to store, retrieve, and display conversation messages.
"""

import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy.types import PropertyGroup, Operator, Panel

class Message(PropertyGroup):
    """
    Represents a single message in the conversation.
    """
    role: StringProperty(name="Role", description="The role of the message sender (e.g., 'user' or 'assistant')")
    content: StringProperty(name="Content", description="The content of the message")

class ConversationManager(PropertyGroup):
    """
    Manages the conversation history, including adding, retrieving, and clearing messages.
    """
    messages: CollectionProperty(type=Message, description="Collection of messages in the conversation")

    def add_message(self, role, content):
        """
        Adds a new message to the conversation history.

        Args:
            role (str): The role of the message sender.
            content (str): The content of the message.
        """
        message = self.messages.add()
        message.role = role
        message.content = content

    def get_conversation_history(self):
        """
        Retrieves the entire conversation history.

        Returns:
            list: A list of dictionaries containing role and content for each message.
        """
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def clear_history(self):
        """
        Clears the entire conversation history.
        """
        self.messages.clear()

class CONVERSATION_OT_print_all(Operator):
    """
    Operator to print all messages in the conversation history.
    """
    bl_idname = "conversation.print_all"
    bl_label = "Print All Messages"
    bl_description = "Print all messages in the conversation history"

    def execute(self, context):
        conversation_manager = context.scene.conversation_manager
        history = conversation_manager.get_conversation_history()
        for msg in history:
            print(f"{msg['role']}: {msg['content']}")
        self.report({"INFO"}, f"Printed {len(history)} messages")
        return {"FINISHED"}

class CONVERSATION_OT_print_latest(Operator):
    """
    Operator to print the latest two messages in the conversation history.
    """
    bl_idname = "conversation.print_latest"
    bl_label = "Print Latest Messages"
    bl_description = "Print the latest two messages in the conversation history"

    def execute(self, context):
        conversation_manager = context.scene.conversation_manager
        history = conversation_manager.get_conversation_history()
        latest = history[-2:] if len(history) >= 2 else history
        for msg in latest:
            print(f"{msg['role']}: {msg['content']}")
        self.report({"INFO"}, f"Printed {len(latest)} messages")
        return {"FINISHED"}

class CONVERSATION_PT_panel(Panel):
    """
    Panel for displaying conversation history controls in the Blender UI.
    """
    bl_label = "Conversation History"
    bl_idname = "CONVERSATION_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        """
        Draws the panel layout in the Blender UI.

        Args:
            context: Blender context
        """
        layout = self.layout
        layout.operator("conversation.print_all")
        layout.operator("conversation.print_latest")