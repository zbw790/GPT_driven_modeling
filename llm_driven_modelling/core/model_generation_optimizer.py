# model_generation_optimizer.py

"""
This module provides functionality for evaluating and optimizing 3D models in Blender.
It uses AI-powered analysis and generation to improve model quality based on user input and scene context.
"""

import bpy
import json
import os
from llm_driven_modelling.llm.claude_module import (
    generate_text_with_claude,
    analyze_screenshots_with_claude,
)
from llm_driven_modelling.llm.LLM_common_utils import (
    sanitize_command,
    get_screenshots,
    get_scene_info,
    format_scene_info,
    execute_blender_command_with_error_handling,
)
from llm_driven_modelling.utils.logger_module import setup_logger
from llm_driven_modelling.llm.gpt_module import (
    generate_text_with_context,
    analyze_screenshots_with_gpt4,
)
from llm_driven_modelling.llama_index_library.llama_index_model_modification import (
    query_modification_documentation,
)
from llm_driven_modelling.core.evaluators_module import ModelEvaluator, EvaluationStatus
from llm_driven_modelling.utils.model_viewer_module import (
    save_screenshots,
    save_screenshots_to_path,
)
from llm_driven_modelling.core.model_generation_utils import (
    sanitize_reference,
    update_blender_view,
)

# Create a dedicated logger
logger = setup_logger("model_generation")


def evaluate_and_optimize_model(
    context,
    obj,
    scene_context,
    model_code,
    user_input,
    rewritten_input,
    log_dir,
):
    """
    Evaluate and optimize a 3D model through multiple iterations.

    Args:
        context: The Blender context.
        obj (dict): Object information.
        scene_context (dict): Scene context information.
        model_code (str): Initial model generation code.
        user_input (str): Original user input.
        rewritten_input (str): Rewritten user input.
        log_dir (str): Directory for logging.

    Returns:
        str: Optimized model code.
    """
    max_iterations = 2
    iteration = 0
    optimized_model_code = None

    optimization_dir = os.path.join(log_dir, f"optimization_{obj['object_type']}")
    os.makedirs(optimization_dir, exist_ok=True)

    while iteration < max_iterations:
        iteration_dir = os.path.join(optimization_dir, f"iteration_{iteration + 1}")
        os.makedirs(iteration_dir, exist_ok=True)

        screenshots = get_screenshots()
        evaluator = ModelEvaluator()

        evaluation_context = {
            "model_code": model_code,
            "obj": obj,
            "scene_context": scene_context,
        }

        results = evaluator.evaluate(screenshots, evaluation_context)
        (
            combined_analysis,
            final_status,
            average_score,
            suggestions,
        ) = evaluator.aggregate_results(results)

        filtered_suggestions = filter_and_consolidate_suggestions(
            suggestions, evaluation_context
        )
        priority_suggestions = filtered_suggestions.get("priority_suggestions", [])

        logger.info(
            f"Iteration {iteration + 1}: Status: {final_status.name}, Score: {average_score:.2f}"
        )
        logger.info(f"Combined Analysis: {combined_analysis}")
        logger.info(f"Suggestions: {suggestions}")
        logger.info(f"Priority Suggestions: {priority_suggestions}")

        save_evaluation_results(
            iteration_dir,
            obj,
            iteration,
            final_status,
            average_score,
            combined_analysis,
            suggestions,
            priority_suggestions,
        )

        if final_status == EvaluationStatus.PASS or iteration == max_iterations - 1:
            break

        optimized_model_code = optimize_model(
            context,
            priority_suggestions,
            evaluation_context,
            screenshots,
            iteration_dir,
            iteration,
        )
        iteration += 1

    log_optimization_result(final_status, iteration, max_iterations)
    save_final_screenshots(optimization_dir, obj)

    return optimized_model_code


