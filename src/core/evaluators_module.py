# evaluators_module.py

import bpy
from bpy.types import Operator, Panel
from abc import ABC, abstractmethod
from src.llm_modules.gpt_module import analyze_screenshots_with_gpt4
from src.llm_modules.claude_module import analyze_screenshots_with_claude
from typing import List, Dict, Any, Tuple
from enum import Enum
from src.llm_modules.LLM_common_utils import get_screenshots
from src.utils.logger_module import setup_logger, log_context
import json
import re

# 创建专门的日志记录器
logger = setup_logger('model_generation')

class EvaluationStatus(Enum):
    NOT_PASS = 0
    PASS = 1
    GOOD = 2

class EvaluationResult:
    def __init__(self, analysis: str, status: EvaluationStatus, score: float, suggestions: List[str]):
        self.analysis = analysis
        self.status = status
        self.score = score
        self.suggestions = suggestions

    def __str__(self):
        return f"Analysis: {self.analysis}\nStatus: {self.status.name}, Score: {self.score}\nSuggestions: {', '.join(self.suggestions)}"

def parse_json_response(response, default_message="无法解析评估结果。"):
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
    
    return {
        "analysis": default_message,
        "status": "NOT_PASS",
        "score": 0,
        "suggestions": ["请检查模型并重新评估。"]
    }

