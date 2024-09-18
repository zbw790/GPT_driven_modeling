# evaluators_module.py

"""
This module provides functionality for evaluating 3D models in Blender using various criteria.
It includes evaluators for overall quality, size, proportion, structure, and usability.
The module integrates with GPT and Claude AI models for analysis.
"""

import bpy
from bpy.types import Operator, Panel
from bpy.props import StringProperty
from abc import ABC, abstractmethod
from llm_driven_modelling.llm.gpt_module import analyze_screenshots_with_gpt4
from llm_driven_modelling.llm.claude_module import analyze_screenshots_with_claude
from llm_driven_modelling.llm.LLM_common_utils import (
    get_screenshots,
    get_scene_info,
    format_scene_info,
)
from llm_driven_modelling.utils.logger_module import setup_logger, log_context
from typing import List, Dict, Any, Tuple
from enum import Enum
import json
import re
import os

# Set up logging
logger = setup_logger("model_generation")


class EvaluationStatus(Enum):
    """Enumeration for evaluation status."""

    NOT_PASS = 0
    PASS = 1
    GOOD = 2


class EvaluationResult:
    """Class to store evaluation results."""

    def __init__(
        self,
        analysis: str,
        status: EvaluationStatus,
        score: float,
        suggestions: List[str],
    ):
        self.analysis = analysis
        self.status = status
        self.score = score
        self.suggestions = suggestions

    def __str__(self):
        return f"Analysis: {self.analysis}\nStatus: {self.status.name}, Score: {self.score}\nSuggestions: {', '.join(self.suggestions)}"


def parse_json_response(
    response: str, default_message: str = "Unable to parse evaluation results."
) -> Dict[str, Any]:
    """
    Parse JSON response from AI models.

    Args:
        response (str): The response string to parse.
        default_message (str): Default message if parsing fails.

    Returns:
        Dict[str, Any]: Parsed JSON data or default dictionary.
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

    return {
        "analysis": default_message,
        "status": "PASS",
        "score": 0,
        "suggestions": ["Analysis failed. Please check the model and re-evaluate."],
    }


class BaseEvaluator(ABC):
    """Abstract base class for evaluators."""

    @abstractmethod
    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for AI model."""
        pass

    @abstractmethod
    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        """Analyze screenshots using AI model."""
        pass

    def evaluate(
        self, screenshots: List[str], context: Dict[str, Any]
    ) -> EvaluationResult:
        """
        Evaluate the model based on screenshots and context.

        Args:
            screenshots (List[str]): List of screenshot file paths.
            context (Dict[str, Any]): Evaluation context.

        Returns:
            EvaluationResult: The evaluation result.
        """
        prompt = self.get_prompt(context)
        response = self.analyze_screenshots(prompt, screenshots)
        result = parse_json_response(response)
        return EvaluationResult(
            result["analysis"],
            EvaluationStatus[result["status"]],
            result["score"],
            result["suggestions"],
        )