def filter_and_consolidate_suggestions(suggestions, evaluation_context):
    """
    Filter and consolidate optimization suggestions using AI analysis.

    Args:
        suggestions (list): List of initial suggestions.
        evaluation_context (dict): Context for evaluation.

    Returns:
        dict: Filtered and consolidated suggestions.
    """
    screenshots = get_screenshots()

    prompt = f"""
        Context:
        You are an AI assistant specialized in consolidating suggestions for 3D model optimization. Your task is to analyze all suggestions based on the images and select the ones that need to be retained.

        Model generation code: {evaluation_context['model_code']}
        Model description: {json.dumps(evaluation_context['obj'], ensure_ascii=False, indent=2)}
        Optimization suggestions: {suggestions}

        Objective:
        This model generation task only requires creating a rough model. In other words, the model is considered to have reached the goal as long as it looks similar to the target. There's no need to pursue more detailed changes.
        The generated model should only consider appearance, not possible internal structures. For example, if a tree's crown is composed of a sphere, there's no need to consider the branches inside the crown as they cannot be seen normally.
        For instance, if a table's top is floating in the air and not connected to the legs, a suggestion to connect these two parts is necessary. This type of suggestion is essential, otherwise, the table won't look like a table.
        On the contrary, suggestions like adding cross beams between table legs to improve overall stability are not particularly important, as adding cross beams won't make a table look more like a table.
        This model will be used to replace corresponding items in a virtual scene, so realism and rationality in the real world are not that important.
        Any suggestions related to materials and textures can be ignored, as this task does not consider upgrading the item's material. A gray model is sufficient.
        Merge similar types of problems, for example, increasing thickness and increasing diameter can be done simultaneously.
        Remove duplicate issues.

        Style:
        - Concise: Provide clear, direct suggestions
        - Focused: Concentrate on key changes that affect the model's appearance
        - Practical: Ensure suggestions can be directly applied to 3D modeling

        Tone:
        - Professional: Use professional terminology related to 3D modeling
        - Direct: Clearly point out areas that need change
        - Objective: Provide suggestions based on the actual needs of the model

        Audience:
        3D model designers and developers

        Response:
        Please provide a JSON object containing the following elements, and it must be in the strict example format, please refer to the example:
        1. priority_suggestions: A list of highest priority suggestions that have a significant impact on the model's appearance and recognizability
        2. secondary_suggestions: A list of secondary suggestions that can improve the model but are not mandatory

        Example:
        The output must be in the following format
        {{
            "priority_suggestions": [
                "Suggestion 1",
            ],
            "secondary_suggestions": [
                "Suggestion 1",
                "Suggestion 2",
                "Suggestion 3"
            ],
        }}
        """

    response = analyze_screenshots_with_claude(prompt, screenshots)
    response = sanitize_command(response)
    response = sanitize_reference(response)
    return json.loads(response)


def optimize_model(
    context,
    priority_suggestions,
    evaluation_context,
    screenshots,
    iteration_dir,
    iteration,
):
    """
    Optimize the 3D model based on priority suggestions.

    Args:
        context: The Blender context.
        priority_suggestions (list): List of priority optimization suggestions.
        evaluation_context (dict): Context for evaluation.
        screenshots (list): List of screenshot paths.
        iteration_dir (str): Directory for the current iteration.
        iteration (int): Current iteration number.

    Returns:
        str: Optimized model code.
    """
    all_optimization_responses = []
    scene_info = get_scene_info()
    formatted_scene_info = format_scene_info(scene_info)
    logger.info(f"Scene model information: {formatted_scene_info}")

    for suggestion in priority_suggestions:
        modification_doc = query_modification_documentation(
            bpy.types.Scene.modification_query_engine, suggestion
        )
        logger.info(f"Relevant optimization documentation: {modification_doc}")

        optimization_response = generate_optimization_code_for_suggestion(
            context,
            suggestion,
            evaluation_context,
            formatted_scene_info,
            modification_doc,
        )
        all_optimization_responses.append(optimization_response)
        logger.info(
            f"Generated optimization code for '{suggestion}': {optimization_response}"
        )

    final_optimization_code = generate_final_optimization_code(
        context,
        all_optimization_responses,
        evaluation_context,
        formatted_scene_info,
    )

    logger.info(f"Final generated optimization code:\n{final_optimization_code}")
    save_optimization_code(iteration_dir, final_optimization_code)

    error_message = execute_blender_command_with_error_handling(final_optimization_code)
    if error_message:
        logger.error(f"Error executing optimization commands: {error_message}")
        corrected_response = handle_optimization_error(
            error_message, final_optimization_code, iteration_dir
        )
        if corrected_response:
            final_optimization_code = corrected_response

    update_blender_view(context)
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

    save_iteration_screenshots(iteration_dir, iteration)

    return final_optimization_code


