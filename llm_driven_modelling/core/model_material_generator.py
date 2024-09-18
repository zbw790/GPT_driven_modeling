# model_material_generator.py

"""
This module provides functionality for generating and applying materials to 3D models in Blender.
It uses AI-driven analysis to determine material requirements and generate appropriate Blender Python code.
"""

import bpy
import json
import os
from llm_driven_modelling.llm.claude_module import (
    generate_text_with_claude,
    analyze_screenshots_with_claude,
)
from llm_driven_modelling.llm.LLM_common_utils import (
    execute_blender_command,
    get_scene_info,
    format_scene_info,
)
from llm_driven_modelling.utils.logger_module import setup_logger
from llm_driven_modelling.llm.gpt_module import (
    generate_text_with_context,
    analyze_screenshots_with_gpt4,
)
from llm_driven_modelling.utils.model_viewer_module import (
    save_screenshots,
    save_screenshots_to_path,
)
from llm_driven_modelling.llama_index_library.llama_index_material_library import (
    query_material_documentation,
)
from llm_driven_modelling.core.model_generation_utils import update_blender_view

# Set up logger
logger = setup_logger("model_generation")


def query_material_docs(material_requirements):
    """
    Query material documentation based on material requirements.

    Args:
        material_requirements (dict): A dictionary of material types and their requirements.

    Returns:
        dict: A dictionary of material types and their corresponding documentation.
    """
    material_docs = {}
    for material_type in material_requirements.keys():
        query = f"Material type: {material_type}"
        results = query_material_documentation(
            bpy.types.Scene.material_query_engine, query
        )
        material_docs[material_type] = results
    return material_docs


def apply_materials(context, user_input, rewritten_input, scene_description, log_dir):
    """
    Apply materials to objects in the Blender scene based on user input and scene analysis.

    Args:
        context (bpy.types.Context): The current Blender context.
        user_input (str): The original user input.
        rewritten_input (str): The rewritten user input.
        scene_description (dict): A description of the scene.
        log_dir (str): The directory to save logs and screenshots.
    """
    try:
        # Get scene information
        scene_info = get_scene_info()
        formatted_scene_info = format_scene_info(scene_info)

        # Step 1: Analyze scene and determine required materials
        material_requirements = analyze_scene_for_materials(
            user_input, rewritten_input, formatted_scene_info, scene_description
        )
        logger.info(f"Material requirements: {material_requirements}")

        # Step 2: Query relevant material documentation
        material_docs = query_material_docs(material_requirements)
        logger.info(f"Material documentation: {material_docs}")

        # Step 3: Generate and apply materials
        generate_and_apply_materials(
            context,
            user_input,
            rewritten_input,
            formatted_scene_info,
            scene_description,
            material_requirements,
            material_docs,
            log_dir,
        )

    except Exception as e:
        logger.error(f"An error occurred while applying materials: {str(e)}")


def analyze_scene_for_materials(
    user_input, rewritten_input, formatted_scene_info, scene_description
):
    """
    Analyze the scene and determine required materials based on user input and scene information.

    Args:
        user_input (str): The original user input.
        rewritten_input (str): The rewritten user input.
        formatted_scene_info (str): Formatted scene information.
        scene_description (dict): A description of the scene.

    Returns:
        dict: A dictionary of material types and objects requiring those materials.
    """
    prompt = f"""
        Context:
        You are an AI assistant specialized in analyzing 3D scenes and determining required materials. Based on the provided scene information and model description, identify the needed material types.

        Original user input: {user_input}
        Rewritten requirements: {rewritten_input}
        Scene information: {formatted_scene_info}
        Model description: {json.dumps(scene_description, ensure_ascii=False, indent=2)}

        Task:
        Analyze each object in the scene and determine the required material types. Consider the object's name, shape, and possible use. Group objects with the same material type.

        Output:
        Provide a JSON object with material types as keys and lists of objects requiring that material as values. Note that some materials are built-in to the Blender scene, such as Camera, and these items do not need materials added:
        {{
            "wood": ["Table_Top", "Chair_Seat"],
            "metal": ["Table_Leg", "Chair_Frame"],
            "fabric": ["Chair_Cushion"],
            "glass": ["Lamp_Shade"]
        }}

        Provide only the JSON object, without any additional explanation.
        """
    response = generate_text_with_context(prompt)
    return json.loads(response)