class GPTOverallEvaluator(BaseEvaluator):
    """Evaluator using GPT for overall model assessment."""

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for GPT overall evaluation."""
        return f"""
        Context:
        You are an AI assistant specialized in evaluating the overall quality of 3D models. Analyze the provided multi-angle screenshots and scene information to assess the model's overall structure and design.

        Model description: {json.dumps(context['obj'], ensure_ascii=False, indent=2)}
        Scene information: {context['scene_info']}

        Objective:
        Evaluate the overall quality of the 3D model, including completeness, reasonableness, and conformity to expectations. Provide detailed evaluation results and improvement suggestions.
        The following situations should be directly judged as not passing:
        - Any point that does not meet user requirements, except for material-related requirements.
        - A common problem is model floating, such as table legs not directly connected to the tabletop. This situation does not meet the requirements and should be judged as not passing.
        - Another common problem is that the generated model has no thickness, which often occurs in board materials. This situation is completely unacceptable and must be supplemented with corresponding thickness.

        Style:
        - Analytical: Carefully observe various aspects of the model
        - Objective: Evaluate based on facts, without personal bias
        - Constructive: Provide specific suggestions to improve the model

        Tone:
        - Professional: Use professional terms related to 3D modeling and design
        - Direct: Clearly point out problems and advantages
        - Encouraging: While pointing out problems, also affirm the model's strengths

        Audience:
        3D model designers and developers

        Response:
        Please provide a JSON object containing the following elements:
        1. analysis: Detailed analysis of the model's overall quality, including strengths and weaknesses
        2. status: Evaluation status ("NOT_PASS", "PASS", or "GOOD")
        3. score: Overall score (float from 0-10, for reference only, with 5 as the boundary, below 5 is not passing, above 7 is Good)
        4. suggestions: List of improvement suggestions

        Example:
        {{
            "analysis": "This 3D model has a complete overall structure, with all main components included. The overall shape of the model meets expectations, demonstrating good design intent. However, the connections between some parts look unnatural, especially at [specific location]. Additionally, the detail handling of [certain part] is slightly rough, affecting the overall refinement.",
            "status": "PASS",
            "score": 7.5,
            "suggestions": [
                "Improve the component connections at [specific location] to make them more natural and smooth",
                "Increase the details of [certain part] to enhance overall refinement",
                "Consider adjusting the proportions of [specific feature] to enhance overall balance"
            ]
        }}

        Evaluation points:
        1. Are the main components of the model complete?
        2. Are the connections between parts reasonable?
        3. Does the overall shape of the model meet expectations?
        4. Are there any obvious structural problems or unnatural parts?
        5. Does the model conform to the user's original input and rewritten requirements?
        6. According to the scene information, are the model's size, position, and proportions appropriate?
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        """Analyze screenshots using GPT-4."""
        return analyze_screenshots_with_gpt4(prompt, screenshots)


class ClaudeOverallEvaluator(BaseEvaluator):
    """Evaluator using Claude for overall model assessment."""

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for Claude overall evaluation."""
        return f"""
        Context:
        You are an AI assistant specialized in evaluating the overall quality of 3D models. Analyze the provided multi-angle screenshots and scene information to assess the model's overall structure and design.

        Model description: {json.dumps(context['obj'], ensure_ascii=False, indent=2)}
        Scene information: {context['scene_info']}

        Objective:
        Use Claude's unique perspective to evaluate the overall quality of the 3D model, including completeness, reasonableness, and conformity to expectations. Provide detailed evaluation results and improvement suggestions.
        Any point that does not meet user requirements, except for material-related requirements.
        A common problem is model floating, such as table legs not directly connected to the tabletop. This situation does not meet the requirements.
        Another common problem is that the generated model has no thickness, which often occurs in board materials. This situation is completely unacceptable and must be supplemented with corresponding thickness.

        Style:
        - Comprehensive: Consider various aspects of the model
        - Innovative: Provide unique insights and suggestions
        - Meticulous: Pay attention to details, don't miss any potential improvement points

        Tone:
        - Friendly: Provide feedback with an encouraging attitude
        - Constructive: Express criticism in a positive way
        - Professional: Use accurate terminology to describe model features

        Audience:
        3D model designers and developers

        Response:
        Please provide a JSON object containing the following elements:
        1. analysis: Detailed analysis of the model's overall quality, including strengths and weaknesses
        2. status: Evaluation status ("NOT_PASS", "PASS", or "GOOD")
        3. score: Overall score (float from 0-10, for reference only, with 5 as the boundary, below 5 is not passing, above 7 is Good)
        4. suggestions: List of improvement suggestions

        Example:
        {{
            "analysis": "This 3D model demonstrates unique creativity and good overall structure. The main components of the model are complete, and the overall shape conforms to the design intent. Particularly praiseworthy is the innovative design of [specific feature]. However, there is room for improvement in the detail handling of [certain area]. Additionally, the transitions between [some parts] could be more smooth and natural.",
            "status": "PASS",
            "score": 8.0,
            "suggestions": [
                "Optimize the details in [certain area], adding more refined textures or structures",
                "Improve the transitions between [some parts] to make the overall more harmonious",
                "Consider adding some subtle decorative elements at [certain location] to enhance overall aesthetics"
            ]
        }}

        Evaluation points:
        1. Are the main components of the model complete?
        2. Are the connections between parts reasonable?
        3. Does the overall shape of the model meet expectations?
        4. Are there any obvious structural problems or unnatural parts?
        5. Does the model conform to the user's original input and rewritten requirements?
        6. According to the scene information, are the model's size, position, and proportions appropriate?
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        """Analyze screenshots using Claude."""
        return analyze_screenshots_with_claude(prompt, screenshots)


