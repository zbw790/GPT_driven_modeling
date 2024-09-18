import json
import re
import bpy
from llm_driven_modelling.utils.logger_module import setup_logger
from llm_driven_modelling.llm.claude_module import generate_text_with_claude
from llm_driven_modelling.llm.LLM_common_utils import sanitize_command

logger = setup_logger("model_generation_utils")


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


def update_blender_view(context):
    # 确保更改立即可见
    bpy.context.view_layer.update()
    logger.debug("Blender view updated.")


def parse_scene_input(user_input, rewritten_input):
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
