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
from llm_driven_modelling.llm.LLM_common_utils import sanitize_command

logger = setup_logger("model_generation_utils")


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
        You are an AI assistant specialized in parsing and restructuring user inputs. You work within a 3D modeling system. Your main task is to process user-provided scene descriptions, which may contain multiple items and their positional relationships.

        Objective:
        Convert the user's original description and the rewritten prompt into a standardized JSON format, including each item in the scene, their relative positions, and the overall context information of the scene.

        Input:
        Original user input: {user_input}
        Parsed prompt: {rewritten_input}

        Output format example:
        {{
          "scene_name": "Study Room Scene",
          "scene_context": "This is a quiet study room with soft lighting and a cozy atmosphere.",
          "objects": [
            {{
              "object_type": "desk",
              "position": "center of the room",
              "description": "A large wooden desk with a smooth surface",
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
                  "name": "leg",
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
              "object_type": "vase",
              "position": "top right corner of the desk",
              "description": "A blue and white ceramic vase with a few fresh flowers",
              "components": [
                {{
                  "name": "body",
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

        Notes:
        1. Identify all items in the scene and create an object description for each.
        2. Include relative position information and a brief description for each item.
        3. For each item, list its core components, similar to the previous single item description.
        4. If some information is missing, make reasonable inferences based on common sense.
        5. Ensure position descriptions are clear enough for subsequent correct placement of items.
        6. Add a scene_context field describing the overall atmosphere, lighting, etc. of the scene.
        """

    logger.info(f"Sending prompt to Claude: {prompt}")
    response = generate_text_with_claude(prompt)
    logger.info(f"Received response from Claude: {response}")

    response = sanitize_command(response)
    response = sanitize_reference(response)
    return json.loads(response)
