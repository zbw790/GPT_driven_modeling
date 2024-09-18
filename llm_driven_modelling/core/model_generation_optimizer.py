# model_generation_optimizer

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

# 创建专门的日志记录器
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
    max_iterations = 2  # 设置最大迭代次数
    iteration = 0
    optimized_model_code = None

    # 为每个模型创建单独的优化目录
    optimization_dir = os.path.join(log_dir, f"optimization_{obj['object_type']}")
    os.makedirs(optimization_dir, exist_ok=True)

    while iteration < max_iterations:
        # 为每次迭代创建一个新的子目录
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
        # 整合并剔除不必要的建议
        filtered_suggestions = filter_and_consolidate_suggestions(
            suggestions, evaluation_context
        )
        # 提取优先建议
        priority_suggestions = filtered_suggestions.get("priority_suggestions", [])

        logger.info(
            f"Iteration {iteration + 1}: Status: {final_status.name}, Score: {average_score:.2f}"
        )
        logger.info(f"Combined Analysis: {combined_analysis}")
        logger.info("Suggestions:")
        logger.info(f"- {suggestions}")
        logger.info(f"Priority Suggestions: {priority_suggestions}")

        # 保存评估结果到文件
        with open(
            os.path.join(
                iteration_dir, f"{obj['object_type']}_evaluation_results.json"
            ),
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

        # 如果模型满意或达到最大迭代次数，退出循环
        if final_status == EvaluationStatus.PASS or iteration == max_iterations - 1:
            break

        # 否则，继续优化模型
        optimized_model_code = optimize_model(
            context,
            priority_suggestions,
            evaluation_context,
            screenshots,
            iteration_dir,
            iteration,
        )
        iteration += 1

    if final_status == EvaluationStatus.PASS:
        logger.info(
            f"Model optimization completed successfully after {iteration + 1} iterations."
        )
    else:
        logger.warning(
            f"Model optimization did not reach satisfactory results after {max_iterations} iterations."
        )

    # 保存最终模型的截图
    final_screenshots = save_screenshots()
    final_screenshot_dir = os.path.join(optimization_dir, "final_model_screenshots")
    save_screenshots_to_path(final_screenshot_dir)
    for screenshot in final_screenshots:
        logger.debug(
            f"Final model screenshot saved for {obj['object_type']}: {screenshot}"
        )

    return optimized_model_code


def filter_and_consolidate_suggestions(suggestions, evaluation_context):
    screenshots = get_screenshots()

    prompt = f"""
        Context:
        你是一个专门负责整合用于优化3D模型的建议的AI助手，你根据图片和需要分析所有的建议，并从中选出需要保留的建议留下。

        模型生成时的代码：{evaluation_context['model_code']}
        模型描述：{json.dumps(evaluation_context['obj'], ensure_ascii=False, indent=2)}
        优化建议：{suggestions}

        Objective:
        该模型生成任务只需要生成模型的草模即可，换句话说就是模型只要长得像就算达到目标，不需要去追求更细节的改变。
        生成的模型应该只考虑外观，而不考虑可能的内部结构，例如一棵树的树冠以球体构成，则不需要考虑树冠内部的树枝，因为无法正常看到树枝。
        例如一个桌子的桌面浮在空中且并未与桌腿相连，建议提出需要链接这两部分。这种类型的建议是必要的，否则桌子将不像是桌子
        反之在桌腿之间增加横梁支撑结构，提高整体稳定性这种类型的建议并不是特别重要，因为增加横梁不会让一个桌子更像桌子。
        该模型将用在虚拟场景中替换对应的物品，因此现实世界中的真实性和合理性不那么重要。
        任何和材质纹理相关的建议都可忽略，这个任务不考虑针对物品材质的升级，灰模即可。
        将同类型的问题合并，例如增加厚度和增加直径可以同时完成
        将重复的问题移除

        Style:
        - 简洁：提供清晰、直接的建议
        - 重点：专注于影响模型外观的关键改变
        - 实用：确保建议可以直接应用于3D建模

        Tone:
        - 专业：使用3D建模相关的专业术语
        - 直接：明确指出需要改变的地方
        - 客观：基于模型的实际需求给出建议

        Audience:
        3D模型设计师和开发人员

        Response:
        请提供一个JSON对象，包含以下元素，且必须是严格的示例形式，请参考example：
        1. priority_suggestions: 优先级最高的建议列表，这些建议对模型的外观和识别度有重大影响
        2. secondary_suggestions: 次要建议列表，这些建议可以改善模型但不是必须的

        Example:
        输出必须是以下形式
        {{
            "priority_suggestions": [
                "建议1",
            ],
            "secondary_suggestions": [
                "建议1",
                "建议2",
                "建议3"
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
    all_optimization_responses = []

    # 获取场景信息
    scene_info = get_scene_info()
    formatted_scene_info = format_scene_info(scene_info)
    logger.info(f"场景内的模型信息: {formatted_scene_info}")

    # 为每个建议生成单独的优化代码
    for suggestion in priority_suggestions:
        # 获取相关优化文档
        modification_doc = query_modification_documentation(
            bpy.types.Scene.modification_query_engine, suggestion
        )
        logger.info(f"相关优化文档: {modification_doc}")

        optimization_response = generate_optimization_code_for_suggestion(
            context,
            suggestion,
            evaluation_context,
            formatted_scene_info,
            modification_doc,
        )
        all_optimization_responses.append(optimization_response)
        logger.info(f"生成的优化代码 for '{suggestion}': {optimization_response}")

    # 综合所有响应，生成最终的优化代码
    final_optimization_code = generate_final_optimization_code(
        context,
        all_optimization_responses,
        evaluation_context,
        formatted_scene_info,
    )

    logger.info(f"最终生成的优化代码:\n{final_optimization_code}")

    # 保存生成的优化代码到文件
    with open(
        os.path.join(iteration_dir, "optimization_code.py"), "w", encoding="utf-8"
    ) as f:
        f.write(final_optimization_code)

    # 执行生成的Blender优化命令
    error_message = execute_blender_command_with_error_handling(final_optimization_code)
    corrected_response = None
    if error_message:
        logger.error(f"Error executing optimization commands: {error_message}")

        # 准备新的提示，包含错误信息
        error_prompt = f"""
            在执行之前生成的Blender优化命令时发生了错误。以下是错误信息：

            {error_message}

            请根据这个错误信息修改之前生成的代码。确保新生成的代码能够正确执行，并避免之前的错误。

            之前生成的代码：
            {final_optimization_code}

            请提供修正后的Blender Python代码。
            请直接返回Python代码，不需要其他解释或注释。
            """

        # 使用 Claude 生成修正后的代码
        corrected_response = generate_text_with_context(error_prompt)

        logger.info(
            f"GPT Generated Corrected Optimization Commands:\n{corrected_response}"
        )

        # 保存修正后的代码到文件
        with open(
            os.path.join(iteration_dir, "corrected_optimization_code.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(corrected_response)

        # 尝试执行修正后的代码
        error_message = execute_blender_command_with_error_handling(corrected_response)
        if error_message:
            logger.error(
                f"Error executing corrected optimization commands: {error_message}"
            )
        else:
            logger.debug("Successfully executed corrected optimization commands.")
    else:
        logger.debug("Successfully executed optimization commands.")

    # 更新视图并等待一小段时间以确保视图已更新
    update_blender_view(context)
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

    # 保存当前迭代的截图
    screenshots = save_screenshots()
    screenshot_dir = os.path.join(iteration_dir, "evaluation_screenshots")
    save_screenshots_to_path(screenshot_dir)
    for screenshot in screenshots:
        logger.debug(
            f"Iteration {iteration + 1} evaluation screenshot saved: {screenshot}"
        )

    if corrected_response is not None:
        return corrected_response
    else:
        return final_optimization_code


def generate_optimization_code_for_suggestion(
    context,
    suggestion,
    evaluation_context,
    formatted_scene_info,
    modification_doc,
):
    prompt = f"""
        Context:
        你是一个专门负责优化3D模型的AI助手。你的任务是根据给定的单个建议，生成Blender Python命令来优化现有的3D模型。
        生成的模型应该只考虑外观，而不考虑可能的内部结构，例如一棵树的树冠以球体构成，则不需要考虑树冠内部的树枝，因为无法正常看到树枝。

        模型生成时的代码：{evaluation_context['model_code']}
        模型描述：{json.dumps(evaluation_context['obj'], ensure_ascii=False, indent=2)}
        场景信息：{formatted_scene_info}
        优化建议：{suggestion}
        相关优化指示文档：{modification_doc}

        Objective:
        生成Blender Python命令来实现这个特定的优化建议，同时保持模型的其他部分不变。

        Style:
        - 精确：使用准确的Blender Python命令
        - 简洁：只包含必要的代码，不添加多余的注释或解释
        - 专注：只针对给定的建议进行优化

        Tone:
        - 专业：使用Blender API的专业术语和函数
        - 直接：直接给出代码，不需要额外的解释
        - 技术性：专注于技术实现，不需要解释代码的意图

        Response:
        请提供实现这个特定优化建议的Blender Python代码。
        请直接返回Python代码，不需要其他解释或注释。
        """

    response = generate_text_with_context(prompt)
    return response


def generate_final_optimization_code(
    context,
    all_optimization_responses,
    evaluation_context,
    formatted_scene_info,
):
    combined_responses = "\n\n".join(all_optimization_responses)

    prompt = f"""
        Context:
        你是一个专门负责优化3D模型的AI助手。你的任务是将多个优化步骤的代码合并成一个连贯的优化脚本。
        生成的模型应该只考虑外观，而不考虑可能的内部结构，例如一棵树的树冠以球体构成，则不需要考虑树冠内部的树枝，因为无法正常看到树枝。

        模型生成时的代码：{evaluation_context['model_code']}
        模型描述：{json.dumps(evaluation_context['obj'], ensure_ascii=False, indent=2)}
        场景信息：{formatted_scene_info}

        以下是各个优化步骤的代码：

        {combined_responses}

        Objective:
        将这些代码片段合并成一个连贯的、高效的优化脚本。确保各个优化步骤之间不会相互冲突，并尽可能优化代码结构。

        Style:
        - 精确：使用准确的Blender Python命令
        - 高效：避免重复操作，优化代码结构
        - 连贯：确保各个优化步骤顺利衔接

        Tone:
        - 专业：使用Blender API的专业术语和函数
        - 直接：直接给出代码，不需要额外的解释
        - 技术性：专注于技术实现，不需要解释代码的意图

        Response:
        请提供合并后的Blender Python代码。代码应该：
        1. 使用bpy库来修改现有对象
        2. 只修改需要优化的部分，保留其他部分不变
        3. 确保优化后的模型符合原始描述和要求
        4. 如果需要添加新组件，确保它们与现有组件协调
        5. 除非绝对必要，不要删除现有模型并生成全新模型

        请直接返回Python代码，不需要其他解释或注释。
        """

    response = generate_text_with_context(prompt)
    return response
