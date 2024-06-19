import sys
import os
import bpy
import logging

# 确保项目根目录在Python的模块搜索路径中
project_path = os.path.abspath(os.path.dirname(__file__))
if project_path not in sys.path:
    sys.path.append(project_path)

from gpt_module import (
    GPTMessage, GPTProperties, initialize_conversation, generate_text, OBJECT_OT_send_to_gpt, GPT_PT_panel
)
from model_viewer_module import (
    ApplyScale, ModelViewerPanel, update_model_dimensions
)
from rotation_module import (
    RotateObjectCW_X_Degree, RotateObjectCW_Y_Degree, RotateObjectCW_Z_Degree, RotateObjectCW_X, RotateObjectCW_Y, RotateObjectCW_Z, RotatePanel
)
from location_module import (
    ResetObjectLocation, LocationPanel
)

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

classes = (
    GPTMessage,
    GPTProperties,
    OBJECT_OT_send_to_gpt,
    GPT_PT_panel,
    RotateObjectCW_X,
    RotateObjectCW_Y,
    RotateObjectCW_Z,
    RotateObjectCW_X_Degree,
    RotateObjectCW_Y_Degree,
    RotateObjectCW_Z_Degree,
    RotatePanel,
    ApplyScale,
    ModelViewerPanel,
    ResetObjectLocation,
    LocationPanel
)

def register():
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
        bpy.types.Scene.gpt_tool = bpy.props.PointerProperty(type=GPTProperties)
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
        bpy.types.Scene.rotation_degree = bpy.props.FloatProperty(
            name="Rotation Degree",
            description="Degree of rotation",
            default=0.0
        )
        logger.info("Registered all classes successfully.")
    except Exception as e:
        logger.error(f"Error registering classes: {e}")

def unregister():
    try:
        for cls in classes:
            if hasattr(bpy.types, cls.__name__):
                bpy.utils.unregister_class(cls)
        if hasattr(bpy.types.Scene, "gpt_tool"):
            del bpy.types.Scene.gpt_tool
        if hasattr(bpy.types.Scene, "model_scale_percentage"):
            del bpy.types.Scene.model_scale_percentage
        if hasattr(bpy.types.Scene, "model_dimensions"):
            del bpy.types.Scene.model_dimensions
        if hasattr(bpy.types.Scene, "rotation_degree"):
            del bpy.types.Scene.rotation_degree
        logger.info("Unregistered all classes successfully.")
    except Exception as e:
        logger.error(f"Error unregistering classes: {e}")

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
