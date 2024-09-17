# model_generation.py

import bpy
import json
import re
import os
from typing import List, Dict, Any
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty
from llm_driven_modelling.llm.claude_module import (
    generate_text_with_claude,
    analyze_screenshots_with_claude,
)
from llm_driven_modelling.llm.LLM_common_utils import (
    sanitize_command,
    initialize_conversation,
    execute_blender_command,
    add_history_to_prompt,
    get_screenshots,
    get_scene_info,
    format_scene_info,
    execute_blender_command_with_error_handling,
)
from llm_driven_modelling.utils.logger_module import setup_logger, log_context
from llm_driven_modelling.core.prompt_rewriter import rewrite_prompt
from llm_driven_modelling.llm.gpt_module import (
    generate_text_with_context,
    analyze_screenshots_with_gpt4,
)
from llm_driven_modelling.llama_index_library.llama_index_model_generation import (
    query_generation_documentation,
)
from llm_driven_modelling.llama_index_library.llama_index_model_modification import (
    query_modification_documentation,
)
from llm_driven_modelling.llama_index_library.llama_index_component_library import (
    query_component_documentation,
)
from llm_driven_modelling.core.evaluators_module import ModelEvaluator, EvaluationStatus
from llm_driven_modelling.utils.model_viewer_module import save_screenshots, save_screenshots_to_path
from llm_driven_modelling.llama_index_library.llama_index_material_library import (
    query_material_documentation,
)

# 创建专门的日志记录器
logger = setup_logger("model_generation")


class ModelGenerationProperties(PropertyGroup):
    input_text: StringProperty(
        name="Model Description",
        description="Describe the model you want to generate",
        default="",
    )

