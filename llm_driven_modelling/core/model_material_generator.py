# model_material_generator

import bpy
import json
import os
from llm_driven_modelling.llm.claude_module import (
    generate_text_with_claude,
    analyze_screenshots_with_claude,
)
from llm_driven_modelling.llm.LLM_common_utils import (
    execute_blender_command,
    get_scene_info,
    format_scene_info,
)
from llm_driven_modelling.utils.logger_module import setup_logger
from llm_driven_modelling.llm.gpt_module import (
    generate_text_with_context,
    analyze_screenshots_with_gpt4,
)
from llm_driven_modelling.utils.model_viewer_module import (
    save_screenshots,
    save_screenshots_to_path,
)
from llm_driven_modelling.llama_index_library.llama_index_material_library import (
    query_material_documentation,
)
from llm_driven_modelling.core.model_generation_utils import update_blender_view

# 创建专门的日志记录器
logger = setup_logger("model_generation")


def query_material_docs(material_requirements):
    material_docs = {}
    for material_type in material_requirements.keys():
        query = f"材质类型：{material_type}"
        results = query_material_documentation(
            bpy.types.Scene.material_query_engine, query
        )
        material_docs[material_type] = results
    return material_docs


def apply_materials(context, user_input, rewritten_input, scene_description, log_dir):
    try:
        # 获取场景信息
        scene_info = get_scene_info()
        formatted_scene_info = format_scene_info(scene_info)

        # 步骤1：分析场景信息并确定所需的材质
        material_requirements = analyze_scene_for_materials(
            user_input, rewritten_input, formatted_scene_info, scene_description
        )
        logger.info(f"材质需求： {material_requirements}")

        # 步骤2：查询相关的材质文档
        material_docs = query_material_docs(material_requirements)
        logger.info(f"材质文档： {material_docs}")

        # 步骤3：生成并应用材质
        generate_and_apply_materials(
            context,
            user_input,
            rewritten_input,
            formatted_scene_info,
            scene_description,
            material_requirements,
            material_docs,
            log_dir,
        )

    except Exception as e:
        logger.error(f"An error occurred while applying materials: {str(e)}")


def analyze_scene_for_materials(
    user_input, rewritten_input, formatted_scene_info, scene_description
):
    prompt = f"""
        Context:
        你是一个专门分析3D场景并确定所需材质的AI助手。根据提供的场景信息和模型描述，确定需要的材质类型。

        用户原始输入：{user_input}
        改写后的要求：{rewritten_input}
        场景信息：{formatted_scene_info}
        模型描述：{json.dumps(scene_description, ensure_ascii=False, indent=2)}

        Task:
        分析场景中的每个对象，并确定所需的材质类型。考虑对象的名称、形状和可能的用途。将相同材质类型的对象分组。

        Output:
        请提供一个JSON对象，其中包含材质类型作为键，以及需要该材质的对象列表作为值。注意一些材质为blender场景自带的，例如摄像机Camera等，该类物品不需要添加材质：
        {{
            "wood": ["Table_Top", "Chair_Seat"],
            "metal": ["Table_Leg", "Chair_Frame"],
            "fabric": ["Chair_Cushion"],
            "glass": ["Lamp_Shade"]
        }}

        只需提供JSON对象，不需要其他解释。
        """
    response = generate_text_with_context(prompt)
    return json.loads(response)


def generate_and_apply_materials(
    context,
    user_input,
    rewritten_input,
    formatted_scene_info,
    scene_description,
    material_requirements,
    material_docs,
    log_dir,
):
    logger.info(f"材质需求： {material_requirements}")
    logger.info(f"材质文档： {material_docs}")
    prompt = f"""
        Context:
        你是一个专门为3D模型生成材质的AI助手。根据提供的材质需求和相关文档，生成Blender Python代码来创建和应用材质。
        注意，你应该且只应该生成材质，不应该修改任何场上的模型。

        注意：
        1. 不要使用 "Subsurface", "Sheen", "Emission", "Transmission", "Specular"等作为直接输入参数。这些是复合参数，需要通过其他允许的参数来实现效果。
        2. 对于颜色和向量类型的输入，请始终使用列表格式，而不是单个浮点数。例如：
        - 对于颜色输入（如Base Color, Specular Tint等），使用4个值的列表：[R, G, B, A]
        - 对于向量输入（如Normal），使用3个值的列表：[X, Y, Z]
        - 对于单一数值输入，直接使用浮点数

        场景内的部件名称等信息：{formatted_scene_info}
        用户原始输入：{user_input}
        改写后的要求：{rewritten_input}
        模型描述：{json.dumps(scene_description, ensure_ascii=False, indent=2)}
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
    material_code = generate_text_with_context(prompt)

    # 保存生成的材质代码到文件
    with open(
        os.path.join(log_dir, "material_application_code.py"), "w", encoding="utf-8"
    ) as f:
        f.write(material_code)

    # 执行生成的Blender材质命令
    try:
        execute_blender_command(material_code)
        logger.debug("Successfully applied materials.")
    except Exception as e:
        logger.error(f"Error applying materials: {str(e)}")

    # 更新视图
    update_blender_view(context)

    # 保存应用材质后的截图
    screenshots = save_screenshots()
    screenshot_dir = os.path.join(log_dir, "material_screenshots")
    save_screenshots_to_path(screenshot_dir)
    for screenshot in screenshots:
        logger.debug(f"Material application screenshot saved: {screenshot}")
