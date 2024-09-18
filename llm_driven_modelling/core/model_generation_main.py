# model_generation_main.py

import bpy
import json
import os
from bpy.types import Operator, PropertyGroup, Panel
from bpy.props import StringProperty
from llm_driven_modelling.utils.logger_module import setup_logger, log_context
from llm_driven_modelling.core.prompt_rewriter import rewrite_prompt
from bpy.types import Operator
from llm_driven_modelling.core.model_generation_utils import parse_scene_input
from llm_driven_modelling.core.model_and_scene_generator import (
    generate_3d_model,
    arrange_scene,
)
from llm_driven_modelling.core.model_material_generator import apply_materials
from llm_driven_modelling.core.model_generation_optimizer import (
    evaluate_and_optimize_model,
)
from llm_driven_modelling.utils.logger_module import setup_logger

# 创建专门的日志记录器
logger = setup_logger("model_generation")


class ModelGenerationProperties(PropertyGroup):
    input_text: StringProperty(
        name="Model Description",
        description="Describe the model you want to generate",
        default="",
    )


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
                scene_description = parse_scene_input(user_input, rewritten_input)
                logger.info("Scene Description:")
                logger.info(json.dumps(scene_description, ensure_ascii=False, indent=2))

                # Save scene description to file
                with open(
                    os.path.join(log_dir, "scene_description.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
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
                        log_dir,
                    )
                    models.append(model)

                # Arrange objects in the scene
                arrange_scene(context, scene_description, models, log_dir)

                # Apply materials to the entire scene
                apply_materials(
                    context, user_input, rewritten_input, scene_description, log_dir
                )

                logger.debug(f"Log directory: {log_dir}")
                # Save screenshot of the current scene
                screenshot_path = os.path.join(log_dir, "scene_screenshot.png")
                bpy.ops.screen.screenshot(filepath=screenshot_path)
                logger.debug(f"Screenshot saved to {screenshot_path}")

                self.report(
                    {"INFO"}, f"Scene generated and optimized. Logs saved in {log_dir}"
                )
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                self.report({"ERROR"}, f"An error occurred: {str(e)}")

        return {"FINISHED"}

    def generate_and_optimize_model(
        self, context, obj, scene_context, user_input, rewritten_input, log_dir
    ):
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
        initial_model_code = generate_3d_model(context, obj, scene_context, log_dir)

        # Optimize the model
        optimized_model_code = evaluate_and_optimize_model(
            context,
            obj,
            scene_context,
            initial_model_code,
            user_input,
            rewritten_input,
            log_dir,
        )

        return {
            "object_type": obj["object_type"],
            "initial_model": initial_model_code,
            "optimized_model": optimized_model_code,
        }


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
