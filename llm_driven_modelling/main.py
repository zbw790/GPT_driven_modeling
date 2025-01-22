# main.py

import sys
import os
import bpy
import logging
from bpy.props import StringProperty, PointerProperty, FloatProperty, IntProperty

project_path = os.path.abspath(os.path.dirname(__file__))
if project_path not in sys.path:
    sys.path.append(project_path)

from llm_driven_modelling.llm.gpt_module import (
    OBJECT_OT_send_to_gpt,
    GPT_PT_panel,
    OBJECT_OT_send_screenshots_to_gpt,
    OBJECT_OT_analyze_screenshots,
)
from llm_driven_modelling.utils.model_viewer_module import (
    ApplyScale,
    ModelViewerPanel,
    SaveScreenshotOperator,
    update_model_dimensions,
)
from llm_driven_modelling.blender_operations.rotation_module import (
    RotateObjectCW_X_Degree,
    RotateObjectCW_Y_Degree,
    RotateObjectCW_Z_Degree,
    RotateObjectCW_X,
    RotateObjectCW_Y,
    RotateObjectCW_Z,
    RotatePanel,
    MirrorObject_X,
    MirrorObject_Y,
    MirrorObject_Z,
)
from llm_driven_modelling.blender_operations.location_module import (
    ResetObjectLocation,
    LocationPanel,
)
from llm_driven_modelling.blender_operations.boolean_operations_module import (
    BooleanUnionOperator,
    BooleanDifferenceOperator,
    BooleanIntersectOperator,
    BooleanPanel,
)
from llm_driven_modelling.blender_operations.geometry_module import (
    GeometryProperties,
    MoveGeometryWithoutAffectingOrigin,
    ResetGeometryToOrigin,
    GeometryPanel,
)
from llm_driven_modelling.blender_operations.subdivision_decimate_module import (
    SubdivisionDecimateProperties,
    ApplySubdivisionSurface,
    ApplyDecimate,
    SubdivisionDecimatePanel,
)
from llm_driven_modelling.blender_operations.align_module import (
    AlignProperties,
    SetAlignPointOperator,
    AlignObjectsOperator,
    AlignPanel,
)
from llm_driven_modelling.llm.claude_module import (
    OBJECT_OT_send_to_claude,
    OBJECT_OT_send_screenshots_to_claude,
    CLAUDE_PT_panel,
    OBJECT_OT_analyze_screenshots_claude,
)
from llm_driven_modelling.llm.conversation_manager import (
    Message,
    ConversationManager,
    CONVERSATION_OT_print_all,
    CONVERSATION_OT_print_latest,
    CONVERSATION_PT_panel,
)
from llm_driven_modelling.llama_index_library.llama_index_model_modification import (
    ModificationProperties,
    MODIFICATION_OT_query,
    MODIFICATION_OT_query_with_screenshots,
    MODIFICATION_PT_panel,
    initialize_modification_db,
    MODIFICATION_OT_query_and_generate,
)
from llm_driven_modelling.llama_index_library.llama_index_model_generation import (
    GenerationProperties,
    GENERATION_OT_query,
    GENERATION_OT_generate_model,
    GENERATION_PT_panel,
    initialize_generation_db,
)
from llm_driven_modelling.blender_operations.bevel_corners_module import (
    BevelEdgesOperator,
    OBJECT_PT_bevel_panel,
    BevelProperties,
)
from llm_driven_modelling.core.model_generation_main import (
    ModelGenerationProperties,
    MODEL_GENERATION_OT_generate,
    MODEL_GENERATION_PT_panel,
)
from llm_driven_modelling.llm.LLM_common_utils import LLMToolProperties
from llm_driven_modelling.llama_index_library.llama_index_component_library import (
    ComponentProperties,
    COMPONENT_OT_query,
    COMPONENT_OT_generate_component,
    COMPONENT_PT_panel,
    initialize_component_db,
)
from llm_driven_modelling.core.evaluators_module import (
    OBJECT_OT_evaluate_model,
    Evaluator_PT_panel,
)
from llm_driven_modelling.llama_index_library.llama_index_material_library import (
    MaterialProperties,
    MATERIAL_OT_query,
    MATERIAL_OT_generate_material,
    MATERIAL_PT_panel,
    initialize_material_db,
)
from llm_driven_modelling.llama_index_library.llama_index_style_library import (
    StyleProperties,
    STYLE_OT_query,
    STYLE_OT_apply_style,
    STYLE_PT_panel,
    initialize_style_db,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

classes = (
    LLMToolProperties,
    Message,
    ConversationManager,
    CONVERSATION_OT_print_all,
    CONVERSATION_OT_print_latest,
    CONVERSATION_PT_panel,
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
    ComponentProperties,
    COMPONENT_OT_query,
    COMPONENT_OT_generate_component,
    COMPONENT_PT_panel,
    MaterialProperties,
    MATERIAL_OT_query,
    MATERIAL_OT_generate_material,
    MATERIAL_PT_panel,
    StyleProperties,
    STYLE_OT_query,
    STYLE_OT_apply_style,
    STYLE_PT_panel,
    ModelGenerationProperties,
    MODEL_GENERATION_OT_generate,
    MODEL_GENERATION_PT_panel,
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
    AlignPanel,
    BevelEdgesOperator,
    OBJECT_PT_bevel_panel,
    BevelProperties,
    OBJECT_OT_evaluate_model,
    Evaluator_PT_panel,
)


def register():
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
        bpy.types.Scene.conversation_manager = PointerProperty(type=ConversationManager)
        bpy.types.Scene.model_scale_percentage = FloatProperty(
            name="Model Scale Percentage",
            default=100.0,
            min=0.01,
            max=10000.0,
            update=update_model_dimensions,
        )
        bpy.types.Scene.model_dimensions = StringProperty(
            name="Model Dimensions", default="0.00 x 0.00 x 0.00"
        )
        bpy.types.Scene.rotation_degree = FloatProperty(
            name="Rotation Degree", description="Degree of rotation", default=0.0
        )
        bpy.types.Scene.geometry_props = PointerProperty(type=GeometryProperties)
        bpy.types.Scene.subdivision_decimate_props = PointerProperty(
            type=SubdivisionDecimateProperties
        )
        bpy.types.Scene.align_props = PointerProperty(type=AlignProperties)
        bpy.types.Scene.align_point_set = IntProperty(default=1)
        bpy.types.Scene.modification_tool = PointerProperty(type=ModificationProperties)
        bpy.types.Scene.generation_tool = PointerProperty(type=GenerationProperties)
        bpy.types.Scene.bevel_properties = PointerProperty(type=BevelProperties)
        bpy.types.Scene.model_generation_tool = PointerProperty(
            type=ModelGenerationProperties
        )
        bpy.types.Scene.llm_tool = PointerProperty(type=LLMToolProperties)
        bpy.types.Scene.component_tool = PointerProperty(type=ComponentProperties)
        bpy.types.Scene.material_tool = PointerProperty(type=MaterialProperties)
        bpy.types.Scene.style_tool = PointerProperty(type=StyleProperties)

        initialize_modification_db()
        initialize_generation_db()
        initialize_component_db()
        initialize_material_db()
        initialize_style_db()

        logger.info("Registered all classes successfully.")
    except Exception as e:
        logger.error(f"Error registering classes: {e}")


def unregister():
    try:
        for cls in reversed(classes):
            if hasattr(bpy.types, cls.__name__):
                bpy.utils.unregister_class(cls)

        if hasattr(bpy.types.Scene, "conversation_manager"):
            del bpy.types.Scene.conversation_manager
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
        if hasattr(bpy.types.Scene, "bevel_properties"):
            del bpy.types.Scene.bevel_properties
        if hasattr(bpy.types.Scene, "model_generation_tool"):
            del bpy.types.Scene.model_generation_tool
        if hasattr(bpy.types.Scene, "llm_tool"):
            del bpy.types.Scene.llm_tool
        if hasattr(bpy.types.Scene, "component_tool"):
            del bpy.types.Scene.component_tool
        if hasattr(bpy.types.Scene, "material_tool"):
            del bpy.types.Scene.material_tool
        if hasattr(bpy.types.Scene, "style_tool"):
            del bpy.types.Scene.style_tool

        logger.info("Unregistered all classes successfully.")
    except Exception as e:
        logger.error(f"Error unregistering classes: {e}")


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
