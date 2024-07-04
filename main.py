import sys
import os
import bpy
import logging
import requests
from bpy.props import StringProperty, PointerProperty

# 确保项目根目录在Python的模块搜索路径中
project_path = os.path.abspath(os.path.dirname(__file__))
if project_path not in sys.path:
    sys.path.append(project_path)

from gpt_module import (
    OBJECT_OT_send_to_gpt, GPT_PT_panel, OBJECT_OT_send_screenshots_to_gpt, OBJECT_OT_analyze_screenshots
)
from model_viewer_module import (
    ApplyScale, ModelViewerPanel, SaveScreenshotOperator, update_model_dimensions
)
from rotation_module import (
    RotateObjectCW_X_Degree, RotateObjectCW_Y_Degree, RotateObjectCW_Z_Degree, RotateObjectCW_X, RotateObjectCW_Y, RotateObjectCW_Z, RotatePanel, MirrorObject_X, MirrorObject_Y, MirrorObject_Z
)
from location_module import (
    ResetObjectLocation, LocationPanel
)
from boolean_operations_module import (
    BooleanUnionOperator, BooleanDifferenceOperator, BooleanIntersectOperator, BooleanPanel
)
from geometry_module import (
    GeometryProperties, MoveGeometryWithoutAffectingOrigin, ResetGeometryToOrigin, GeometryPanel
)
from subdivision_decimate_module import (
    SubdivisionDecimateProperties, ApplySubdivisionSurface, ApplyDecimate, SubdivisionDecimatePanel
)
from align_module import (
    AlignProperties, SetAlignPointOperator, AlignObjectsOperator, AlignPanel
)
from claude_module import (
    OBJECT_OT_send_to_claude, OBJECT_OT_send_screenshots_to_claude, CLAUDE_PT_panel, OBJECT_OT_analyze_screenshots_claude
)
from LLM_common_utils import (
    Message, Properties
)
from llama_index_model_modification import (
    ModificationProperties, MODIFICATION_OT_query, MODIFICATION_OT_query_with_screenshots, MODIFICATION_PT_panel, initialize_modification_db, MODIFICATION_OT_query_and_generate
)
from llama_index_model_generation import (
    GenerationProperties, GENERATION_OT_query, GENERATION_OT_generate_model, GENERATION_PT_panel, initialize_generation_db
)

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

classes = (
    Message,
    Properties,
    OBJECT_OT_send_to_gpt,
    OBJECT_OT_analyze_screenshots,
    OBJECT_OT_send_screenshots_to_gpt,
    GPT_PT_panel,
    OBJECT_OT_send_to_claude,
    OBJECT_OT_analyze_screenshots_claude,
    OBJECT_OT_send_screenshots_to_claude,
    CLAUDE_PT_panel,
    ModificationProperties,
    MODIFICATION_OT_query,
    MODIFICATION_OT_query_with_screenshots,
    MODIFICATION_OT_query_and_generate,
    MODIFICATION_PT_panel,
    GenerationProperties,
    GENERATION_OT_query,
    GENERATION_OT_generate_model,
    GENERATION_PT_panel,
    RotateObjectCW_X,
    RotateObjectCW_Y,
    RotateObjectCW_Z,
    RotateObjectCW_X_Degree,
    RotateObjectCW_Y_Degree,
    RotateObjectCW_Z_Degree,
    RotatePanel,
    MirrorObject_X,
    MirrorObject_Y,
    MirrorObject_Z,
    ApplyScale,
    ModelViewerPanel,
    SaveScreenshotOperator,
    ResetObjectLocation,
    LocationPanel,
    BooleanUnionOperator,
    BooleanDifferenceOperator,
    BooleanIntersectOperator,
    BooleanPanel,
    GeometryProperties,
    MoveGeometryWithoutAffectingOrigin,
    ResetGeometryToOrigin,
    GeometryPanel,
    SubdivisionDecimateProperties,
    ApplySubdivisionSurface,
    ApplyDecimate,
    SubdivisionDecimatePanel,
    AlignProperties,
    SetAlignPointOperator,
    AlignObjectsOperator,
    AlignPanel
)

def register():
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
        bpy.types.Scene.gpt_tool = bpy.props.PointerProperty(type=Properties)
        bpy.types.Scene.claude_tool = bpy.props.PointerProperty(type=Properties)
        bpy.types.Scene.model_scale_percentage = bpy.props.FloatProperty(
            name="Model Scale Percentage",
            default=100.0,
            min=0.01,
            max=10000.0,
            update=update_model_dimensions
        )
        bpy.types.Scene.model_dimensions = bpy.props.StringProperty(
            name="Model Dimensions",
            default="0.00 x 0.00 x 0.00"
        )
        bpy.types.Scene.rotation_degree = bpy.props.FloatProperty(
            name="Rotation Degree",
            description="Degree of rotation",
            default=0.0
        )
        bpy.types.Scene.geometry_props = bpy.props.PointerProperty(type=GeometryProperties)
        bpy.types.Scene.subdivision_decimate_props = bpy.props.PointerProperty(type=SubdivisionDecimateProperties)
        bpy.types.Scene.align_props = bpy.props.PointerProperty(type=AlignProperties)
        bpy.types.Scene.align_point_set = bpy.props.IntProperty(default=1)
        bpy.types.Scene.modification_tool = bpy.props.PointerProperty(type=ModificationProperties)
        bpy.types.Scene.generation_tool = bpy.props.PointerProperty(type=GenerationProperties)
        
        initialize_modification_db()
        initialize_generation_db()
        
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
        if hasattr(bpy.types.Scene, "claude_tool"):
            del bpy.types.Scene.claude_tool
        if hasattr(bpy.types.Scene, "model_scale_percentage"):
            del bpy.types.Scene.model_scale_percentage
        if hasattr(bpy.types.Scene, "model_dimensions"):
            del bpy.types.Scene.model_dimensions
        if hasattr(bpy.types.Scene, "rotation_degree"):
            del bpy.types.Scene.rotation_degree
        if hasattr(bpy.types.Scene, "geometry_props"):
            del bpy.types.Scene.geometry_props
        if hasattr(bpy.types.Scene, "subdivision_decimate_props"):
            del bpy.types.Scene.subdivision_decimate_props
        if hasattr(bpy.types.Scene, "align_props"):
            del bpy.types.Scene.align_props
        if hasattr(bpy.types.Scene, "align_point_set"):
            del bpy.types.Scene.align_point_set
        if hasattr(bpy.types.Scene, "modification_tool"):
            del bpy.types.Scene.modification_tool
        if hasattr(bpy.types.Scene, "generation_tool"):
            del bpy.types.Scene.generation_tool
        
        logger.info("Unregistered all classes successfully.")
    except Exception as e:
        logger.error(f"Error unregistering classes: {e}")

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()