class SizeEvaluator(BaseEvaluator):
    """Evaluator for assessing model size."""

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for size evaluation."""
        return f"""
        Context:
        You are an AI assistant specialized in evaluating the size of 3D models. Analyze the provided multi-angle screenshots and scene information to assess whether the size of various parts of the model is appropriate.

        Model description: {json.dumps(context['obj'], ensure_ascii=False, indent=2)}
        Scene information: {context['scene_info']}

        Objective:
        Evaluate whether the size of the 3D model is reasonable, including overall size and relative sizes of various parts, and provide detailed evaluation results and improvement suggestions.

        Style:
        - Precise: Focus on specific size issues
        - Comparative: Compare model sizes with expected or standard sizes
        - Practical: Provide directly applicable size adjustment suggestions

        Tone:
        - Technical: Use precise measurement terms
        - Objective: Judge based on facts and standards
        - Direct: Clearly point out size issues

        Audience:
        3D model designers and developers

        Response:
        Please provide a JSON object containing the following elements:
        1. analysis: Detailed analysis of the model's size, including strengths and issues
        2. status: Evaluation status ("NOT_PASS", "PASS", or "GOOD")
        3. score: Size score (float from 0-10, for reference only, with 5 as the boundary, below 5 is not passing, above 7 is Good)
        4. suggestions: List of size adjustment suggestions

        Example:
        {{
            "analysis": "The overall size of this 3D model is generally reasonable and meets the expected purpose. The size of [a major part] is appropriate, providing a good foundation for the overall structure. However, the size of [a minor part] appears slightly too large, which may affect the overall harmony. Additionally, the size of [a detail part] is too small, which may lead to it being not obvious enough or functionally limited in actual use.",
            "status": "PASS",
            "score": 7.0,
            "suggestions": [
                "Reduce the size of [minor part] by about 10-15% to better coordinate with the overall proportions",
                "Increase the size of [detail part] by about 20% to enhance its visibility and functionality",
                "Consider adjusting the size of [specific feature] to make it more coordinated with adjacent parts"
            ]
        }}

        Evaluation points:
        1. Is the overall size of the model reasonable?
        2. Do the absolute sizes of various parts meet expectations?
        3. Are there any parts with obviously inappropriate sizes?
        4. Do the sizes affect the model's functionality or aesthetics?
        5. Do the model sizes conform to the user's original input and rewritten requirements?
        6. According to the scene information, are the model's sizes coordinated with other objects?
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        """Analyze screenshots for size evaluation."""
        return analyze_screenshots_with_claude(prompt, screenshots)


