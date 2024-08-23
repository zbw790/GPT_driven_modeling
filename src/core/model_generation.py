# model_generation.py

import bpy
import json
import re
import os
from typing import List, Dict, Any
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty
from src.llm_modules.claude_module import generate_text_with_claude, analyze_screenshots_with_claude
from src.llm_modules.LLM_common_utils import sanitize_command, initialize_conversation, execute_blender_command, add_history_to_prompt, get_screenshots, get_scene_info, format_scene_info, execute_blender_command_with_error_handling
from src.utils.logger_module import setup_logger, log_context
from src.core.prompt_rewriter import rewrite_prompt
from src.llm_modules.gpt_module import generate_text_with_context, analyze_screenshots_with_gpt4
from src.llama_index_modules.llama_index_model_generation import query_generation_documentation
from src.llama_index_modules.llama_index_model_modification import query_modification_documentation
from src.llama_index_modules.llama_index_component_library import query_component_documentation
from src.core.evaluators_module import ModelEvaluator, EvaluationStatus
from src.utils.model_viewer_module import save_screenshots, save_screenshots_to_path
from src.llama_index_modules.llama_index_material_library import query_material_documentation

# 创建专门的日志记录器
logger = setup_logger('model_generation')

class ModelGenerationProperties(PropertyGroup):
    input_text: StringProperty(
        name="Model Description",
        description="Describe the model you want to generate",
        default=""
    )

def parse_user_input(user_input, rewritten_input):
    prompt = f"""
    Context:
    你是一个专门用于解析和重构用户输入的AI助手。工作在一个3D建模系统中。你的主要任务是处理用户提供的各种物品描述，这些描述可能涉及家具、建筑结构、日常用品，甚至是抽象概念的具象化。
    你的任务是将用户的描述转化为结构化的JSON数据，以便后续的建模功能使用。

    Objective:
    将用户的原始描述和重写后的提示词转换为标准化的JSON格式，包含物品类型和核心组件的详细信息。

    Style:
    - 分析性：仔细识别物品的核心组件和关键特征
    - 结构化：将信息组织成规定的JSON格式
    - 精确：提供准确的数量和尺寸信息
    - 简洁：只包含定义物品基本形态和功能的必要信息

    Tone:
    - 专业：使用准确的术语描述形状和尺寸
    - 客观：基于给定信息进行合理推断，不添加主观臆测
    - 直接：直接提供所需的JSON数据，不包含额外解释

    Audience:
    - 主要面向后续的3D建模系统或算法
    - 可能包括需要处理这些数据的开发人员或设计师

    Response:
    请提供一个JSON对象，包含以下元素：
    1. object_type: 物品类型
    2. components: 核心组件列表，每个组件包含：
      - name: 部件名称
      - quantity: 数量
      - shape: 形状描述，以下是一些列子，但不仅限于此，其他例如圆锥体等的许多形状未列出，请根据情况自行判断并添加对应的专有名词描述：
         - "cuboid": 对于长方体，包含长宽高
         - "cylinder": 对于圆柱体，包含半径和高度
         - "sphere": 对于球体，包含半径
         - "custom": 对于异形，包含简洁的形状描述
      - dimensions: 根据形状提供的尺寸信息

    输入:
    用户原始输入: {user_input}
    解析后的提示词：{rewritten_input}

    输出格式示例:
    {{
      "object_type": "书桌",
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
        }},
        {{
          "name": "抽屉",
          "quantity": 2,
          "shape": "cuboid",
          "dimensions": {{
            "length": 40,
            "width": 50,
            "height": 15
          }}
        }}
      ]
    }}

    注意事项:
    1. 只识别并列出定义物品基本结构和核心功能的必要部件。
    2. 如果某些信息缺失，请根据常识进行合理推断。
    3. 简化结构，避免列出不必要的装饰性或次要部件。
    4. 对于简单物品（如桌子、椅子），通常只需要主体和支撑部分。
    5. 对于功能性物品（如书桌、衣柜），包含核心功能部件（如抽屉、柜门）。
    6. 省略纯装饰性元素、内部支撑结构或不影响整体形态的次要部件。
    7. 形状描述不仅限于示例中给出的类型，可根据需要使用其他适当的形状描述（如"cone"表示圆锥体等）。
    """
    
    logger.info(f"Sending prompt to Claude: {prompt}")
    response = generate_text_with_claude(prompt)
    logger.info(f"Received response from Claude: {response}")
    
    response = sanitize_command(response)
    response = sanitize_reference(response)
    return json.loads(response)

