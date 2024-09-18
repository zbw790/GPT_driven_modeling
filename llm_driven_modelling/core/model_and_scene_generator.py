# model_and_scene_generator

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

logger = setup_logger("model_generation_utils")


def query_component_library(obj):
    component_docs = []
    for component in obj.get("components", []):
        component_name = component.get("name", "")
        if component_name:
            results = query_component_documentation(
                bpy.types.Scene.component_query_engine, component_name
            )
            component_docs.extend(results)
    return "\n\n".join(component_docs)


def generate_3d_model(context, obj, scene_context, log_dir):
    # 为每个模型创建单独的目录
    model_dir = os.path.join(log_dir, f"model_{obj['object_type']}")
    os.makedirs(model_dir, exist_ok=True)

    # 查询必要文件
    logger.info("Querying generation documentation")
    generation_docs = query_generation_documentation(
        bpy.types.Scene.generation_query_engine, obj["object_type"]
    )
    logger.info(f"Generation documentation: {generation_docs}")

    # 查询部件库
    component_docs = query_component_library(obj)
    logger.info(f"Component library documentation: {component_docs}")

    # 准备提示信息
    prompt = f"""
        Context:
        你是一个专门用于生成Blender Python命令的AI助手，负责创建3D模型。你需要根据用户的描述和相关文档生成适当的Python代码。

        物体描述：{json.dumps(obj, ensure_ascii=False, indent=2)}
        场景上下文：{scene_context}
        相关生成文档：{generation_docs}
        部件库文档：{component_docs}

        Objective:
        生成时请尽可能参照相关生成文档的内容，因为他们提供了一个合理的生成方法，可以在此基础上进行改动
        生成适当的Blender Python命令来创建指定的3D模型。代码应该准确反映用户的需求，并遵循Blender API的最佳实践。同时，参考部件库文档中的指南来创建各个部件。
        生成的模型应该只考虑外观，而不考虑可能的内部结构，例如一棵树的树冠以球体构成，则不需要考虑树冠内部的树枝，因为无法正常看到树枝。

        Style:
        - 精确：使用正确的Blender Python语法和函数
        - 简洁：只包含必要的代码，不添加多余的注释或解释
        - 结构化：按照逻辑顺序组织代码，使用适当的缩进

        Tone:
        - 专业：使用Blender API的专业术语和函数
        - 直接：直接给出代码，不需要额外的解释
        - 技术性：专注于技术实现，不需要解释代码的意图

        Audience:
        熟悉Blender Python API的3D建模工程师和开发人员

        Response:
        请提供创建3D模型的Blender Python代码。代码应该：
        1. 使用bpy库来创建和操作对象
        2. 为每个组件创建单独的对象，并根据其形状和尺寸进行设置
        3. 正确放置每个组件，确保它们的相对位置正确
        4. 使用循环来创建重复的组件（如多个桌腿）
        5. 为生成的对象设置合适的名称，以便于识别
        6. 添加简单的材质（如果需要）
        7. 生成正确的集合以便于模型管理
        8. 确保所有生成的模型都是3D的，有适当的厚度
        9. 参考部件库文档中的指南来创建各个部件

        请直接返回Python代码，不需要其他解释或注释。
        """

    # 使用 GPT 生成响应
    conversation_manager = context.scene.conversation_manager
    initialize_conversation(context)
    prompt_with_history = add_history_to_prompt(context, prompt)
    response = generate_text_with_context(prompt_with_history)

    # 更新对话历史
    conversation_manager.add_message("user", prompt)
    conversation_manager.add_message("assistant", response)

    logger.info(f"GPT Generated Commands for 3D Model:\n```python\n{response}\n```")

    # 保存生成的代码到文件
    with open(
        os.path.join(model_dir, f"{obj['object_type']}_generation_code.py"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(response)

    # 执行生成的Blender命令
    error_message = execute_blender_command_with_error_handling(response)
    corrected_response = None
    if error_message:
        logger.error(f"Error executing Blender commands: {error_message}")

        # 准备新的提示，包含错误信息
        error_prompt = f"""
            之前的prompt:{prompt}
            在执行之前生成的Blender命令时发生了错误。以下是错误信息：

            {error_message}

            请根据这个错误信息修改之前生成的代码。确保新生成的代码能够正确执行，并避免之前的错误。

            之前生成的代码：
            {response}

            请提供修正后的Blender Python代码。
            """

        # 使用 GPT 生成修正后的代码
        corrected_response = generate_text_with_context(error_prompt)

        logger.info(f"GPT Generated Corrected Commands:\n{corrected_response}")

        # 保存修正后的代码到文件
        with open(
            os.path.join(
                model_dir, f"{obj['object_type']}_corrected_generation_code.py"
            ),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(corrected_response)

        # 尝试执行修正后的代码
        error_message = execute_blender_command_with_error_handling(corrected_response)
        if error_message:
            logger.error(f"Error executing corrected Blender commands: {error_message}")
        else:
            logger.debug("Successfully executed corrected Blender commands.")
    else:
        logger.debug("Successfully executed Blender commands.")

    # 更新视图并等待一小段时间以确保视图已更新
    update_blender_view(context)
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

    # 保存生成模型的截图
    screenshots = save_screenshots()
    screenshot_dir = os.path.join(model_dir, "generation_screenshots")
    save_screenshots_to_path(screenshot_dir)
    for screenshot in screenshots:
        logger.debug(
            f"Generation screenshot saved for {obj['object_type']}: {screenshot}"
        )

    if corrected_response is not None:
        return corrected_response
    else:
        return response


def arrange_scene(context, scene_description, generated_models, log_dir):
    scene_info = get_scene_info()
    formatted_scene_info = format_scene_info(scene_info)
    prompt = f"""
        Context:
        你是一个专门负责安排3D场景中物体位置的AI助手。你的任务是根据给定的场景描述和已生成的模型代码，生成Blender Python命令来正确放置场景中的所有物体。、

        运行之前请先使用以下代码移除场内所有可能干扰的东西：

        # 删除所有对象
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # 删除所有集合（除了场景的主集合）
        for collection in bpy.data.collections:
            bpy.data.collections.remove(collection)


        场景描述：{json.dumps(scene_description, ensure_ascii=False, indent=2)}

        场景内已有的模型信息：{formatted_scene_info}

        已生成的模型代码：
        {json.dumps(generated_models, ensure_ascii=False, indent=2)}

        Task:
        请根据已生成好的模型代码重新生成所有必要的模型
        根据场景描述中每个物体的位置信息，生成Blender Python代码来移动和旋转这些物体，使它们在场景中的位置符合描述。

        Output:
        请提供可以直接在Blender中执行的Python代码。代码应该：
        1. 找到场景中的每个物体（它们已经被创建，名称与object_type相同）
        2. 根据位置描述移动和旋转每个物体
        3. 确保物体之间不会相互穿透或重叠
        4. 如果需要，调整物体的大小以适应场景

        只需提供Python代码，不需要其他解释。
        """

    arrangement_code = generate_text_with_context(prompt)

    # 保存生成的场景安排代码到文件
    with open(
        os.path.join(log_dir, "scene_arrangement_code.py"), "w", encoding="utf-8"
    ) as f:
        f.write(arrangement_code)

    # 执行生成的Blender场景安排命令
    try:
        execute_blender_command(arrangement_code)
        logger.debug("Successfully arranged scene objects.")
    except Exception as e:
        logger.error(f"Error arranging scene objects: {str(e)}")

    # 更新视图
    update_blender_view(context)

    # 保存场景安排后的截图
    screenshots = save_screenshots()
    screenshot_dir = os.path.join(log_dir, "scene_arrangement_screenshots")
    save_screenshots_to_path(screenshot_dir)
    for screenshot in screenshots:
        logger.debug(f"Scene arrangement screenshot saved: {screenshot}")
