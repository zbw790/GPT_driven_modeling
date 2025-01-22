# model_generation_utils.py

"""
This module provides utility functions for parsing user input and generating 3D scene descriptions.
It includes functions for sanitizing Claude AI responses, updating Blender views, and parsing scene inputs.
"""

import json
import re
import bpy
from llm_driven_modelling.utils.logger_module import setup_logger
from llm_driven_modelling.llm.claude_module import generate_text_with_claude
from llm_driven_modelling.llm.gpt_module import generate_text_with_context
from llm_driven_modelling.llm.LLM_common_utils import sanitize_command

logger = setup_logger("model_generation")


def sanitize_reference(response):
    """
    Extract JSON data from Claude's response, removing comments and non-JSON content.

    Args:
        response (str): The raw response from Claude AI.

    Returns:
        str: Sanitized JSON string or an empty string if no JSON is found.
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
    """
    Update the Blender view to ensure changes are immediately visible.

    Args:
        context: The current Blender context.
    """
    bpy.context.view_layer.update()
    logger.debug("Blender view updated.")


def parse_scene_input(user_input, rewritten_input):
    """
    Parse user input and rewritten input to generate a standardized scene description.

    Args:
        user_input (str): The original user input describing the scene.
        rewritten_input (str): The rewritten and processed input.

    Returns:
        dict: A dictionary containing the parsed scene description in JSON format.
    """
    prompt = f"""
      Context:
      You are an AI assistant specialized in parsing and restructuring user inputs for a 3D modeling system. Your task is to process user-provided scene descriptions, focusing on the visible and significant aspects of objects.

      Objective:
      Convert the user's original description and the rewritten prompt into a standardized JSON format, including each visible item in the scene, their relative positions, the overall context information of the scene, and the style for each object. Focus on components that significantly affect the object's external appearance.

      *Important: Organize the objects in the scene from least important to most important. This order will be used in the subsequent generation process.

      Input:
      Original user input: {user_input}
      Parsed prompt: {rewritten_input}

      Output format example:
      {{
        "scene_name": "Study Room Scene",
        "scene_context": "This is a quiet study room with soft lighting and a cozy atmosphere.",
        "objects": [
          {{
            "object_type": "plant",
            "importance": "low",
            "position": "corner of the room",
            "description": "A small potted plant for decoration",
            "style": "low_poly",
            "components": [
              {{
                "name": "pot",
                "quantity": 1,
                "shape": "cylinder",
                "dimensions": {{
                  "radius": 10,
                  "height": 15
                }}
              }},
              {{
                "name": "plant",
                "quantity": 1,
                "shape": "sphere",
                "dimensions": {{
                  "radius": 20
                }}
              }}
            ]
          }},
          {{
            "object_type": "chair",
            "importance": "medium",
            "position": "in front of the desk",
            "description": "A simple office chair",
            "style": "voxel",
            "components": [
              {{
                "name": "seat",
                "quantity": 1,
                "shape": "cuboid",
                "dimensions": {{
                  "length": 50,
                  "width": 50,
                  "height": 10
                }}
              }},
              {{
                "name": "backrest",
                "quantity": 1,
                "shape": "cuboid",
                "dimensions": {{
                  "length": 50,
                  "width": 5,
                  "height": 60
                }}
              }}
            ]
          }},
          {{
            "object_type": "desk",
            "importance": "high",
            "position": "center of the room",
            "description": "A large wooden desk with a smooth surface",
            "style": "low_poly",
            "components": [
              {{
                "name": "desktop",
                "quantity": 1,
                "shape": "cuboid",
                "dimensions": {{
                  "length": 120,
                  "width": 60,
                  "height": 5
                }}
              }},
              {{
                "name": "legs",
                "quantity": 4,
                "shape": "cylinder",
                "dimensions": {{
                  "radius": 3,
                  "height": 75
                }}
              }}
            ]
          }}
        ]
      }}

      Notes:
      1. Identify all visible items in the scene and create an object description for each.
      2. Include relative position information and a brief description for each item.
      3. For each item, list only its core visible components that significantly affect its appearance.
      4. Omit all details, internal structures, or components unless specifically mentioned in the input descriptions.
      5. If some information is missing, make reasonable inferences based on common sense, but lean towards simplicity.
      6. Ensure position descriptions are clear enough for subsequent correct placement of items.
      7. Add a scene_context field describing the overall atmosphere, lighting, etc. of the scene.
      8. Assign an importance level ("low", "medium", or "high") to each object and order them from least to most important.
      9. Do not add any large objects or environmental elements (such as ground, floor, walls, etc.) unless they are explicitly mentioned in the input descriptions.
      10. Assign a style to each object. Default to "low_poly".

      Guidelines for simplification:
      - Include only the most basic shape that represents the object's overall form.
      - Use simple geometric shapes (cubes, cylinders, spheres) to represent complex forms when possible.
      - Omit all decorative elements, textures, or patterns unless explicitly specified.
      - For furniture, include only the main body and essential structural elements (like legs for tables and chairs).
      - For appliances or electronics, represent them as simple boxes unless specific features are mentioned.
      - Natural objects (like plants) should be simplified to basic forms (e.g., a tree as a cylinder for trunk and sphere for foliage).

      Remember: The goal is to create the simplest possible representation that still allows the object to be recognizable and fulfill its role in the scene. Only add details if they are specifically mentioned in the input descriptions. Do not include any objects or environmental elements that are not explicitly mentioned in the input. Assign a style to each object based on the input or context, defaulting to "low_poly" if not specified.
      """

    logger.info(f"Sending prompt to Claude: {prompt}")
    response = generate_text_with_context(prompt)
    logger.info(f"Received response from Claude: {response}")

    response = sanitize_command(response)
    response = sanitize_reference(response)
    return json.loads(response)