def generate_optimization_code_for_suggestion(
    context,
    suggestion,
    evaluation_context,
    formatted_scene_info,
    modification_doc,
):
    """
    Generate optimization code for a single suggestion.

    Args:
        context: The Blender context.
        suggestion (str): The optimization suggestion.
        evaluation_context (dict): Context for evaluation.
        formatted_scene_info (str): Formatted scene information.
        modification_doc (str): Relevant modification documentation.

    Returns:
        str: Generated optimization code.
    """
    prompt = f"""
        Context:
        You are an AI assistant specialized in optimizing 3D models. Your task is to generate Blender Python commands to optimize an existing 3D model based on a given single suggestion.
        The generated model should only consider appearance, not possible internal structures. For example, if a tree's crown is composed of a sphere, there's no need to consider the branches inside the crown as they cannot be seen normally.

        Model generation code: {evaluation_context['model_code']}
        Model description: {json.dumps(evaluation_context['obj'], ensure_ascii=False, indent=2)}
        Scene information: {formatted_scene_info}
        Optimization suggestion: {suggestion}
        Relevant optimization instruction document: {modification_doc}

        Objective:
        Generate Blender Python commands to implement this specific optimization suggestion while keeping other parts of the model unchanged.

        Style:
        - Precise: Use accurate Blender Python commands
        - Concise: Include only necessary code, without adding extra comments or explanations
        - Focused: Optimize only based on the given suggestion

        Tone:
        - Professional: Use professional terms and functions of the Blender API
        - Direct: Provide code directly, without additional explanations
        - Technical: Focus on technical implementation, no need to explain the intention of the code

        Response:
        Please provide Blender Python code that implements this specific optimization suggestion.
        Please return Python code directly, without other explanations or comments.
        """
    return generate_text_with_context(prompt)


def generate_final_optimization_code(
    context,
    all_optimization_responses,
    evaluation_context,
    formatted_scene_info,
):
    """
    Generate final optimization code by combining all optimization responses.

    Args:
        context: The Blender context.
        all_optimization_responses (list): List of all optimization responses.
        evaluation_context (dict): Context for evaluation.
        formatted_scene_info (str): Formatted scene information.

    Returns:
        str: Final combined optimization code.
    """
    combined_responses = "\n\n".join(all_optimization_responses)
    prompt = f"""
        Context:
        You are an AI assistant specialized in optimizing 3D models. Your task is to merge multiple optimization step codes into a coherent optimization script.
        The generated model should only consider appearance, not possible internal structures. For example, if a tree's crown is composed of a sphere, there's no need to consider the branches inside the crown as they cannot be seen normally.

        Model generation code: {evaluation_context['model_code']}
        Model description: {json.dumps(evaluation_context['obj'], ensure_ascii=False, indent=2)}
        Scene information: {formatted_scene_info}

        Here are the codes for each optimization step:

        {combined_responses}

        Objective:
        Merge these code snippets into a coherent, efficient optimization script. Ensure that the various optimization steps do not conflict with each other, and optimize the code structure as much as possible.

        Style:
        - Precise: Use accurate Blender Python commands
        - Efficient: Avoid repetitive operations, optimize code structure
        - Coherent: Ensure smooth connection between optimization steps

        Tone:
        - Professional: Use professional terms and functions of the Blender API
        - Direct: Provide code directly, without additional explanations
        - Technical: Focus on technical implementation, no need to explain the intention of the code

        Response:
        Please provide the merged Blender Python code. The code should:
        1. Use the bpy library to modify existing objects
        2. Only modify parts that need optimization, keeping other parts unchanged
        3. Ensure the optimized model meets the original description and requirements
        4. If new components need to be added, ensure they coordinate with existing components
        5. Do not delete the existing model and generate a completely new one unless absolutely necessary

        Please return Python code directly, without other explanations or comments.
        """
    return generate_text_with_context(prompt)