class ProportionEvaluator(BaseEvaluator):
    """Evaluator for assessing model proportions."""

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for proportion evaluation."""
        return f"""
        Context:
        You are an AI assistant specialized in evaluating the proportions of 3D models. Analyze the provided multi-angle screenshots and scene information to assess the proportional relationships between various parts of the model.

        Model description: {json.dumps(context['obj'], ensure_ascii=False, indent=2)}
        Scene information: {context['scene_info']}

        Objective:
        Evaluate whether the proportions of the 3D model are harmonious, including the size relationships between various parts, and provide detailed evaluation results and improvement suggestions.

        Style:
        - Aesthetic: Consider the impact of proportions on overall aesthetics
        - Functional: Assess whether proportions affect the model's expected functionality
        - Precise: Provide specific proportion adjustment suggestions

        Tone:
        - Professional: Use professional terms related to design and proportions
        - Constructive: Provide specific suggestions to improve proportions
        - Balanced: Acknowledge good proportion designs while pointing out issues

        Audience:
        3D model designers and developers

        Response:
        Please provide a JSON object containing the following elements:
        1. analysis: Detailed analysis of the model's proportions, including strengths and issues
        2. status: Evaluation status ("NOT_PASS", "PASS", or "GOOD")
        3. score: Proportion score (float from 0-10, for reference only, with 5 as the boundary, below 5 is not passing, above 7 is Good)
        4. suggestions: List of proportion adjustment suggestions

        Example:
        {{
            "analysis": "This 3D model demonstrates a good sense of balance in its overall proportions. The proportions between the main body and supporting structures are appropriate, creating a stable and elegant appearance. The proportions of [specific part] are particularly excellent, adding to the model's visual appeal. However, the proportions of [minor part] appear slightly out of harmony with surrounding elements, slightly affecting the overall harmony. Additionally, the proportions of [functional component] may be slightly insufficient, potentially affecting its actual functionality.",
            "status": "PASS",
            "score": 8.5,
            "suggestions": [
                "Adjust the size of [minor part] to make its proportions more harmonious with surrounding elements, suggest reducing by about 5-10%",
                "Increase the proportions of [functional component] by about 15% to ensure its functionality is not affected",
                "Consider fine-tuning the proportions of [some detail elements] to further enhance overall visual balance"
            ]
        }}

        Evaluation points:
        1. Are the size relationships between various parts of the model appropriate?
        2. Are there any parts that look disproportionate?
        3. Do the proportions conform to the model's expected use?
        4. Compared to real objects, which proportions need adjustment?
        5. Do the model proportions conform to the user's original input and rewritten requirements?
        6. According to the scene information, are the model's proportions coordinated with other objects?
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        """Analyze screenshots for proportion evaluation."""
        return analyze_screenshots_with_claude(prompt, screenshots)


class StructureEvaluator(BaseEvaluator):
    """Evaluator for assessing model structure."""

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for structure evaluation."""
        return f"""
        Context:
        You are an AI assistant specialized in evaluating the structure of 3D models. Analyze the provided multi-angle screenshots and scene information to assess the model's overall structure and detail handling.

        Model description: {json.dumps(context['obj'], ensure_ascii=False, indent=2)}
        Scene information: {context['scene_info']}

        Objective:
        Evaluate whether the structure of the 3D model is reasonable, including overall layout, connection methods, and detail handling, and provide detailed evaluation results and improvement suggestions.
        A common problem is that the generated model is flat rather than 3D solid, which often occurs in board materials.
        Or there are obvious intersections, such as chair legs directly piercing through the chair cushion, which is clearly unacceptable.

        Style:
        - Systematic: Comprehensively consider various structural parts of the model
        - Technical: Focus on the engineering characteristics of the structure
        - Meticulous: Pay attention to structural details and potential problem points

        Tone:
        - Rigorous: Use accurate engineering and design terminology
        - Analytical: Provide in-depth structural analysis
        - Constructive: Give specific and feasible structural improvement suggestions

        Audience:
        3D model designers and engineers

        Response:
        Please provide a JSON object containing the following elements:
        1. analysis: Detailed analysis of the model's structure, including strengths and issues
        2. status: Evaluation status ("NOT_PASS", "PASS", or "GOOD")
        3. score: Structure score (float from 0-10, for reference only, with 5 as the boundary, below 5 is not passing, above 7 is Good)
        4. suggestions: List of structural improvement suggestions

        Example:
        {{
            "analysis": "The overall structural design of this 3D model is reasonable, demonstrating good engineering considerations. The main supporting structure is solid and can effectively bear the overall weight. The design of [key connection point] is particularly excellent, ensuring strength without affecting aesthetics. However, there may be potential structural weaknesses in [stress concentration area]. Additionally, the connection methods of [some detail parts] can be further optimized to enhance the overall structural integrity.",
            "status": "PASS",
            "score": 7.8,
            "suggestions": [
                "Strengthen the structure in [stress concentration area], consider adding support or changing materials",
                "Optimize the connection methods of [some detail parts], suggest using stronger joining techniques",
                "Consider adding additional supporting structures at [certain location] to improve overall stability",
                "Redesign the internal structure of [specific component] to reduce weight while maintaining strength"
            ]
        }}

        Evaluation points:
        1. Is the overall structure of the model reasonable?
        2. Are the connections between various parts stable and appropriate?
        3. Does the structural design conform to the model's expected use?
        4. Are there potential structural weaknesses or instability factors?
        5. Does the model structure conform to the user's original input and rewritten requirements?
        6. According to the scene information, is the model's structure coordinated with other objects?
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        """Analyze screenshots for structure evaluation."""
        return analyze_screenshots_with_claude(prompt, screenshots)


