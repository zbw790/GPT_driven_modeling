# llama_index_material_library.py

import json
import openai
import bpy
import os
import logging
import shutil
import re
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.response_synthesizers import get_response_synthesizer
from dotenv import load_dotenv
from src.llm_modules.LLM_common_utils import (
    execute_blender_command,
    initialize_conversation,
    add_history_to_prompt,
    get_scene_info,
    format_scene_info,
)
from src.llm_modules.gpt_module import generate_text_with_context
from src.llm_modules.claude_module import generate_text_with_claude
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty, EnumProperty
from src.utils.model_viewer_module import save_screenshots, save_screenshots_to_path
from src.utils.logger_module import setup_logger, log_context


# 设置日志记录
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key


def preprocess_markdown(content):
    return re.split(r"\n##", content)[0]


def load_material_data(directory_path):
    documents = []
    material_library_path = os.path.join(directory_path, "material_library")
    structure_file_path = os.path.join(
        material_library_path, "material_library_structure.json"
    )

    with open(structure_file_path, "r", encoding="utf-8") as f:
        structure = json.load(f)

    for material in structure["materials"]:
        file_path = os.path.join(material_library_path, material["file"])
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                description = preprocess_markdown(content)
                doc = Document(
                    text=description,
                    metadata={
                        "material": material["name"],
                        "file_name": material["file"],
                        "file_path": os.path.abspath(file_path),
                    },
                )
                documents.append(doc)
            logger.info(f"Loaded material file: {file_path}")
        else:
            logger.warning(f"Material file not found - {file_path}")

    logger.info(f"Total material documents loaded: {len(documents)}")
    return documents, structure


def create_material_index(documents):
    db_path = "./database/chroma_db_materials"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        logger.info("Existing material database deleted.")

    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("material_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002", api_key=api_key)
    return VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, embed_model=embed_model
    )


def configure_material_query_engine(index):
    retriever = VectorIndexRetriever(index=index, similarity_top_k=3)
    response_synthesizer = get_response_synthesizer(
        response_mode="tree_summarize", use_async=True
    )
    return RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.65)],
    )


