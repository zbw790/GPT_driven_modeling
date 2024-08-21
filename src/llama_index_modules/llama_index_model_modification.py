# llama_index_model_modification.py

import json
import openai
import bpy
import os
import logging
import requests
import time
import shutil
import re
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty, EnumProperty
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.embeddings.openai import OpenAIEmbedding
from dotenv import load_dotenv
from llama_index.core.response_synthesizers import get_response_synthesizer
from src.llm_modules.LLM_common_utils import execute_blender_command, initialize_conversation, add_history_to_prompt, get_scene_info, format_scene_info
from src.llm_modules.gpt_module import generate_text_with_context, analyze_screenshots_with_gpt4
from src.llm_modules.claude_module import generate_text_with_claude, analyze_screenshots_with_claude

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

def preprocess_markdown(content):
    # 提取描述部分（假设描述部分在文件的开头，到第一个 ## 标题之前）
    return re.split(r'\n##', content)[0]

def load_modification_data(directory_path):
    documents = []
    category_structure_path = os.path.join(directory_path, 'model_modification', 'modification_category_structure.json')
    
    # 加载类别结构
    with open(category_structure_path, 'r', encoding='utf-8') as f:
        category_structure = json.load(f)
    
    # 遍历类别结构并加载对应的 Markdown 文件
    for category in category_structure['categories']:
        for subcategory in category['subcategories']:
            for problem in subcategory['problems']:
                file_path = os.path.join(directory_path, 'model_modification', category['name'], subcategory['name'], problem['file'])
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 使用预处理函数提取描述部分
                        description = preprocess_markdown(content)
                        doc = Document(text=description, metadata={
                            "category": category['name'],
                            "subcategory": subcategory['name'],
                            "problem": problem['name'],
                            "file_name": problem['file'],
                            "file_path": os.path.abspath(file_path)
                        })
                        documents.append(doc)
                    logger.info(f"Loaded file: {file_path}")
                else:
                    logger.warning(f"File not found - {file_path}")
    
    logger.info(f"Total documents loaded: {len(documents)}")
    return documents, category_structure

# 创建向量存储索引
def create_modification_index(documents):
    db_path = "./database/chroma_db_modification"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        logger.info("Existing modification database deleted.")
    
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("modification_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002", api_key=api_key)
    return VectorStoreIndex.from_documents(documents, storage_context=storage_context, embed_model=embed_model)

# 配置查询引擎
def configure_modification_query_engine(index):
    retriever = VectorIndexRetriever(index=index, similarity_top_k=1)
    response_synthesizer = get_response_synthesizer(
        response_mode="tree_summarize",
        use_async=True
    )
    return RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.6)],
    )

# 查询函数
def query_modification_documentation(query_engine, query):
    response = query_engine.query(query)
    if response.source_nodes:
        # 获取最相关文档的文件路径
        file_path = response.source_nodes[0].node.metadata.get('file_path')
        if file_path and os.path.exists(file_path):
            # 直接读取并返回整个文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    return "No relevant modification information found."

class ModificationProperties(PropertyGroup):
    input_text: StringProperty(name="Modification Query", default="")
    model_choice: EnumProperty(
        name="Model",
        items=[
            ('GPT', "GPT-4", "Use GPT-4 model"),
            ('CLAUDE', "Claude-3.5", "Use Claude-3.5 model"),
        ],
        default='GPT'
    )

class MODIFICATION_OT_query(Operator):
    bl_idname = "modification.query"
    bl_label = "Query Modification DB"

    def execute(self, context):
        props = context.scene.modification_tool
        query = props.input_text
        result = query_modification_documentation(context.scene.modification_query_engine, query)
        print("Modification Query Result:", result)
        logger.info(f"Modification Query Result Length: {len(result)}")
        return {'FINISHED'}