def save_evaluation_results(
    iteration_dir,
    obj,
    iteration,
    final_status,
    average_score,
    combined_analysis,
    suggestions,
    priority_suggestions,
):
    """Save evaluation results to a JSON file."""
    with open(
        os.path.join(iteration_dir, f"{obj['object_type']}_evaluation_results.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "iteration": iteration + 1,
                "status": final_status.name,
                "score": average_score,
                "analysis": combined_analysis,
                "suggestions": suggestions,
                "priority_suggestions": priority_suggestions,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def log_optimization_result(final_status, iteration, max_iterations):
    """Log the final result of the optimization process."""
    if final_status == EvaluationStatus.PASS:
        logger.info(
            f"Model optimization completed successfully after {iteration + 1} iterations."
        )
    else:
        logger.warning(
            f"Model optimization did not reach satisfactory results after {max_iterations} iterations."
        )


def save_final_screenshots(optimization_dir, obj):
    """Save screenshots of the final optimized model."""
    final_screenshots = save_screenshots()
    final_screenshot_dir = os.path.join(optimization_dir, "final_model_screenshots")
    save_screenshots_to_path(final_screenshot_dir)
    for screenshot in final_screenshots:
        logger.debug(
            f"Final model screenshot saved for {obj['object_type']}: {screenshot}"
        )


def save_optimization_code(iteration_dir, optimization_code):
    """Save the generated optimization code to a file."""
    with open(
        os.path.join(iteration_dir, "optimization_code.py"), "w", encoding="utf-8"
    ) as f:
        f.write(optimization_code)


def handle_optimization_error(error_message, optimization_code, iteration_dir):
    """Handle errors in optimization code execution."""
    error_prompt = f"""
        An error occurred while executing the previously generated Blender optimization commands. Here is the error message:

        {error_message}

        Please modify the previously generated code based on this error message. Ensure that the newly generated code can be executed correctly and avoid the previous error.

        Previously generated code:
        {optimization_code}

        Please provide the corrected Blender Python code.
        Please return Python code directly, without other explanations or comments.
        """
    corrected_response = generate_text_with_context(error_prompt)
    logger.info(f"GPT Generated Corrected Optimization Commands:\n{corrected_response}")

    with open(
        os.path.join(iteration_dir, "corrected_optimization_code.py"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(corrected_response)

    new_error_message = execute_blender_command_with_error_handling(corrected_response)
    if new_error_message:
        logger.error(
            f"Error executing corrected optimization commands: {new_error_message}"
        )
        return None
    else:
        logger.debug("Successfully executed corrected optimization commands.")
        return corrected_response


def save_iteration_screenshots(iteration_dir, iteration):
    """Save screenshots for the current iteration."""
    screenshots = save_screenshots()
    screenshot_dir = os.path.join(iteration_dir, "evaluation_screenshots")
    save_screenshots_to_path(screenshot_dir)
    for screenshot in screenshots:
        logger.debug(
            f"Iteration {iteration + 1} evaluation screenshot saved: {screenshot}"
        )