def generate_and_apply_materials(
    context,
    user_input,
    rewritten_input,
    formatted_scene_info,
    scene_description,
    material_requirements,
    material_docs,
    log_dir,
):
    """
    Generate and apply materials to objects in the Blender scene.

    Args:
        context (bpy.types.Context): The current Blender context.
        user_input (str): The original user input.
        rewritten_input (str): The rewritten user input.
        formatted_scene_info (str): Formatted scene information.
        scene_description (dict): A description of the scene.
        material_requirements (dict): A dictionary of material types and objects requiring those materials.
        material_docs (dict): A dictionary of material types and their corresponding documentation.
        log_dir (str): The directory to save logs and screenshots.
    """
    logger.info(f"Material requirements: {material_requirements}")
    logger.info(f"Material documentation: {material_docs}")
    prompt = f"""
        Context:
        You are an AI assistant specialized in generating materials for 3D models. Based on the provided material requirements and related documentation, generate Blender Python code to create and apply materials.
        Note that you should only generate materials and not modify any models in the scene.

        Note:
        1. Do not use "Subsurface", "Sheen", "Emission", "Transmission", "Specular" as direct input parameters. These are composite parameters that need to be achieved through other allowed parameters.
        2. For color and vector type inputs, always use list format instead of single float numbers. For example:
        - For color inputs (like Base Color, Specular Tint, etc.), use a list of 4 values: [R, G, B, A]
        - For vector inputs (like Normal), use a list of 3 values: [X, Y, Z]
        - For single value inputs, use float numbers directly

        Component names and other information in the scene: {formatted_scene_info}
        Original user input: {user_input}
        Rewritten requirements: {rewritten_input}
        Model description: {json.dumps(scene_description, ensure_ascii=False, indent=2)}
        Material requirements: {json.dumps(material_requirements, ensure_ascii=False, indent=2)}
        Material documentation: {json.dumps(material_docs, ensure_ascii=False, indent=2)}

        Task:
        Generate appropriate materials for each object and create Blender Python code to apply these materials. Use the Principled BSDF shader and only use the following allowed input parameters:

        Allowed Principled BSDF input parameters:
        - Base Color
        - Metallic
        - Roughness
        - IOR
        - Alpha
        - Normal
        - Weight
        - Subsurface Weight
        - Subsurface Radius
        - Subsurface Scale
        - Subsurface Anisotropy
        - Specular IOR Level
        - Specular Tint
        - Anisotropic
        - Anisotropic Rotation
        - Tangent
        - Transmission Weight
        - Coat Weight
        - Coat Roughness
        - Coat IOR
        - Coat Tint
        - Coat Normal
        - Sheen Weight
        - Sheen Roughness
        - Sheen Tint
        - Emission Color
        - Emission Strength

        Output:
        Provide Python code that can be executed directly in Blender. The code should:
        1. Create new materials for each object
        2. Set various parameters for the materials
        3. Apply the materials to the corresponding objects
        4. Use nodes to create more complex material effects (such as wood grain, metal texture, etc.)

        Provide only the Python code, without any additional explanation.
        """
    material_code = generate_text_with_context(prompt)

    # Save the generated material code to a file
    with open(
        os.path.join(log_dir, "material_application_code.py"), "w", encoding="utf-8"
    ) as f:
        f.write(material_code)

    # Execute the generated Blender material commands
    try:
        execute_blender_command(material_code)
        logger.debug("Successfully applied materials.")
    except Exception as e:
        logger.error(f"Error applying materials: {str(e)}")

    # Update the view
    update_blender_view(context)

    # Save screenshots after applying materials
    screenshots = save_screenshots()
    screenshot_dir = os.path.join(log_dir, "material_screenshots")
    save_screenshots_to_path(screenshot_dir)
    for screenshot in screenshots:
        logger.debug(f"Material application screenshot saved: {screenshot}")