def query_material_documentation(query_engine, query):
    response = query_engine.query(query)
    results = []
    for node in response.source_nodes:
        file_path = node.node.metadata.get("file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                results.append(f.read())
    return results if results else ["No relevant material information found."]


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


class MaterialProperties(PropertyGroup):
    input_text: StringProperty(name="Material Query", default="")
    model_choice: EnumProperty(
        name="Model",
        items=[
            ("GPT", "GPT-4", "Use GPT-4 model"),
            ("CLAUDE", "Claude-3.5", "Use Claude-3.5 model"),
        ],
        default="GPT",
    )


class MATERIAL_OT_query(Operator):
    bl_idname = "material.query"
    bl_label = "Query Material DB"

    def execute(self, context):
        props = context.scene.material_tool
        query = props.input_text
        results = query_material_documentation(
            context.scene.material_query_engine, query
        )
        for i, result in enumerate(results):
            print(f"Material Query Result {i+1}:", result)
            logger.info(f"Material Query Result {i+1} Length: {len(result)}")
        return {"FINISHED"}


class MATERIAL_OT_generate_material(Operator):
    bl_idname = "material.apply_materials"
    bl_label = "Apply Materials"
    bl_description = "Apply materials to the generated model"

    def execute(self, context):
        props = context.scene.model_generation_tool
        user_input = props.input_text

        with log_context(logger, user_input) as log_dir:
            try:
                # 获取场景信息
                scene_info = get_scene_info()
                formatted_scene_info = format_scene_info(scene_info)

                # 步骤1：分析场景信息并确定所需的材质
                material_requirements = self.analyze_scene_for_materials(
                    formatted_scene_info
                )

                # 步骤2：查询相关的材质文档
                material_docs = self.query_material_docs(material_requirements)

                # 步骤3：生成并应用材质
                self.generate_and_apply_materials(
                    context, material_requirements, material_docs, log_dir
                )

                self.report(
                    {"INFO"}, f"Materials applied successfully. Logs saved in {log_dir}"
                )
            except Exception as e:
                logger.error(f"An error occurred while applying materials: {str(e)}")
                self.report(
                    {"ERROR"}, f"An error occurred while applying materials: {str(e)}"
                )

        return {"FINISHED"}

    def analyze_scene_for_materials(self, scene_info):
        prompt = f"""
        Context:
        你是一个专门分析3D场景并确定所需材质的AI助手。根据提供的场景信息和模型描述，确定每个对象需要的材质类型。

        场景信息：
        {scene_info}

        Task:
        分析场景中的每个对象，并确定它们可能需要的材质类型。考虑对象的名称、形状和可能的用途。

        Output:
        请提供一个JSON对象，其中包含每个对象的名称作为键，以及建议的材质类型作为值,注意一些材质为blender场景自带的，例如摄像机Camera等，该类物品不需要添加材质：
        {{
            "Table_Top": "wood",
            "Table_Leg": "metal",
            "Chair_Seat": "fabric",
            "Lamp_Shade": "glass"
        }}

        只需提供JSON对象，不需要其他解释。
        """
        response = generate_text_with_claude(prompt)
        return json.loads(response)

    def query_material_docs(self, material_requirements):
        material_docs = {}
        unique_docs = set()  # 用于存储唯一的文档

        for obj_name, material_type in material_requirements.items():
            query = f"材质类型：{material_type}"
            results = query_material_documentation(
                bpy.types.Scene.material_query_engine, query
            )

            # 过滤并只添加唯一的文档
            unique_results = []
            for result in results:
                if result not in unique_docs:
                    unique_docs.add(result)
                    unique_results.append(result)

            material_docs[obj_name] = unique_results

        # 将所有唯一的文档合并为一个列表
        all_unique_docs = list(unique_docs)

        return all_unique_docs

    def generate_and_apply_materials(
        self, context, material_requirements, material_docs, log_dir
    ):
        logger.info(f"材质需求： {material_requirements}")
        logger.info(f"材质文档： {material_docs}")
        prompt = f"""
        Context:
        你是一个专门为3D模型生成材质的AI助手。根据提供的材质需求和相关文档，生成Blender Python代码来创建和应用材质。

        注意：
        1. 不要使用 "Subsurface", "Sheen", "Emission", "Transmission" 等作为直接输入参数。这些是复合参数，需要通过其他允许的参数来实现效果。
        2. 对于颜色和向量类型的输入，请始终使用列表格式，而不是单个浮点数。例如：
        - 对于颜色输入（如Base Color, Specular Tint等），使用4个值的列表：[R, G, B, A]
        - 对于向量输入（如Normal），使用3个值的列表：[X, Y, Z]
        - 对于单一数值输入，直接使用浮点数

        材质需求：
        {json.dumps(material_requirements, ensure_ascii=False, indent=2)}

        材质文档：
        {json.dumps(material_docs, ensure_ascii=False, indent=2)}

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
        material_code = generate_text_with_claude(prompt)

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
            self.report({"ERROR"}, f"Error applying materials: {str(e)}")

        # 更新视图
        self.update_blender_view(context)

        # 保存应用材质后的截图
        screenshots = save_screenshots()
        screenshot_dir = os.path.join(log_dir, "material_screenshots")
        save_screenshots_to_path(screenshot_dir)
        for screenshot in screenshots:
            logger.debug(f"Material application screenshot saved: {screenshot}")

    def update_blender_view(self, context):
        # 确保更改立即可见
        bpy.context.view_layer.update()
        logger.debug("Blender view updated.")


class MATERIAL_PT_panel(Panel):
    bl_label = "Llama Index Material Library"
    bl_idname = "MATERIAL_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        props = context.scene.material_tool

        layout.prop(props, "input_text")
        layout.prop(props, "model_choice")
        layout.operator("material.query")
        layout.operator("material.apply_materials")


def initialize_material_db():
    db_path = "./database/chroma_db_materials"
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("material_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    bpy.types.Scene.material_query_engine = configure_material_query_engine(index)
    logger.info("Material DB initialized successfully.")