class MODIFICATION_OT_query_with_screenshots(Operator):
    bl_idname = "modification.query_with_screenshots"
    bl_label = "Query Modification with Screenshots"

    def execute(self, context):
        try:
            props = context.scene.modification_tool
            model_choice = props.model_choice

            screenshots_path = r"D:\GPT_driven_modeling\resources\screenshots"
            screenshots = [os.path.join(screenshots_path, f) for f in os.listdir(screenshots_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]

            prompt = """
            请分析下列图片并观察有什么问题
            """

            if model_choice == 'GPT':
                description = analyze_screenshots_with_gpt4(prompt, screenshots)
            elif model_choice == 'CLAUDE':
                description = analyze_screenshots_with_claude(prompt, screenshots)
            else:
                raise ValueError("Invalid model choice")

            logger.info(f"{model_choice} Response: {description}")

            result = query_modification_documentation(context.scene.modification_query_engine, description)
            print("Query with Screenshots Result:", result)
            logger.info(f"Query with Screenshots Result Length: {len(result)}")

        except Exception as e:
            logger.error(f"Error in MODIFICATION_OT_query_with_screenshots.execute: {e}")
            print(f"Error: {str(e)}")

        return {'FINISHED'}

class MODIFICATION_OT_query_and_generate(Operator):
    bl_idname = "modification.query_and_generate"
    bl_label = "Query and Generate Modification Commands"

    def execute(self, context):
        try:
            props = context.scene.modification_tool
            model_choice = props.model_choice

            screenshots_path = r"D:\GPT_driven_modeling\resources\screenshots"
            screenshots = [os.path.join(screenshots_path, f) for f in os.listdir(screenshots_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]

            prompt = """
            请分析下列图片并观察有什么问题
            """

            if model_choice == 'GPT':
                description = analyze_screenshots_with_gpt4(prompt, screenshots)
            elif model_choice == 'CLAUDE':
                description = analyze_screenshots_with_claude(prompt, screenshots)
            else:
                raise ValueError("Invalid model choice")

            logger.info(f"{model_choice} Image Analysis: {description}")

            result = query_modification_documentation(context.scene.modification_query_engine, description)
            logger.info(f"Modification Query Result: {result}")
            logger.info(f"Modification Query Result Length: {len(result)}")

            scene_info = get_scene_info()
            formatted_scene_info = format_scene_info(scene_info)
            
            prompt = f"基于以下信息生成Blender命令：\n\nblender内的场景信息:{formatted_scene_info}\n\n图像分析：{description}\n\可以参考相关问题的解决文档{result}\n\n请生成适当的Blender Python命令来修复或改进模型，注意当前的运行函数允许导入新的库，所以请生成代码时也import相关的库。"
            
            conversation_manager = context.scene.conversation_manager
            initialize_conversation(context)
            prompt_with_history = add_history_to_prompt(context, prompt)

            if model_choice == 'GPT':
                response = generate_text_with_context(prompt_with_history)
            elif model_choice == 'CLAUDE':
                response = generate_text_with_claude(prompt_with_history)

            # 更新对话历史
            conversation_manager.add_message("user", prompt)
            conversation_manager.add_message("assistant", response)

            logger.info(f"{model_choice} Generated Commands: {response}")

            execute_blender_command(response)

        except Exception as e:
            logger.error(f"Error in MODIFICATION_OT_query_and_generate.execute: {e}")
            print(f"Error: {str(e)}")

        return {'FINISHED'}

class MODIFICATION_PT_panel(Panel):
    bl_label = "Llama Index Model Modification"
    bl_idname = "MODIFICATION_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        props = context.scene.modification_tool

        layout.prop(props, "input_text")
        layout.prop(props, "model_choice")
        layout.operator("modification.query")
        layout.operator("modification.query_with_screenshots")
        layout.operator("modification.query_and_generate")

def initialize_modification_db():
    db_path = "./database/chroma_db_modification"
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("modification_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    bpy.types.Scene.modification_query_engine = configure_modification_query_engine(index)
    logger.info("Modification DB initialized successfully.")