class BaseEvaluator(ABC):
    @abstractmethod
    def get_prompt(self, context: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        pass

    def evaluate(self, screenshots: List[str], context: Dict[str, Any]) -> EvaluationResult:
        prompt = self.get_prompt(context)
        response = self.analyze_screenshots(prompt, screenshots)
        result = parse_json_response(response)
        return EvaluationResult(
            result['analysis'],
            EvaluationStatus[result['status']],
            result['score'],
            result['suggestions']
        )

class GPTOverallEvaluator(BaseEvaluator):
    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Context:
        你是一个专门用于评估3D模型整体质量的AI助手。你需要分析提供的多角度截图，评估模型的整体结构和设计。

        用户原始输入: {context['user_input']}
        改写后的输入: {context['rewritten_input']}
        模型描述: {json.dumps(context['model_description'], ensure_ascii=False, indent=2)}

        Objective:
        评估3D模型的整体质量，包括完整性、合理性和预期符合度，并提供详细的评估结果和改进建议。
        一种常见的问题是，模型浮空，例如桌腿和桌面直接没有直接的连接，这种情况不符合要求
        另一种常见的问题则是，生成的模型为平面而非3D立体的，该问题常出现在板材上。

        Style:
        - 分析性：仔细观察模型的各个方面
        - 客观性：基于事实进行评估，不带个人偏见
        - 建设性：提供有助于改进模型的具体建议

        Tone:
        - 专业：使用3D建模和设计相关的专业术语
        - 直接：清晰明了地指出问题和优点
        - 鼓励性：在指出问题的同时，也要肯定模型的优点

        Audience:
        3D模型设计师和开发人员

        Response:
        请提供一个JSON对象，包含以下元素：
        1. analysis: 对模型整体质量的详细分析，包括优点和缺点
        2. status: 评估状态（"NOT_PASS", "PASS", 或 "GOOD"）
        3. score: 整体评分（0-10的浮点数，仅供参考，以5为分界线，5以下都属于不通过，7以上为Good）
        4. suggestions: 改进建议列表

        Example:
        {{
            "analysis": "该3D模型整体结构完整，主要组成部分都已包含。模型的整体形状符合预期，展现了良好的设计意图。然而，某些部分之间的连接看起来不够自然，特别是在[具体位置]处。此外，[某个部分]的细节处理略显粗糙，影响了整体的精致度。",
            "status": "PASS",
            "score": 7.5,
            "suggestions": [
                "改善[具体位置]的部件连接，使其更加自然流畅",
                "增加[某个部分]的细节，提高整体精致度",
                "考虑调整[某个特定特征]的比例，以增强整体平衡感"
            ]
        }}

        评估要点：
        1. 模型的主要组成部分是否完整？
        2. 各部分之间的连接是否合理？
        3. 模型的整体形状是否符合预期？
        4. 是否有明显的结构问题或不自然的部分？
        5. 模型是否符合用户的原始输入和改写后的要求？
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        # return analyze_screenshots_with_gpt4(prompt, screenshots)
        return analyze_screenshots_with_claude(prompt, screenshots)
    
class ClaudeOverallEvaluator(BaseEvaluator):
    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Context:
        你是一个专门用于评估3D模型整体质量的AI助手。你需要分析提供的多角度截图，评估模型的整体结构和设计。

        用户原始输入: {context['user_input']}
        改写后的输入: {context['rewritten_input']}
        模型描述: {json.dumps(context['model_description'], ensure_ascii=False, indent=2)}

        Objective:
        使用Claude的独特视角评估3D模型的整体质量，包括完整性、合理性和预期符合度，并提供详细的评估结果和改进建议。
        一种常见的问题是，模型浮空，例如桌腿和桌面直接没有直接的连接，这种情况不符合要求
        另一种常见的问题则是，生成的模型没有任何厚度，该问题常出现在板材上，例如桌板，椅板等，这种模型可以通过对比两张图轻易发现，且严重不符合要求。

        Style:
        - 全面性：考虑模型的各个方面
        - 创新性：提供独特的见解和建议
        - 细致性：注意细节，不放过任何潜在的改进点

        Tone:
        - 友好：以鼓励的态度提供反馈
        - 建设性：即使是批评也要以积极的方式表达
        - 专业：使用准确的术语描述模型特征

        Audience:
        3D模型设计师和开发人员

        Response:
        请提供一个JSON对象，包含以下元素：
        1. analysis: 对模型整体质量的详细分析，包括优点和缺点
        2. status: 评估状态（"NOT_PASS", "PASS", 或 "GOOD"）
        3. score: 整体评分（0-10的浮点数，仅供参考，以5为分界线，5以下都属于不通过，7以上为Good）
        4. suggestions: 改进建议列表

        Example:
        {{
            "analysis": "这个3D模型展现了独特的创意和良好的整体结构。模型的主要组成部分完整，整体形状符合设计意图。特别值得称赞的是[某个特定特征]的创新设计。然而，在[某个区域]的细节处理上还有提升空间。此外，[某些部分]之间的过渡可以更加流畅自然。",
            "status": "PASS",
            "score": 8.0,
            "suggestions": [
                "优化[某个区域]的细节，增加更多精细的纹理或结构",
                "改善[某些部分]之间的过渡，使整体更加协调",
                "考虑在[某个位置]添加一些细微的装饰元素，以增强整体美感"
            ]
        }}

        评估要点：
        1. 模型的主要组成部分是否完整？
        2. 各部分之间的连接是否合理？
        3. 模型的整体形状是否符合预期？
        4. 是否有明显的结构问题或不自然的部分？
        5. 模型是否符合用户的原始输入和改写后的要求？
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        return analyze_screenshots_with_claude(prompt, screenshots)

class SizeEvaluator(BaseEvaluator):
    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Context:
        你是一个专门评估3D模型尺寸的AI助手。你需要分析提供的多角度截图，评估模型各部分的大小是否合适。

        用户原始输入: {context['user_input']}
        改写后的输入: {context['rewritten_input']}
        模型描述: {json.dumps(context['model_description'], ensure_ascii=False, indent=2)}

        Objective:
        评估3D模型的尺寸是否合理，包括整体大小和各部分的相对尺寸，并提供详细的评估结果和改进建议。

        Style:
        - 精确性：关注具体的尺寸问题
        - 比较性：将模型尺寸与预期或标准尺寸进行对比
        - 实用性：提供可直接应用的尺寸调整建议

        Tone:
        - 技术性：使用精确的度量术语
        - 客观：基于事实和标准进行评判
        - 直接：清晰地指出尺寸问题

        Audience:
        3D模型设计师和开发人员

        Response:
        请提供一个JSON对象，包含以下元素：
        1. analysis: 对模型尺寸的详细分析，包括优点和问题
        2. status: 评估状态（"NOT_PASS", "PASS", 或 "GOOD"）
        3. score: 尺寸评分（0-10的浮点数，仅供参考，以5为分界线，5以下都属于不通过，7以上为Good）
        4. suggestions: 尺寸调整建议列表

        Example:
        {{
            "analysis": "该3D模型的整体尺寸基本合理，符合预期用途。[某个主要部分]的大小恰当，为整体结构提供了良好的基础。然而，[某个次要部分]的尺寸略显过大，可能影响整体的协调性。此外，[某个细节部分]的尺寸过小，可能导致在实际使用中不够明显或功能受限。",
            "status": "PASS",
            "score": 7.0,
            "suggestions": [
                "将[某个次要部分]的尺寸缩小约10-15%，以更好地与整体比例协调",
                "增大[某个细节部分]的尺寸约20%，以增强其可见度和功能性",
                "考虑调整[某个特定特征]的尺寸，使其与相邻部分更加协调"
            ]
        }}

        评估要点：
        1. 模型的整体尺寸是否合理？
        2. 各部分的绝对尺寸是否符合预期？
        3. 是否有任何部分的尺寸明显不合适？
        4. 尺寸是否影响了模型的功能或美观？
        5. 模型尺寸是否符合用户的原始输入和改写后的要求？
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        return analyze_screenshots_with_claude(prompt, screenshots)

class ProportionEvaluator(BaseEvaluator):
    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Context:
        你是一个专门评估3D模型比例的AI助手。你需要分析提供的多角度截图，评估模型各部分之间的比例关系。

        用户原始输入: {context['user_input']}
        改写后的输入: {context['rewritten_input']}
        模型描述: {json.dumps(context['model_description'], ensure_ascii=False, indent=2)}

        Objective:
        评估3D模型的比例是否协调，包括各部分之间的大小关系，并提供详细的评估结果和改进建议。

        Style:
        - 审美性：考虑比例对整体美感的影响
        - 功能性：评估比例是否影响模型的预期功能
        - 精确性：提供具体的比例调整建议

        Tone:
        - 专业：使用设计和比例相关的专业术语
        - 建设性：提供有助于改善比例的具体建议
        - 平衡：在指出问题的同时也要肯定良好的比例设计

        Audience:
        3D模型设计师和开发人员

        Response:
        请提供一个JSON对象，包含以下元素：
        1. analysis: 对模型比例的详细分析，包括优点和问题
        2. status: 评估状态（"NOT_PASS", "PASS", 或 "GOOD"）
        3. score: 比例评分（0-10的浮点数，仅供参考，以5为分界线，5以下都属于不通过，7以上为Good）
        4. suggestions: 比例调整建议列表

        Example:
        {{
            "analysis": "该3D模型的整体比例展现了良好的平衡感。主体部分与支撑结构的比例恰当，创造出稳定而优雅的外观。[某个特定部分]的比例特别出色，增添了模型的视觉吸引力。然而，[某个次要部分]与周围元素的比例略显不协调，稍微影响了整体的和谐性。此外，[某个功能性部件]的比例可能略显不足，可能会影响其实际功能。",
            "status": "PASS",
            "score": 8.5,
            "suggestions": [
                "调整[某个次要部分]的大小，使其与周围元素的比例更加协调，建议缩小约5-10%",
                "增大[某个功能性部件]的比例约15%，以确保其功能性不受影响",
                "考虑微调[某些细节元素]的比例，以进一步增强整体的视觉平衡"
            ]
        }}

        评估要点：
        1. 模型各部分的大小关系是否合适？
        2. 是否有任何部分看起来不成比例？
        3. 比例是否符合模型的预期用途？
        4. 与真实物体相比，有哪些比例需要调整？
        5. 模型比例是否符合用户的原始输入和改写后的要求？
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        return analyze_screenshots_with_claude(prompt, screenshots)

class StructureEvaluator(BaseEvaluator):
    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Context:
        你是一个专门评估3D模型结构的AI助手。你需要分析提供的多角度截图，评估模型的整体结构和细节处理。

        用户原始输入: {context['user_input']}
        改写后的输入: {context['rewritten_input']}
        模型描述: {json.dumps(context['model_description'], ensure_ascii=False, indent=2)}

        Objective:
        评估3D模型的结构是否合理，包括整体布局、连接方式和细节处理，并提供详细的评估结果和改进建议。
        一种常见的问题是，生成的模型为平面而非3D立体的，该问题常出现在板材上。

        Style:
        - 系统性：全面考虑模型的各个结构部分
        - 技术性：关注结构的工程学特性
        - 细致性：注意结构细节和潜在的问题点

        Tone:
        - 严谨：使用准确的工程和设计术语
        - 分析性：提供深入的结构分析
        - 建设性：给出具体可行的结构改进建议

        Audience:
        3D模型设计师和工程师

        Response:
        请提供一个JSON对象，包含以下元素：
        1. analysis: 对模型结构的详细分析，包括优点和问题
        2. status: 评估状态（"NOT_PASS", "PASS", 或 "GOOD"）
        3. score: 结构评分（0-10的浮点数，仅供参考，以5为分界线，5以下都属于不通过，7以上为Good）
        4. suggestions: 结构改进建议列表

        Example:
        {{
            "analysis": "该3D模型的整体结构设计合理，展现了良好的工程学考量。主要支撑结构稳固，能够有效承载整体重量。[某个关键连接点]的设计特别出色，既保证了强度又不影响美观。然而，在[某个应力集中区域]可能存在潜在的结构弱点。此外，[某些细节部分]的连接方式可以进一步优化，以增强整体的结构完整性。",
            "status": "PASS",
            "score": 7.8,
            "suggestions": [
                "加强[某个应力集中区域]的结构，可以考虑增加支撑或改变材料",
                "优化[某些细节部分]的连接方式，建议使用更强固的接合技术",
                "考虑在[某个位置]添加额外的支撑结构，以提高整体稳定性",
                "重新设计[某个特定部件]的内部结构，以减轻重量同时保持强度"
            ]
        }}

        评估要点：
        1. 模型的整体结构是否合理？
        2. 各部分之间的连接是否稳固和合适？
        3. 结构设计是否符合模型的预期用途？
        4. 是否存在潜在的结构弱点或不稳定因素？
        5. 模型结构是否符合用户的原始输入和改写后的要求？
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        return analyze_screenshots_with_claude(prompt, screenshots)

class ModelEvaluator:
    def __init__(self):
        self.evaluators: List[BaseEvaluator] = [
            GPTOverallEvaluator(),
            ClaudeOverallEvaluator(),
            SizeEvaluator(),
            ProportionEvaluator(),
            StructureEvaluator(),
        ]

    def evaluate(self, screenshots: List[str], context: Dict[str, Any]) -> Dict[str, EvaluationResult]:
        results = {}
        for evaluator in self.evaluators:
            result = evaluator.evaluate(screenshots, context)
            results[evaluator.__class__.__name__] = result
            
            # 使用 logger 记录每个评估器的结果
            logger.info(f"\n--- {evaluator.__class__.__name__} Results ---")
            logger.info(f"Analysis: {result.analysis}")
            logger.info(f"Status: {result.status.name}")
            logger.info(f"Score: {result.score}")
            logger.info("Suggestions:")
            for suggestion in result.suggestions:
                logger.info(f"- {suggestion}")
            logger.info("-----------------------------------")

        return results

    def aggregate_results(self, results: Dict[str, EvaluationResult]) -> Tuple[str, EvaluationStatus, float, List[str]]:
        statuses = [result.status for result in results.values()]
        average_score = sum(result.score for result in results.values()) / len(results)
        
        all_suggestions = []
        all_analyses = []
        for result in results.values():
            all_suggestions.extend(result.suggestions)
            all_analyses.append(result.analysis)
        
        unique_suggestions = list(set(all_suggestions))
        combined_analysis = " ".join(all_analyses)
        
        if EvaluationStatus.NOT_PASS in statuses:
            final_status = EvaluationStatus.NOT_PASS
        elif all(status == EvaluationStatus.GOOD for status in statuses):
            final_status = EvaluationStatus.GOOD
        else:
            final_status = EvaluationStatus.PASS
        
        return combined_analysis, final_status, average_score, unique_suggestions

    def is_model_satisfactory(self, results: Dict[str, EvaluationResult]) -> bool:
        _, final_status, _, _ = self.aggregate_results(results)
        return final_status in [EvaluationStatus.PASS, EvaluationStatus.GOOD]

# 以下是用于Blender界面的操作符和面板类，可以根据需要保留或删除

class OBJECT_OT_evaluate_model(Operator):
    bl_idname = "object.evaluate_model"
    bl_label = "Evaluate Model"
    bl_description = "Evaluate the current 3D model"

    def execute(self, context):
        screenshots = get_screenshots()
        evaluator = ModelEvaluator()
        
        # 这里需要提供评估所需的上下文信息
        evaluation_context = {
            "user_input": "用户的原始输入",  # 这里需要从某处获取用户输入
            "rewritten_input": "重写后的输入",  # 这里需要从某处获取重写后的输入
            "model_description": {}  # 这里需要从某处获取模型描述
        }
        
        results = evaluator.evaluate(screenshots, evaluation_context)
        
        combined_analysis, final_status, average_score, suggestions = evaluator.aggregate_results(results)

        print(f"Combined Analysis: {combined_analysis}")
        print(f"Final Status: {final_status.name}")
        print(f"Average Score: {average_score:.2f}")
        print("Suggestions:")
        for suggestion in suggestions:
            print(f"- {suggestion}")

        self.report({'INFO'}, f"Evaluation complete. Status: {final_status.name}, Score: {average_score:.2f}")

        return {'FINISHED'}

class Evaluator_PT_panel(Panel):
    bl_label = "Model Evaluator"
    bl_idname = "EVALUATOR_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.evaluate_model")