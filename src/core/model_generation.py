# model_generation.py

import bpy
import json
import re
import os
from typing import List, Dict, Any
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty
from src.llm_modules.claude_module import generate_text_with_claude, analyze_screenshots_with_claude
from src.llm_modules.LLM_common_utils import sanitize_command, initialize_conversation, execute_blender_command, add_history_to_prompt, get_screenshots
from src.utils.logger_module import setup_logger, log_context
from src.core.prompt_rewriter import rewrite_prompt
from src.llm_modules.gpt_module import generate_text_with_context
from src.llama_index_modules.llama_index_model_generation import query_generation_documentation
from src.llama_index_modules.llama_index_model_modification import query_modification_documentation
from src.core.evaluators_module import ModelEvaluator, EvaluationStatus
from src.utils.model_viewer_module import save_screenshots

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

                # 评估模型
                self.evaluate_and_optimize_model(context, user_input, rewritten_input, model_description, log_dir)

                logger.info(f"Log directory: {log_dir}")
                # 保存当前场景的屏幕截图
                screenshot_path = os.path.join(log_dir, "model_screenshot.png")
                bpy.ops.screen.screenshot(filepath=screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
                
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

        # 准备提示信息
        prompt = f"""
        请根据以下信息生成Blender Python命令来创建3D模型：

        用户原始输入的要求：{user_input}
        改写后的要求：{rewritten_input}
        模型描述（JSON格式）：{json.dumps(model_description, ensure_ascii=False, indent=2)}
        相关生成文档：{generation_docs}

        请生成适当的Blender Python命令来创建这个3D模型。注意以下几点：
        1. 使用 bpy 库来创建和操作对象。
        2. 为每个组件创建单独的对象，并根据其形状和尺寸进行设置。
        3. 正确放置每个组件，确保它们的相对位置正确。
        4. 如果需要，可以使用循环来创建重复的组件（如多个桌腿）。
        5. 为生成的对象设置合适的名称，以便于识别。
        6. 如果需要，可以添加简单的材质。
        7. 生成正确的集合以便于模型管理。

        请只返回Python代码，不需要其他解释。
        """

        # 使用 GPT 生成响应
        conversation_manager = context.scene.conversation_manager
        initialize_conversation(context)
        prompt_with_history = add_history_to_prompt(context, prompt)
        response = generate_text_with_context(prompt_with_history)

        # 更新对话历史
        conversation_manager.add_message("user", prompt)
        conversation_manager.add_message("assistant", response)

        logger.info(f"GPT Generated Commands for 3D Model: {response}")

        # 保存生成的代码到文件
        with open(os.path.join(log_dir, "generated_blender_code.py"), "w", encoding='utf-8') as f:
            f.write(response)

        # 执行生成的Blender命令
        try:
            execute_blender_command(response)
            logger.info("Successfully executed Blender commands.")
        except Exception as e:
            logger.error(f"Error executing Blender commands: {str(e)}")
            self.report({'ERROR'}, f"Error executing Blender commands: {str(e)}")

        # 更新视图并等待一小段时间以确保视图已更新
        self.update_blender_view(context)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        # 更新resources内的截图
        save_screenshots()


    def update_blender_view(self, context):
        # 确保更改立即可见
        bpy.context.view_layer.update()
        logger.info("Blender view updated.")


    def evaluate_and_optimize_model(self, context, user_input, rewritten_input, model_description, log_dir):
        screenshots = get_screenshots()
        evaluator = ModelEvaluator()
        
        evaluation_context = {
            "user_input": user_input,
            "rewritten_input": rewritten_input,
            "model_description": model_description
        }
        
        results = evaluator.evaluate(screenshots, evaluation_context)
        
        combined_analysis, final_status, average_score, suggestions = evaluator.aggregate_results(results)

        logger.info(f"Evaluation results: Status: {final_status.name}, Score: {average_score:.2f}")
        logger.info(f"Combined Analysis: {combined_analysis}")
        logger.info("Suggestions:")
        for suggestion in suggestions:
            logger.info(f"- {suggestion}")

        # 如果模型不满意，尝试优化
        if final_status == EvaluationStatus.NOT_PASS:
            self.optimize_model(context, suggestions, evaluation_context, log_dir)
            # print("不满意")

    
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
                "将桌面与桌腿连接，确保结构的完整性",
                "调整桌腿的位置，使其位于桌面四个角落，提供更好的稳定性"
            ],
            "secondary_suggestions": [
                "考虑增加桌面厚度至4-5厘米，以提高视觉上的稳定性",
                "将桌腿直径增加到6-8厘米，以更好地支撑桌面"
            ],
        }}
        """
        response = analyze_screenshots_with_claude(prompt, screenshots)
        response = sanitize_command(response)
        response = sanitize_reference(response)
        return json.loads(response)


    def optimize_model(self, context, suggestions, evaluation_context, log_dir):

        # 整合并剔除不必要的建议
        filtered_suggestions  = self.filter_and_consolidate_suggestions(suggestions, evaluation_context)

        # 提取优先建议
        priority_suggestions = filtered_suggestions.get('priority_suggestions', [])

        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",filtered_suggestions)
        print("YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",priority_suggestions)

        priority_suggestions_str = "\n".join(priority_suggestions)

        # 查询必要文件
        logger.info("Querying modification documentation")
        modification_docs = query_modification_documentation(bpy.types.Scene.modification_query_engine, priority_suggestions_str)
        logger.info(f"modification documentation: {modification_docs}")

        # 准备优化提示
        prompt = f"""
        请根据以下信息优化现有的3D模型：

        原始用户输入：{evaluation_context['user_input']}
        改写后的要求：{evaluation_context['rewritten_input']}
        模型描述：{json.dumps(evaluation_context['model_description'], ensure_ascii=False, indent=2)}
        优化建议：{chr(10).join(f"- {suggestion}" for suggestion in priority_suggestions)}
        相关优化文档：{modification_docs}

        请生成Blender Python命令来优化这个3D模型。注意：
        1. 使用 bpy 库来修改现有对象。
        2. 仅修改需要优化的部分，保留其他部分不变。
        3. 确保优化后的模型仍然符合原始描述和要求。
        4. 如果需要添加新的组件，请确保它们与现有组件协调。

        请只返回Python代码，不需要其他解释。
        """

        # 使用 GPT 生成优化命令
        conversation_manager = context.scene.conversation_manager
        initialize_conversation(context)
        prompt_with_history = add_history_to_prompt(context, prompt)
        response = generate_text_with_context(prompt_with_history)

        # 更新对话历史
        conversation_manager.add_message("user", prompt)
        conversation_manager.add_message("assistant", response)

        logger.info(f"GPT Generated Optimization Commands: {response}")

        # 保存生成的优化代码到文件
        with open(os.path.join(log_dir, "optimization_code.py"), "w", encoding='utf-8') as f:
            f.write(response)

        # 执行生成的Blender优化命令
        try:
            execute_blender_command(response)
            logger.info("Successfully executed optimization commands.")
        except Exception as e:
            logger.error(f"Error executing optimization commands: {str(e)}")
            self.report({'ERROR'}, f"Error executing optimization commands: {str(e)}")

        # 更新视图并等待一小段时间以确保视图已更新
        self.update_blender_view(context)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            

class MODEL_GENERATION_OT_optimize_once(Operator):
    bl_idname = "model_generation.optimize_once"
    bl_label = "Optimize Model Once"
    bl_description = "Perform one iteration of model optimization"

    def execute(self, context):
        props = context.scene.model_generation_tool
        user_input = props.input_text

        with log_context(logger, "model_optimization") as log_dir:
            try:
                # 重新获取模型描述（如果需要的话）
                rewritten_input = rewrite_prompt(user_input)
                model_description = parse_user_input(user_input, rewritten_input)

                # 评估和优化模型
                self.evaluate_and_optimize_model(context, user_input, rewritten_input, model_description, log_dir)

                self.report({'INFO'}, "Model optimization iteration completed.")
                return {'FINISHED'}
            except Exception as e:
                logger.error(f"Error during optimization: {str(e)}")
                self.report({'ERROR'}, f"Error during optimization: {str(e)}")
                return {'CANCELLED'}

    def evaluate_and_optimize_model(self, context, user_input, rewritten_input, model_description, log_dir):
        screenshots = get_screenshots()
        evaluator = ModelEvaluator()
        
        evaluation_context = {
            "user_input": user_input,
            "rewritten_input": rewritten_input,
            "model_description": model_description
        }
        
        results = evaluator.evaluate(screenshots, evaluation_context)
        
        combined_analysis, final_status, average_score, suggestions = evaluator.aggregate_results(results)

        logger.info(f"Evaluation results: Status: {final_status.name}, Score: {average_score:.2f}")
        logger.info(f"Combined Analysis: {combined_analysis}")
        logger.info("Suggestions:")
        for suggestion in suggestions:
            logger.info(f"- {suggestion}")

        # 无论评估结果如何，都尝试优化
        self.optimize_model(context, suggestions, evaluation_context, log_dir)

    def optimize_model(self, context, suggestions, evaluation_context, log_dir):
        # 准备优化提示
        prompt = f"""
        请根据以下信息优化现有的3D模型：

        原始用户输入：{evaluation_context['user_input']}
        改写后的要求：{evaluation_context['rewritten_input']}
        模型描述：{json.dumps(evaluation_context['model_description'], ensure_ascii=False, indent=2)}
        优化建议：
        {chr(10).join(f"- {suggestion}" for suggestion in suggestions)}

        请生成Blender Python命令来优化这个3D模型。注意：
        1. 使用 bpy 库来修改现有对象。
        2. 仅修改需要优化的部分，保留其他部分不变。
        3. 确保优化后的模型仍然符合原始描述和要求。
        4. 如果需要添加新的组件，请确保它们与现有组件协调。

        请只返回Python代码，不需要其他解释。
        """

        # 使用 GPT 生成优化命令
        conversation_manager = context.scene.conversation_manager
        initialize_conversation(context)
        prompt_with_history = add_history_to_prompt(context, prompt)
        response = generate_text_with_context(prompt_with_history)

        # 更新对话历史
        conversation_manager.add_message("user", prompt)
        conversation_manager.add_message("assistant", response)

        logger.info(f"GPT Generated Optimization Commands: {response}")

        # 保存生成的优化代码到文件
        with open(os.path.join(log_dir, "generated_optimization_code.py"), "w", encoding='utf-8') as f:
            f.write(response)

        # 执行生成的Blender优化命令
        try:
            execute_blender_command(response)
            logger.info("Successfully executed optimization commands.")
        except Exception as e:
            logger.error(f"Error executing optimization commands: {str(e)}")
            self.report({'ERROR'}, f"Error executing optimization commands: {str(e)}")

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
        layout.operator("model_generation.optimize_once")