def sanitize_reference(response):
    """
    从Claude的响应中提取JSON数据，去除注释和其他非JSON内容。
    """
    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        json_str = json_match.group(0)
        try:
            json_data = json.loads(json_str)
            return json.dumps(json_data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            return json_str
    else:
        return ""


class MODEL_GENERATION_OT_generate(Operator):
    bl_idname = "model_generation.generate"
    bl_label = "Generate Scene"
    bl_description = "Generate a 3D scene based on the description"

    def execute(self, context):
        props = context.scene.model_generation_tool
        user_input = props.input_text

        with log_context(logger, user_input) as log_dir:
            try:
                logger.info("Rewriting user input")
                rewritten_input = rewrite_prompt(user_input)
                logger.info(f"Rewritten input: {rewritten_input}")

                logger.info("Parsing rewritten user input")
                scene_description = self.parse_scene_input(user_input, rewritten_input)
                logger.info("Scene Description:")
                logger.info(json.dumps(scene_description, ensure_ascii=False, indent=2))

                # Save scene description to file
                with open(os.path.join(log_dir, "scene_description.json"), "w", encoding="utf-8") as f:
                    json.dump(scene_description, f, ensure_ascii=False, indent=2)

                # Generate and optimize 3D models for each object in the scene
                models = []
                for obj in scene_description["objects"]:
                    logger.info(f"Generating model for: {obj['object_type']}")
                    model = self.generate_and_optimize_model(
                        context, 
                        obj, 
                        scene_description["scene_context"], 
                        user_input, 
                        rewritten_input, 
                        log_dir
                    )
                    models.append(model)

                # Arrange objects in the scene
                self.arrange_scene(context, scene_description, models, log_dir)

                # Apply materials to the entire scene
                self.apply_materials(context, user_input, rewritten_input, scene_description, log_dir)

                logger.debug(f"Log directory: {log_dir}")
                # Save screenshot of the current scene
                screenshot_path = os.path.join(log_dir, "scene_screenshot.png")
                bpy.ops.screen.screenshot(filepath=screenshot_path)
                logger.debug(f"Screenshot saved to {screenshot_path}")

                self.report({"INFO"}, f"Scene generated and optimized. Logs saved in {log_dir}")
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                self.report({"ERROR"}, f"An error occurred: {str(e)}")

        return {"FINISHED"}

    def generate_and_optimize_model(self, context, obj, scene_context, user_input, rewritten_input, log_dir):
        """
        Generate and optimize a 3D model for a given object.

        Args:
            context (bpy.types.Context): The current Blender context.
            obj (dict): The object description.
            scene_context (dict): The overall scene context.
            user_input (str): The original user input.
            rewritten_input (str): The rewritten user input.
            log_dir (str): The directory for saving logs.

        Returns:
            dict: A dictionary containing the original and optimized model information.
        """
        # Generate initial model
        initial_model_code = self.generate_3d_model(context, obj, scene_context, log_dir)

        # Optimize the model
        optimized_model_code = self.evaluate_and_optimize_model(
            context,
            obj,
            scene_context,
            initial_model_code,
            user_input,
            rewritten_input,
            log_dir
        )

        return {
            "object_type": obj["object_type"],
            "initial_model": initial_model_code,
            "optimized_model": optimized_model_code
        }

    def parse_scene_input(self, user_input, rewritten_input):
        prompt = f"""
        Context:
        你是一个专门用于解析和重构用户输入的AI助手。工作在一个3D建模系统中。你的主要任务是处理用户提供的场景描述，这些描述可能包含多个物品及其位置关系。

        Objective:
        将用户的原始描述和重写后的提示词转换为标准化的JSON格式，包含场景中的每个物品及其相对位置，以及整个场景的上下文信息。

        输入:
        用户原始输入: {user_input}
        解析后的提示词：{rewritten_input}

        输出格式示例:
        {{
          "scene_name": "书房场景",
          "scene_context": "这是一个安静的书房，光线柔和，氛围温馨。",
          "objects": [
            {{
              "object_type": "书桌",
              "position": "房间中央",
              "description": "一张宽大的木质书桌，表面光滑",
              "components": [
                {{
                  "name": "桌面",
                  "quantity": 1,
                  "shape": "cuboid",
                  "dimensions": {{
                    "length": 120,
                    "width": 60,
                    "height": 5
                  }}
                }},
                {{
                  "name": "桌腿",
                  "quantity": 4,
                  "shape": "cylinder",
                  "dimensions": {{
                    "radius": 3,
                    "height": 75
                  }}
                }}
              ]
            }},
            {{
              "object_type": "花瓶",
              "position": "书桌右上角",
              "description": "一个蓝白相间的陶瓷花瓶，里面插着几支鲜花",
              "components": [
                {{
                  "name": "瓶身",
                  "quantity": 1,
                  "shape": "cylinder",
                  "dimensions": {{
                    "radius": 10,
                    "height": 30
                  }}
                }}
              ]
            }}
          ]
        }}

        注意事项:
        1. 识别场景中的所有物品，并为每个物品创建一个对象描述。
        2. 包含每个物品的相对位置信息和简短描述。
        3. 对于每个物品，列出其核心组件，类似于之前的单一物品描述。
        4. 如果某些信息缺失，请根据常识进行合理推断。
        5. 确保位置描述足够清晰，以便后续正确放置物品。
        6. 添加一个scene_context字段，描述整个场景的氛围、光线等信息。
        """

        logger.info(f"Sending prompt to Claude: {prompt}")
        response = generate_text_with_claude(prompt)
        logger.info(f"Received response from Claude: {response}")

        response = sanitize_command(response)
        response = sanitize_reference(response)
        return json.loads(response)

    def arrange_scene(self, context, scene_description, generated_models, log_dir):
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
            self.report({"ERROR"}, f"Error arranging scene objects: {str(e)}")

        # 更新视图
        self.update_blender_view(context)

        # 保存场景安排后的截图
        screenshots = save_screenshots()
        screenshot_dir = os.path.join(log_dir, "scene_arrangement_screenshots")
        save_screenshots_to_path(screenshot_dir)
        for screenshot in screenshots:
            logger.debug(f"Scene arrangement screenshot saved: {screenshot}")

    def generate_3d_model(self, context, obj, scene_context, log_dir):
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
        component_docs = self.query_component_library(obj)
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
            error_message = execute_blender_command_with_error_handling(
                corrected_response
            )
            if error_message:
                logger.error(
                    f"Error executing corrected Blender commands: {error_message}"
                )
                self.report(
                    {"ERROR"},
                    f"Error executing corrected Blender commands: {error_message}",
                )
            else:
                logger.debug("Successfully executed corrected Blender commands.")
        else:
            logger.debug("Successfully executed Blender commands.")

        # 更新视图并等待一小段时间以确保视图已更新
        self.update_blender_view(context)
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

    def query_component_library(self, obj):
        component_docs = []
        for component in obj.get("components", []):
            component_name = component.get("name", "")
            if component_name:
                results = query_component_documentation(
                    bpy.types.Scene.component_query_engine, component_name
                )
                component_docs.extend(results)
        return "\n\n".join(component_docs)

    def update_blender_view(self, context):
        # 确保更改立即可见
        bpy.context.view_layer.update()
        logger.debug("Blender view updated.")

    def evaluate_and_optimize_model(
        self,
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
            filtered_suggestions = self.filter_and_consolidate_suggestions(
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
            optimized_model_code = self.optimize_model(
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
            self.report(
                {"INFO"},
                f"Model optimized successfully after {iteration + 1} iterations.",
            )
        else:
            logger.warning(
                f"Model optimization did not reach satisfactory results after {max_iterations} iterations."
            )
            self.report(
                {"WARNING"},
                f"Model optimization completed with suboptimal results after {max_iterations} iterations.",
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

    def filter_and_consolidate_suggestions(self, suggestions, evaluation_context):
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
        self,
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

            optimization_response = self.generate_optimization_code_for_suggestion(
                context,
                suggestion,
                evaluation_context,
                formatted_scene_info,
                modification_doc,
            )
            all_optimization_responses.append(optimization_response)
            logger.info(f"生成的优化代码 for '{suggestion}': {optimization_response}")

        # 综合所有响应，生成最终的优化代码
        final_optimization_code = self.generate_final_optimization_code(
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
        error_message = execute_blender_command_with_error_handling(
            final_optimization_code
        )
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
            error_message = execute_blender_command_with_error_handling(
                corrected_response
            )
            if error_message:
                logger.error(
                    f"Error executing corrected optimization commands: {error_message}"
                )
                self.report(
                    {"ERROR"},
                    f"Error executing corrected optimization commands: {error_message}",
                )
            else:
                logger.debug("Successfully executed corrected optimization commands.")
        else:
            logger.debug("Successfully executed optimization commands.")

        # 更新视图并等待一小段时间以确保视图已更新
        self.update_blender_view(context)
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
        self,
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
        self,
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

    def apply_materials(
        self, context, user_input, rewritten_input, scene_description, log_dir
    ):
        try:
            # 获取场景信息
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)

            # 步骤1：分析场景信息并确定所需的材质
            material_requirements = self.analyze_scene_for_materials(
                user_input, rewritten_input, formatted_scene_info, scene_description
            )
            logger.info(f"材质需求： {material_requirements}")

            # 步骤2：查询相关的材质文档
            material_docs = self.query_material_docs(material_requirements)
            logger.info(f"材质文档： {material_docs}")

            # 步骤3：生成并应用材质
            self.generate_and_apply_materials(
                context,
                user_input,
                rewritten_input,
                formatted_scene_info,
                scene_description,
                material_requirements,
                material_docs,
                log_dir,
            )

            self.report(
                {"INFO"}, f"Materials applied successfully. Logs saved in {log_dir}"
            )
        except Exception as e:
            logger.error(f"An error occurred while applying materials: {str(e)}")
            self.report(
                {"ERROR"}, f"An error occurred while applying materials: {str(e)}"
            )

    def analyze_scene_for_materials(
        self, user_input, rewritten_input, formatted_scene_info, scene_description
    ):
        prompt = f"""
        Context:
        你是一个专门分析3D场景并确定所需材质的AI助手。根据提供的场景信息和模型描述，确定需要的材质类型。

        用户原始输入：{user_input}
        改写后的要求：{rewritten_input}
        场景信息：{formatted_scene_info}
        模型描述：{json.dumps(scene_description, ensure_ascii=False, indent=2)}

        Task:
        分析场景中的每个对象，并确定所需的材质类型。考虑对象的名称、形状和可能的用途。将相同材质类型的对象分组。

        Output:
        请提供一个JSON对象，其中包含材质类型作为键，以及需要该材质的对象列表作为值。注意一些材质为blender场景自带的，例如摄像机Camera等，该类物品不需要添加材质：
        {{
            "wood": ["Table_Top", "Chair_Seat"],
            "metal": ["Table_Leg", "Chair_Frame"],
            "fabric": ["Chair_Cushion"],
            "glass": ["Lamp_Shade"]
        }}

        只需提供JSON对象，不需要其他解释。
        """
        response = generate_text_with_context(prompt)
        return json.loads(response)

    def query_material_docs(self, material_requirements):
        material_docs = {}
        for material_type in material_requirements.keys():
            query = f"材质类型：{material_type}"
            results = query_material_documentation(
                bpy.types.Scene.material_query_engine, query
            )
            material_docs[material_type] = results
        return material_docs

    def generate_and_apply_materials(
        self,
        context,
        user_input,
        rewritten_input,
        formatted_scene_info,
        scene_description,
        material_requirements,
        material_docs,
        log_dir,
    ):
        logger.info(f"材质需求： {material_requirements}")
        logger.info(f"材质文档： {material_docs}")
        prompt = f"""
        Context:
        你是一个专门为3D模型生成材质的AI助手。根据提供的材质需求和相关文档，生成Blender Python代码来创建和应用材质。
        注意，你应该且只应该生成材质，不应该修改任何场上的模型。

        注意：
        1. 不要使用 "Subsurface", "Sheen", "Emission", "Transmission", "Specular"等作为直接输入参数。这些是复合参数，需要通过其他允许的参数来实现效果。
        2. 对于颜色和向量类型的输入，请始终使用列表格式，而不是单个浮点数。例如：
        - 对于颜色输入（如Base Color, Specular Tint等），使用4个值的列表：[R, G, B, A]
        - 对于向量输入（如Normal），使用3个值的列表：[X, Y, Z]
        - 对于单一数值输入，直接使用浮点数

        场景内的部件名称等信息：{formatted_scene_info}
        用户原始输入：{user_input}
        改写后的要求：{rewritten_input}
        模型描述：{json.dumps(scene_description, ensure_ascii=False, indent=2)}
        材质需求：{json.dumps(material_requirements, ensure_ascii=False, indent=2)}
        材质文档：{json.dumps(material_docs, ensure_ascii=False, indent=2)}

        Task:
        为每个对象生成适当的材质，并创建Blender Python代码来应用这些材质。使用Principled BSDF着色器，并仅使用以下允许的输入参数：

        允许的Principled BSDF输入参数：
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
        请提供可以直接在Blender中执行的Python代码。代码应该：
        1. 为每个对象创建新的材质
        2. 设置材质的各项参数
        3. 将材质应用到相应的对象上
        4. 使用节点来创建更复杂的材质效果（如木纹、金属纹理等）

        只需提供Python代码，不需要其他解释。
        """
        material_code = generate_text_with_context(prompt)

        # 保存生成的材质代码到文件
        with open(
            os.path.join(log_dir, "material_application_code.py"), "w", encoding="utf-8"
        ) as f:
            f.write(material_code)

        # 执行生成的Blender材质命令
        try:
            execute_blender_command(material_code)
            logger.debug("Successfully applied materials.")
        except Exception as e:
            logger.error(f"Error applying materials: {str(e)}")
            self.report({"ERROR"}, f"Error applying materials: {str(e)}")

        # 更新视图
        self.update_blender_view(context)

        # 保存应用材质后的截图
        screenshots = save_screenshots()
        screenshot_dir = os.path.join(log_dir, "material_screenshots")
        save_screenshots_to_path(screenshot_dir)
        for screenshot in screenshots:
            logger.debug(f"Material application screenshot saved: {screenshot}")


class MODEL_GENERATION_PT_panel(Panel):
    bl_label = "Model Generation"
    bl_idname = "MODEL_GENERATION_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        props = context.scene.model_generation_tool

        layout.prop(props, "input_text")
        layout.operator("model_generation.generate")
        # layout.operator("model_generation.optimize_once")
        # layout.operator("model_generation.apply_materials")