def sanitize_reference(response):
    """
    从Claude的响应中提取JSON数据，去除注释和其他非JSON内容。
    """
    json_match = re.search(r'\{[\s\S]*\}', response)
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
    bl_label = "Generate Model"
    bl_description = "Generate a 3D model based on the description"

    def execute(self, context):
        props = context.scene.model_generation_tool
        user_input = props.input_text

        with log_context(logger, user_input) as log_dir:
            try:
                logger.info("Rewriting user input")
                rewritten_input = rewrite_prompt(user_input)
                logger.info(f"Rewritten input: {rewritten_input}")
                
                logger.info("Parsing rewritten user input")
                model_description = parse_user_input(user_input, rewritten_input)
                logger.info("Model Description:")
                logger.info(json.dumps(model_description, ensure_ascii=False, indent=2))
                
                # Save model description to file
                with open(os.path.join(log_dir, "model_description.json"), "w", encoding='utf-8') as f:
                    json.dump(model_description, f, ensure_ascii=False, indent=2)
                
                # Generate 3D model using GPT
                self.generate_3d_model(context, user_input, rewritten_input, model_description, log_dir)

                # 评估并优化模型
                self.evaluate_and_optimize_model(context, user_input, rewritten_input, model_description, log_dir)

                # 添加新的材质应用步骤
                self.apply_materials(context, user_input, rewritten_input, model_description, log_dir)

                logger.debug(f"Log directory: {log_dir}")
                # 保存当前场景的屏幕截图
                screenshot_path = os.path.join(log_dir, "model_screenshot.png")
                bpy.ops.screen.screenshot(filepath=screenshot_path)
                logger.debug(f"Screenshot saved to {screenshot_path}")
                
                self.report({'INFO'}, f"Model generated and optimized for {model_description['object_type']}. Logs saved in {log_dir}")
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                self.report({'ERROR'}, f"An error occurred: {str(e)}")
        
        return {'FINISHED'}

    def generate_3d_model(self, context, user_input, rewritten_input, model_description, log_dir):
        # 查询必要文件
        logger.info("Querying generation documentation")
        generation_docs = query_generation_documentation(bpy.types.Scene.generation_query_engine, rewritten_input)
        logger.info(f"Generation documentation: {generation_docs}")

        # 查询部件库
        component_docs = self.query_component_library(model_description)
        logger.info(f"Component library documentation: {component_docs}")

        # 准备提示信息
        prompt = f"""
        Context:
        你是一个专门用于生成Blender Python命令的AI助手，负责创建3D模型。你需要根据用户的描述和相关文档生成适当的Python代码。

        用户原始输入的要求：{user_input}
        改写后的要求：{rewritten_input}
        模型描述（JSON格式）：{json.dumps(model_description, ensure_ascii=False, indent=2)}
        相关生成文档：{generation_docs}
        部件库文档：{component_docs}

        Objective:
        生成适当的Blender Python命令来创建指定的3D模型。代码应该准确反映用户的需求，并遵循Blender API的最佳实践。同时，参考部件库文档中的指南来创建各个部件。

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
        with open(os.path.join(log_dir, "generated_blender_code.py"), "w", encoding='utf-8') as f:
            f.write(response)

        # 执行生成的Blender命令
        error_message = execute_blender_command_with_error_handling(response)
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
            with open(os.path.join(log_dir, "corrected_blender_code.py"), "w", encoding='utf-8') as f:
                f.write(corrected_response)
            
            # 尝试执行修正后的代码
            error_message = execute_blender_command_with_error_handling(corrected_response)
            if error_message:
                logger.error(f"Error executing corrected Blender commands: {error_message}")
                self.report({'ERROR'}, f"Error executing corrected Blender commands: {error_message}")
            else:
                logger.debug("Successfully executed corrected Blender commands.")
        else:
            logger.debug("Successfully executed Blender commands.")

        # 更新视图并等待一小段时间以确保视图已更新
        self.update_blender_view(context)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        # 更新resources内的截图
        screenshots = save_screenshots()
        screenshot_dir = os.path.join(log_dir, "generation_screenshots")
        save_screenshots_to_path(screenshot_dir)
        for screenshot in screenshots:
            logger.debug(f"Generation screenshot saved: {screenshot}")

    def query_component_library(self, model_description):
        component_docs = []
        for component in model_description.get('components', []):
            component_name = component.get('name', '')
            if component_name:
                results = query_component_documentation(bpy.types.Scene.component_query_engine, component_name)
                component_docs.extend(results)
        return "\n\n".join(component_docs)

    def update_blender_view(self, context):
        # 确保更改立即可见
        bpy.context.view_layer.update()
        logger.debug("Blender view updated.")
    
    def evaluate_and_optimize_model(self, context, user_input, rewritten_input, model_description, log_dir):
        max_iterations = 5  # 设置最大迭代次数
        iteration = 0
        
        while iteration < max_iterations:
            # 为每次迭代创建一个新的子目录
            iteration_dir = os.path.join(log_dir, f"iteration_{iteration + 1}")
            os.makedirs(iteration_dir, exist_ok=True)

            screenshots = get_screenshots()

            evaluator = ModelEvaluator()
            
            evaluation_context = {
                "user_input": user_input,
                "rewritten_input": rewritten_input,
                "model_description": model_description
            }
            
            results = evaluator.evaluate(screenshots, evaluation_context)
            combined_analysis, final_status, average_score, suggestions = evaluator.aggregate_results(results)
            # 整合并剔除不必要的建议
            filtered_suggestions = self.filter_and_consolidate_suggestions(suggestions, evaluation_context)
            # 提取优先建议
            priority_suggestions = filtered_suggestions.get('priority_suggestions', [])

            logger.info(f"Iteration {iteration + 1}: Status: {final_status.name}, Score: {average_score:.2f}")
            logger.info(f"Combined Analysis: {combined_analysis}")
            logger.info("Suggestions:")
            logger.info(f"- {suggestions}")
            logger.info(f"Priority Suggestions: {priority_suggestions}")

            # 保存评估结果到文件
            with open(os.path.join(iteration_dir, "evaluation_results.json"), "w", encoding='utf-8') as f:
                json.dump({
                    "iteration": iteration + 1,
                    "status": final_status.name,
                    "score": average_score,
                    "analysis": combined_analysis,
                    "suggestions": suggestions,
                    "priority_suggestions": priority_suggestions
                }, f, ensure_ascii=False, indent=2)

            # 如果模型满意或达到最大迭代次数，退出循环
            if final_status == EvaluationStatus.PASS or iteration == max_iterations - 1:
                break

            # 否则，继续优化模型
            self.optimize_model(context, priority_suggestions, evaluation_context, screenshots, iteration_dir, iteration)
            iteration += 1

        if final_status == EvaluationStatus.PASS:
            logger.info(f"Model optimization completed successfully after {iteration + 1} iterations.")
            self.report({'INFO'}, f"Model optimized successfully after {iteration + 1} iterations.")
        else:
            logger.warning(f"Model optimization did not reach satisfactory results after {max_iterations} iterations.")
            self.report({'WARNING'}, f"Model optimization completed with suboptimal results after {max_iterations} iterations.")

        # 保存最终模型的截图
        final_screenshots = save_screenshots()
        final_screenshot_dir = os.path.join(log_dir, "final_model")
        save_screenshots_to_path(final_screenshot_dir)
        for screenshot in final_screenshots:
            logger.debug(f"Final model screenshot saved: {screenshot}")

    def filter_and_consolidate_suggestions(self, suggestions, evaluation_context):
        screenshots = get_screenshots()

        prompt = f"""
        Context:
        你是一个专门负责整合用于优化3D模型的建议的AI助手，你根据图片和需要分析所有的建议，并从中选出需要保留的建议留下。

        原始用户输入：{evaluation_context['user_input']}
        改写后的要求：{evaluation_context['rewritten_input']}
        模型描述：{json.dumps(evaluation_context['model_description'], ensure_ascii=False, indent=2)}
        优化建议：{suggestions}

        Objective:
        该模型生成任务只需要生成模型的草模即可，换句话说就是模型只要长得像就算达到目标，不需要去追求更细节的改变。
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
                "建议2",
                "建议3"
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

    def optimize_model(self, context, priority_suggestions, evaluation_context, screenshots, iteration_dir, iteration):
        # 查询每个优先建议的相关文档
        suggestion_docs = self.query_suggestion_docs(priority_suggestions)

        # 获取场景信息
        scene_info = get_scene_info()
        formatted_scene_info = format_scene_info(scene_info)
        logger.info(f"场景内的模型信息: {formatted_scene_info}")

        # 准备优化提示
        prompt = f"""
        Context:
        你是一个专门负责优化3D模型的AI助手。你的任务是根据给定的信息和建议,生成Blender Python命令来优化现有的3D模型。

        原始用户输入：{evaluation_context['user_input']}
        改写后的要求：{evaluation_context['rewritten_input']}
        模型描述：{json.dumps(evaluation_context['model_description'], ensure_ascii=False, indent=2)}
        优化建议：{json.dumps(priority_suggestions, ensure_ascii=False, indent=2)}
        相关优化文档：{json.dumps(suggestion_docs, ensure_ascii=False, indent=2)}
        以下是场景中所有存在的对象的详细信息：{formatted_scene_info}

        Objective:
        生成Blender Python命令来优化现有的3D模型,同时保持模型的基本结构和特征。主要任务是优化模型,而不是创建全新的模型。只有在现有模型的某些部分完全不可用时,才考虑删除并重新生成。

        Style:
        - 精确：使用准确的Blender Python命令
        - 简洁：只包含必要的代码,不添加多余的注释或解释
        - 结构化：按照逻辑顺序组织代码

        Tone:
        - 专业：使用Blender API的专业术语和函数
        - 直接：直接给出代码,不需要额外的解释
        - 技术性：专注于技术实现,不需要解释代码的意图

        Audience:
        熟悉Blender Python API的3D建模工程师和开发人员

        Response:
        请提供优化3D模型的Blender Python代码。代码应该：
        1. 使用bpy库来修改现有对象
        2. 只修改需要优化的部分,保留其他部分不变
        3. 确保优化后的模型符合原始描述和要求
        4. 如果需要添加新组件,确保它们与现有组件协调
        5. 除非绝对必要,不要删除现有模型并生成全新模型

        请直接返回Python代码,不需要其他解释或注释。
        """
        logger.info(f"相关优化文档： {suggestion_docs}")

        # 使用 GPT 生成优化命令
        conversation_manager = context.scene.conversation_manager
        initialize_conversation(context)
        prompt_with_history = add_history_to_prompt(context, prompt)
        
        if iteration % 2 == 0:
            response = analyze_screenshots_with_claude(prompt_with_history, screenshots)
        else:
            response = analyze_screenshots_with_gpt4(prompt_with_history, screenshots)

        # 更新对话历史
        conversation_manager.add_message("user", prompt)
        conversation_manager.add_message("assistant", response)

        logger.info(f"GPT Generated Optimization Commands:\n```python\n{response}\n```")

        # 保存生成的优化代码到文件
        with open(os.path.join(iteration_dir, "optimization_code.py"), "w", encoding='utf-8') as f:
            f.write(response)

        # 执行生成的Blender优化命令
        error_message = execute_blender_command_with_error_handling(response)
        if error_message:
            logger.error(f"Error executing optimization commands: {error_message}")
            
            # 准备新的提示，包含错误信息
            error_prompt = f"""
            之前的prompt:{prompt}
            在执行之前生成的Blender优化命令时发生了错误。以下是错误信息：

            {error_message}

            请根据这个错误信息修改之前生成的代码。确保新生成的代码能够正确执行，并避免之前的错误。

            之前生成的代码：
            {response}

            请提供修正后的Blender Python代码。
            """
            
            # 使用 GPT 生成修正后的代码
            corrected_response = generate_text_with_context(error_prompt)
            
            logger.info(f"GPT Generated Corrected Optimization Commands:\n{corrected_response}")
            
            # 保存修正后的代码到文件
            with open(os.path.join(iteration_dir, "corrected_optimization_code.py"), "w", encoding='utf-8') as f:
                f.write(corrected_response)
            
            # 尝试执行修正后的代码
            error_message = execute_blender_command_with_error_handling(corrected_response)
            if error_message:
                logger.error(f"Error executing corrected optimization commands: {error_message}")
                self.report({'ERROR'}, f"Error executing corrected optimization commands: {error_message}")
            else:
                logger.debug("Successfully executed corrected optimization commands.")
        else:
            logger.debug("Successfully executed optimization commands.")

        # 更新视图并等待一小段时间以确保视图已更新
        self.update_blender_view(context)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        # 保存当前迭代的截图
        screenshots = save_screenshots()
        screenshot_dir = os.path.join(iteration_dir, "evaluation_screenshots")
        save_screenshots_to_path(screenshot_dir)
        for screenshot in screenshots:
            logger.debug(f"Iteration {iteration + 1} evaluation screenshot saved: {screenshot}")

    def query_suggestion_docs(self, suggestions):
        all_docs = []

        for suggestion in suggestions:
            results = query_modification_documentation(bpy.types.Scene.modification_query_engine, suggestion)
            all_docs.extend(results)

        return all_docs
    
    def apply_materials(self, context, user_input, rewritten_input, model_description, log_dir):
        try:
            # 获取场景信息
            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)

            # 步骤1：分析场景信息并确定所需的材质
            material_requirements = self.analyze_scene_for_materials(user_input, rewritten_input, formatted_scene_info, model_description)
            logger.info(f"材质需求： {material_requirements}")

            # 步骤2：查询相关的材质文档
            material_docs = self.query_material_docs(material_requirements)
            logger.info(f"材质文档： {material_docs}")

            # 步骤3：生成并应用材质
            self.generate_and_apply_materials(context, user_input, rewritten_input, formatted_scene_info, model_description, material_requirements, material_docs, log_dir)

            self.report({'INFO'}, f"Materials applied successfully. Logs saved in {log_dir}")
        except Exception as e:
            logger.error(f"An error occurred while applying materials: {str(e)}")
            self.report({'ERROR'}, f"An error occurred while applying materials: {str(e)}")

    def analyze_scene_for_materials(self, user_input, rewritten_input, formatted_scene_info, model_description):
        prompt = f"""
        Context:
        你是一个专门分析3D场景并确定所需材质的AI助手。根据提供的场景信息和模型描述，确定每个对象需要的材质类型。

        用户原始输入：{user_input}
        改写后的要求：{rewritten_input}
        场景信息：{formatted_scene_info}
        模型描述：{json.dumps(model_description, ensure_ascii=False, indent=2)}

        Task:
        分析场景中的每个对象，并确定它们可能需要的材质类型。考虑对象的名称、形状和可能的用途。

        Output:
        请提供一个JSON对象，其中包含每个对象的名称作为键，以及建议的材质类型作为值,注意一些材质为blender场景自带的，例如摄像机Camera等，该类物品不需要添加材质：
        {{
            "Table_Top": "wood",
            "Table_Leg": "metal",
            "Chair_Seat": "fabric",
            "Lamp_Shade": "glass"
        }}

        只需提供JSON对象，不需要其他解释。
        """
        response = generate_text_with_claude(prompt)
        return json.loads(response)

    def query_material_docs(self, material_requirements):
        material_docs = {}
        unique_docs = set()  # 用于存储唯一的文档

        for obj_name, material_type in material_requirements.items():
            query = f"材质类型：{material_type}"
            results = query_material_documentation(bpy.types.Scene.material_query_engine, query)
            
            # 过滤并只添加唯一的文档
            unique_results = []
            for result in results:
                if result not in unique_docs:
                    unique_docs.add(result)
                    unique_results.append(result)
            
            material_docs[obj_name] = unique_results

        # 将所有唯一的文档合并为一个列表
        all_unique_docs = list(unique_docs)

        return all_unique_docs

    def generate_and_apply_materials(self, context, user_input, rewritten_input, formatted_scene_info, model_description, material_requirements, material_docs, log_dir):
        logger.info(f"材质需求： {material_requirements}")
        logger.info(f"材质文档： {material_docs}")
        prompt = f"""
        Context:
        你是一个专门为3D模型生成材质的AI助手。根据提供的材质需求和相关文档，生成Blender Python代码来创建和应用材质。

        注意：
        1. 不要使用 "Subsurface", "Sheen", "Emission", "Transmission" 等作为直接输入参数。这些是复合参数，需要通过其他允许的参数来实现效果。
        2. 对于颜色和向量类型的输入，请始终使用列表格式，而不是单个浮点数。例如：
        - 对于颜色输入（如Base Color, Specular Tint等），使用4个值的列表：[R, G, B, A]
        - 对于向量输入（如Normal），使用3个值的列表：[X, Y, Z]
        - 对于单一数值输入，直接使用浮点数

        场景内的部件名称等信息：{formatted_scene_info}
        用户原始输入：{user_input}
        改写后的要求：{rewritten_input}
        模型描述：{json.dumps(model_description, ensure_ascii=False, indent=2)}
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
        material_code = generate_text_with_claude(prompt)

        # 保存生成的材质代码到文件
        with open(os.path.join(log_dir, "material_application_code.py"), "w", encoding='utf-8') as f:
            f.write(material_code)

        # 执行生成的Blender材质命令
        try:
            execute_blender_command(material_code)
            logger.debug("Successfully applied materials.")
        except Exception as e:
            logger.error(f"Error applying materials: {str(e)}")
            self.report({'ERROR'}, f"Error applying materials: {str(e)}")

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
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        props = context.scene.model_generation_tool

        layout.prop(props, "input_text")
        layout.operator("model_generation.generate")
        # layout.operator("model_generation.optimize_once")
        # layout.operator("model_generation.apply_materials")