class UsabilityEvaluator(BaseEvaluator):
    """Evaluator for assessing model usability and functionality."""

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for usability evaluation."""
        return f"""
        Context:
        You are an AI assistant specialized in evaluating the practicality and functionality of 3D models. Analyze the provided multi-angle screenshots and scene information to judge whether the item is usable based on common sense.

        Model description: {json.dumps(context['obj'], ensure_ascii=False, indent=2)}
        Scene information: {context['scene_info']}

        Objective:
        Evaluate the practicality and functionality of the 3D model, judge whether it conforms to common sense and expected use, and provide detailed evaluation results and improvement suggestions.

        Style:
        - Practical: Focus on the actual use value of the model
        - Common sense: Make judgments based on daily life experience
        - Functional: Assess whether the model can meet its expected functions

        Tone:
        - Objective: Judge based on facts and common sense
        - Practical: Consider actual usage scenarios
        - Constructive: Provide suggestions that help improve practicality

        Audience:
        3D model designers, product developers, and end users

        Response:
        Please provide a JSON object containing the following elements:
        1. analysis: Detailed analysis of the model's practicality and functionality, including strengths and issues
        2. status: Evaluation status ("NOT_PASS", "PASS", or "GOOD")
        3. score: Usability score (float from 0-10, for reference only, with 5 as the boundary, below 5 is not passing, above 7 is Good)
        4. suggestions: List of suggestions to improve practicality and functionality

        Example:
        {{
            "analysis": "This 3D model demonstrates good practical design. As a table, its surface is sufficiently spacious to support daily use items. The table leg structure is solid, providing good support. However, the design of the table edges may be slightly sharp, potentially posing a safety hazard. Additionally, the table height seems slightly higher than standard, which may affect comfortable use for some users.",
            "status": "PASS",
            "score": 7.5,
            "suggestions": [
                "Consider designing the table edges to be more rounded to improve safety",
                "Adjust the table height to standard level (about 75 cm) to improve comfort",
                "Add anti-slip texture or material to the table surface to enhance practicality",
                "Consider adding simple storage functionality, such as drawers or hidden storage spaces"
            ]
        }}

        Evaluation points:
        1. Does the model's design conform to its intended use?
        2. Are there obvious safety hazards or usage obstacles?
        3. Are the model's dimensions and structure suitable for actual use?
        4. Compared to similar items, is this model competitive?
        5. Does the model conform to the user's original input and rewritten requirements?
        6. According to the scene information, is the model easy to use in the actual environment?
        """

    def analyze_screenshots(self, prompt: str, screenshots: List[str]) -> str:
        """Analyze screenshots for usability evaluation."""
        return analyze_screenshots_with_claude(prompt, screenshots)


class ModelEvaluator:
    """Class for evaluating 3D models using multiple evaluators."""

    def __init__(self):
        self.evaluators: List[BaseEvaluator] = [
            GPTOverallEvaluator(),
            ClaudeOverallEvaluator(),
            SizeEvaluator(),
            ProportionEvaluator(),
            StructureEvaluator(),
            UsabilityEvaluator(),
        ]

    def evaluate(
        self, screenshots: List[str], context: Dict[str, Any]
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate the model using all evaluators.

        Args:
            screenshots (List[str]): List of screenshot file paths.
            context (Dict[str, Any]): Evaluation context.

        Returns:
            Dict[str, EvaluationResult]: Evaluation results for each evaluator.
        """
        scene_info = get_scene_info()
        formatted_scene_info = format_scene_info(scene_info)
        context["scene_info"] = formatted_scene_info

        if "obj" in context and "model_description" not in context:
            context["model_description"] = context["obj"]

        results = {}
        for evaluator in self.evaluators:
            result = evaluator.evaluate(screenshots, context)
            results[evaluator.__class__.__name__] = result

            logger.info(f"\n--- {evaluator.__class__.__name__} Results ---")
            logger.info(f"Analysis: {result.analysis}")
            logger.info(f"Status: {result.status.name}")
            logger.info(f"Score: {result.score}")
            logger.info("Suggestions:")
            for suggestion in result.suggestions:
                logger.info(f"- {suggestion}")
            logger.info("-----------------------------------")

        return results

    def aggregate_results(
        self, results: Dict[str, EvaluationResult]
    ) -> Tuple[str, EvaluationStatus, float, List[str]]:
        """
        Aggregate results from all evaluators.

        Args:
            results (Dict[str, EvaluationResult]): Evaluation results from all evaluators.

        Returns:
            Tuple[str, EvaluationStatus, float, List[str]]: Aggregated analysis, status, score, and suggestions.
        """
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
        """
        Determine if the model is satisfactory based on evaluation results.

        Args:
            results (Dict[str, EvaluationResult]): Evaluation results from all evaluators.

        Returns:
            bool: True if the model is satisfactory, False otherwise.
        """
        _, final_status, _, _ = self.aggregate_results(results)
        return final_status in [EvaluationStatus.PASS, EvaluationStatus.GOOD]


