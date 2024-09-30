# model_and_scene_generator.py

"""
This module provides functionality for generating 3D models and arranging scenes in Blender.
It utilizes AI-powered text generation to create Blender Python commands for model creation and scene arrangement.
"""

import bpy
import json
import os
from llm_driven_modelling.llm.claude_module import generate_text_with_claude
from llm_driven_modelling.llm.gpt_module import generate_text_with_context
from llm_driven_modelling.utils.logger_module import setup_logger
from llm_driven_modelling.llm.LLM_common_utils import get_scene_info, format_scene_info
from llm_driven_modelling.core.model_generation_utils import update_blender_view
from llm_driven_modelling.utils.model_viewer_module import (
    save_screenshots,
    save_screenshots_to_path,
)
from llm_driven_modelling.llm.LLM_common_utils import (
    initialize_conversation,
    execute_blender_command,
    add_history_to_prompt,
    get_scene_info,
    format_scene_info,
    execute_blender_command_with_error_handling,
)
from llm_driven_modelling.llama_index_library.llama_index_model_generation import (
    query_generation_documentation,
)
from llm_driven_modelling.llama_index_library.llama_index_component_library import (
    query_component_documentation,
)

logger = setup_logger("model_generation")


def query_component_library(obj):
    """
    Query the component library for documentation on specified components.

    Args:
        obj (dict): Object containing component information.

    Returns:
        str: Concatenated documentation for all queried components.
    """
    component_docs = []
    for component in obj.get("components", []):
        component_name = component.get("name", "")
        if component_name:
            results = query_component_documentation(
                bpy.types.Scene.component_query_engine, component_name
            )
            component_docs.extend(results)
    return "\n\n".join(component_docs)


