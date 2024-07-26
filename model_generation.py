# model_generation.py

import bpy
import json
import re
import os
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty
from claude_module import generate_text_with_claude
from LLM_common_utils import sanitize_command
from logger_module import setup_logger, log_context
from prompt_rewriter import rewrite_prompt

# 创建专门的日志记录器
logger = setup_logger('model_generation')

class ModelGenerationProperties(PropertyGroup):
    input_text: StringProperty(
        name="Model Description",
        description="Describe the model you want to generate",
        default=""
    )

def parse_user_input(user_input):
    prompt = f"""
    请解析以下用户输入，并生成一个JSON格式的结构化数据。
    输入: {user_input}
    
    要求:
    1. 识别出需要生成的物品类型
    2. 只识别并列出定义物品基本结构和核心功能的必要部件
    3. 对于每个必要部件，提供名称、数量和形状信息
    4. 如果某些信息缺失，请根据常识进行合理推断
    5. 简化结构，避免列出不必要的装饰性或次要部件
    6. 输出格式应该是一个列表，每个元素代表一个核心部件，包含以下字段：
       - name: 部件名称
       - quantity: 数量
       - shape: 形状描述，以下是一些列子，但不仅限于此，其他例如圆锥体等的许多形状未列出，请根据情况自行判断并添加对应的专有名词描述：
         - "cuboid": 对于长方体，包含长宽高
         - "cylinder": 对于圆柱体，包含半径和高度
         - "sphere": 对于球体，包含半径
         - "custom": 对于异形，包含简洁的形状描述
       - dimensions: 根据形状包含相应的必要尺寸信息

    注意：
    - 只包含定义物品基本形态和功能的核心部件
    - 对于简单物品（如家具中的桌子、椅子），通常只需要主体和支撑部分
    - 对于功能性物品（如书桌、衣柜），包含核心功能部件（如抽屉、柜门）
    - 省略纯装饰性元素、内部支撑结构或不影响整体形态的次要部件

    示例输出格式:
    {{
      "furniture_type": "书桌",
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
    """
    
    logger.info(f"Sending prompt to Claude: {prompt}")
    response = generate_text_with_claude([], prompt)
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
                model_description = parse_user_input(rewritten_input)
                logger.info("Model Description:")
                logger.info(json.dumps(model_description, ensure_ascii=False, indent=2))
                
                # Save model description to file
                with open(os.path.join(log_dir, "model_description.json"), "w", encoding='utf-8') as f:
                    json.dump(model_description, f, ensure_ascii=False, indent=2)
                
                # TODO: 根据model_description生成实际的3D模型
                # 这里需要实现具体的模型生成逻辑
                
                # 保存当前场景的屏幕截图
                screenshot_path = os.path.join(log_dir, "model_screenshot.png")
                bpy.ops.screen.screenshot(filepath=screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
                
                self.report({'INFO'}, f"Model generated for {model_description['furniture_type']}. Logs saved in {log_dir}")
            except json.JSONDecodeError:
                logger.error("Failed to parse the model description.")
                self.report({'ERROR'}, "Failed to parse the model description.")
            except KeyError as e:
                logger.error(f"Missing key in model description: {str(e)}")
                self.report({'ERROR'}, f"Missing key in model description: {str(e)}")
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                self.report({'ERROR'}, f"An error occurred: {str(e)}")
        
        return {'FINISHED'}

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