class OBJECT_OT_evaluate_model(Operator):
    """Blender operator for evaluating the current 3D model."""

    bl_idname = "object.evaluate_model"
    bl_label = "Evaluate Model"
    bl_description = "Evaluate the current 3D model"

    def execute(self, context):
        screenshots = get_screenshots()
        evaluator = ModelEvaluator()

        evaluation_context = {
            "model_code": "Model code",  # This needs to be obtained from user input
            "obj": "obj",  # This needs to be obtained from rewritten input
            "scene_context": {},  # This needs to be obtained from model description
        }

        results = evaluator.evaluate(screenshots, evaluation_context)

        (
            combined_analysis,
            final_status,
            average_score,
            suggestions,
        ) = evaluator.aggregate_results(results)

        print(f"Combined Analysis: {combined_analysis}")
        print(f"Final Status: {final_status.name}")
        print(f"Average Score: {average_score:.2f}")
        print("Suggestions:")
        for suggestion in suggestions:
            print(f"- {suggestion}")

        self.report(
            {"INFO"},
            f"Evaluation complete. Status: {final_status.name}, Score: {average_score:.2f}",
        )

        return {"FINISHED"}


class Evaluator_PT_panel(Panel):
    """Blender panel for model evaluation."""

    bl_label = "Model Evaluator"
    bl_idname = "EVALUATOR_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.evaluate_model")
