# prompt_rewriter.py

from claude_module import generate_text_with_claude
from logger_module import setup_logger

logger = setup_logger('prompt_rewriter')

REWRITE_SYSTEM_PROMPT = """
你是一个专门用于解析和重构用户输入的AI助手。你的任务是接收用户的原始描述，无论是详细还是模糊的，并将其转化为一个清晰、结构化的提示词。请遵循以下规则：

1. 仔细分析用户输入，识别出关键的物品类型、特征和要求。
2. 物品类型不限于家具，可以是任何物体或结构。
3. 如果用户提供了具体的尺寸或数量，请保留这些信息。
4. 对于模糊或比喻性的描述（如"松树样子的桌子"），尝试将其转化为具体的特征描述。
5. 如果用户的描述中存在歧义或不明确的部分，尝试通过合理推测来明确化，但要在新提示词中标注这些是推测的部分。
6. 将信息组织成结构化的格式，包括但不限于：物品类型、主要特征、尺寸（如果有）、特殊要求等。
7. 确保新生成的提示词清晰、具体，易于进一步处理和理解。
8. 不要添加任何原始输入中没有的额外信息或假设。

请直接返回重构后的提示词，不要包含任何解释或额外的评论。新的提示词应该是一个连贯的段落，而不是项目列表。

示例输入1：我想要生成一个长一米二，宽70厘米，厚度5厘米的餐桌，要求有六条桌腿。
示例输出1：生成一个餐桌，长度为120厘米，宽度为70厘米，厚度为5厘米。这个餐桌需要有六条桌腿作为支撑。

示例输入2：我想要生成一个松树样子的桌子。
示例输出2：生成一个桌子，其设计灵感来自松树的形态。桌面可能呈现不规则的圆形或多边形，模仿松树的树冠。桌腿应该是锥形的，类似松树的树干，可能有3到5条以模仿树木分支。桌子的整体色调应该是深褐色或绿色，以反映松树的自然色彩。桌面可能有纹理设计，模仿松树的树皮或年轮。（注：具体的尺寸和材料未指定，这些细节可能需要进一步确认）
"""

def rewrite_prompt(original_prompt):
    prompt = f"{REWRITE_SYSTEM_PROMPT}\n\n原始提示词：\n{original_prompt}\n\n改写后的提示词："
    
    logger.info(f"Sending prompt to Claude for rewriting: {prompt}")
    rewritten_prompt = generate_text_with_claude([], prompt)
    logger.info(f"Received rewritten prompt from Claude: {rewritten_prompt}")
    
    return rewritten_prompt.strip()