def generate_3d_model(context, models, obj, scene_context, log_dir):
    """
    Generate a 3D model based on the provided object description and scene context.

    Args:
        context (bpy.types.Context): The current Blender context.
        models (dict): Previously generated models.
        obj (dict): Object description containing model details.
        scene_context (str): Description of the scene context.
        log_dir (str): Directory path for saving logs and generated files.

    Returns:
        str: The generated Blender Python code for creating the 3D model.
    """
    model_dir = os.path.join(log_dir, f"model_{obj['object_type']}")
    os.makedirs(model_dir, exist_ok=True)

    logger.info("Querying generation documentation")
    generation_docs = query_generation_documentation(
        bpy.types.Scene.generation_query_engine, obj["object_type"]
    )
    logger.info(f"Generation documentation: {generation_docs}")

    component_docs = query_component_library(obj)
    logger.info(f"Component library documentation: {component_docs}")

    # Query style documentation
    style = obj["style"]
    style_docs = query_generation_documentation(
        bpy.types.Scene.generation_query_engine, obj["style"]
    )
    logger.info(f"Style documentation: {style_docs}")

    prompt = f"""
        Context:
        You are an AI assistant specialized in generating Blender Python commands for creating 3D models. Your task is to generate appropriate Python code based on user descriptions and relevant documentation.
        
        Previously generated models: {models}
        Object description: {json.dumps(obj, ensure_ascii=False, indent=2)}
        Scene context: {scene_context}
        Relevant generation documentation: {generation_docs}
        Component library documentation: {component_docs}
        Style documentation: {style_docs}

        Objective:
        Generate appropriate Blender Python commands to create the specified 3D model. The code should accurately reflect the user's requirements and follow Blender API best practices. Also, refer to the component library documentation for guidelines on creating individual components.
        The generated model should only consider the appearance and not potential internal structures. For example, if a tree crown is composed of spheres, there's no need to consider the branches inside the crown as they won't be visible.

        IMPORTANT: You must strictly adhere to the specified style ({style}) for this model. The style is a crucial aspect of the model's appearance and should be implemented precisely according to the provided style documentation. Do not deviate from this style under any circumstances.

        When generating the main object, incorporate and reference the code from previously generated models where appropriate. This allows for a more cohesive and efficient overall model generation.

        Additionally, ensure that all components of the model are precisely calculated and tightly fitted. This includes:
        1. Strict calculation of distances between interconnected parts (e.g., legs and base of furniture).
        2. Ensuring that adjoining components (like backrest and seat of a chair) are tightly fitted without gaps.
        3. Precise positioning of all elements to create a cohesive and realistic model.

        Style:
        - Precise: Use correct Blender Python syntax and functions
        - Concise: Include only necessary code, without extra comments or explanations
        - Structured: Organize code in a logical order, using appropriate indentation

        Tone:
        - Professional: Use professional terminology and functions from the Blender API
        - Direct: Provide code directly without additional explanations
        - Technical: Focus on technical implementation without explaining code intent

        Audience:
        3D modeling engineers and developers familiar with the Blender Python API

        Response:
        Please provide Blender Python code to create the 3D model. The code should:
        1. Use the bpy library to create and manipulate objects
        2. Create separate objects for each component, setting their shape and dimensions
        3. Correctly position each component, ensuring their relative positions are accurate
        4. Use loops to create repetitive components (e.g., multiple table legs)
        5. Set appropriate names for generated objects for easy identification
        6. Add simple materials (if needed)
        7. Generate correct collections for model management
        8. Ensure all generated models are 3D with appropriate thickness
        9. Refer to the component library documentation for guidelines on creating individual components
        10. Implement strict calculations for distances between interconnected parts
        11. Ensure tight fitting of adjoining components without gaps
        12. Use precise measurements and positioning for all elements of the model
        13. Integrate code from previously generated models when creating the main object or related components
        14. Ensure consistency in naming conventions and coding style with previously generated models
        15. STRICTLY apply the specified style ({style}) to the model, following the provided style documentation. This is a critical requirement and must be implemented accurately.

        Remember: The style ({style}) is a non-negotiable aspect of this model. Every aspect of the model's creation should be influenced by this style, from the overall shape to the smallest details. Refer constantly to the style documentation to ensure compliance.

        Please return Python code directly, without additional explanations or comments.
        """

    conversation_manager = context.scene.conversation_manager
    initialize_conversation(context)
    prompt_with_history = add_history_to_prompt(context, prompt)
    response = generate_text_with_claude(prompt_with_history)

    conversation_manager.add_message("user", prompt)
    conversation_manager.add_message("assistant", response)

    logger.info(f"GPT Generated Commands for 3D Model:\n```python\n{response}\n```")

    with open(
        os.path.join(model_dir, f"{obj['object_type']}_generation_code.py"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(response)

    error_message = execute_blender_command_with_error_handling(response)
    corrected_response = None
    if error_message:
        logger.error(f"Error executing Blender commands: {error_message}")

        error_prompt = f"""
            Previous prompt: {prompt}
            An error occurred while executing the previously generated Blender commands. Here's the error message:

            {error_message}

            Please modify the previously generated code based on this error message. Ensure the newly generated code executes correctly and avoids the previous error.

            Previously generated code:
            {response}

            Please provide the corrected Blender Python code.
            """

        corrected_response = generate_text_with_claude(error_prompt)

        logger.info(f"GPT Generated Corrected Commands:\n{corrected_response}")

        with open(
            os.path.join(
                model_dir, f"{obj['object_type']}_corrected_generation_code.py"
            ),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(corrected_response)

        error_message = execute_blender_command_with_error_handling(corrected_response)
        if error_message:
            logger.error(f"Error executing corrected Blender commands: {error_message}")
        else:
            logger.debug("Successfully executed corrected Blender commands.")
    else:
        logger.debug("Successfully executed Blender commands.")

    update_blender_view(context)
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

    screenshots = save_screenshots()
    screenshot_dir = os.path.join(model_dir, "generation_screenshots")
    save_screenshots_to_path(screenshot_dir)
    for screenshot in screenshots:
        logger.debug(
            f"Generation screenshot saved for {obj['object_type']}: {screenshot}"
        )

    return corrected_response if corrected_response is not None else response


def arrange_scene(context, scene_description, generated_models, log_dir):
    """
    Arrange the scene based on the provided scene description and generated models.

    Args:
        context (bpy.types.Context): The current Blender context.
        scene_description (dict): Description of the scene layout.
        generated_models (dict): Dictionary of generated model codes.
        log_dir (str): Directory path for saving logs and generated files.
    """
    scene_info = get_scene_info()
    formatted_scene_info = format_scene_info(scene_info)
    prompt = f"""
        Context:
        You are an AI assistant specialized in arranging objects in a 3D scene. Your task is to generate Blender Python commands to correctly position all objects in the scene based on the given scene description and generated model code.

        Before running, please use the following code to remove any potential interfering elements in the scene:

        # Delete all objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # Delete all collections (except the main scene collection)
        for collection in bpy.data.collections:
            bpy.data.collections.remove(collection)

        Scene description: {json.dumps(scene_description, ensure_ascii=False, indent=2)}

        Existing model information in the scene: {formatted_scene_info}

        Generated model code:
        {json.dumps(generated_models, ensure_ascii=False, indent=2)}

        Task:
        *Strictly use the provided generated model code to recreate all necessary objects in the scene. The number of objects can be determined based on the scene description, but the generation code for each object type must follow the provided code exactly.

        Generate Blender Python code to move and rotate these objects based on the position information of each object in the scene description, ensuring their positions in the scene match the description.

        Additionally, ensure precise calculations and tight positioning of objects:
        1. Implement strict calculations for distances between objects
        2. Ensure objects are tightly fitted against walls, floors, or other objects as described
        3. Use precise measurements for object placement, considering their dimensions and the scene's scale

        Output:
        Please provide Python code that can be executed directly in Blender. The code should:
        1. *Recreate each object using the exact code provided in the generated model code
        2. Find each object in the scene (they have been created with names matching their object_type)
        3. Move and rotate each object according to the position description
        4. Ensure objects do not intersect or overlap with each other
        5. Adjust object sizes to fit the scene if necessary
        6. Calculate and apply precise positions, ensuring objects are exactly where they should be
        7. Implement checks to verify that objects are correctly placed and oriented
        8. Use mathematical calculations to ensure objects are aligned properly with each other and the scene

        *Note: You may perform minor optimizations or combine steps where appropriate, but the core generation code for each object must remain unchanged.

        Provide only the Python code, without additional explanations.
    """

    arrangement_code = generate_text_with_claude(prompt)

    with open(
        os.path.join(log_dir, "scene_arrangement_code.py"), "w", encoding="utf-8"
    ) as f:
        f.write(arrangement_code)

    error_message = execute_blender_command_with_error_handling(arrangement_code)
    if error_message:
        logger.error(f"Error arranging scene objects: {error_message}")

        error_prompt = f"""
            Previous prompt: {prompt}
            An error occurred while executing the previously generated scene arrangement commands. Here's the error message:

            {error_message}

            Please modify the previously generated code based on this error message. Ensure the newly generated code executes correctly and avoids the previous error.

            Previously generated code:
            {arrangement_code}

            Please provide the corrected Blender Python code for scene arrangement.
            """

        corrected_arrangement_code = generate_text_with_claude(error_prompt)

        logger.info(
            f"GPT Generated Corrected Scene Arrangement Commands:\n{corrected_arrangement_code}"
        )

        with open(
            os.path.join(log_dir, "corrected_scene_arrangement_code.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(corrected_arrangement_code)

        error_message = execute_blender_command_with_error_handling(
            corrected_arrangement_code
        )
        if error_message:
            logger.error(
                f"Error executing corrected scene arrangement commands: {error_message}"
            )
        else:
            logger.debug("Successfully executed corrected scene arrangement commands.")
    else:
        logger.debug("Successfully arranged scene objects.")

    update_blender_view(context)

    screenshots = save_screenshots()
    screenshot_dir = os.path.join(log_dir, "scene_arrangement_screenshots")
    save_screenshots_to_path(screenshot_dir)
    for screenshot in screenshots:
        logger.debug(f"Scene arrangement screenshot saved: {screenshot}")
