import json
import openai
import bpy
import os
import logging
import requests
import time
import shutil
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.embeddings.openai import OpenAIEmbedding
from dotenv import load_dotenv
from llama_index.core.response_synthesizers import get_response_synthesizer
from LLM_common_utils import *
from gpt_module import generate_text_with_context

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

def load_generation_data(directory_path):
    documents = []
    category_structure_path = os.path.join(directory_path, 'model_generation', 'generation_category_structure.json')
    
    # 加载类别结构
    with open(category_structure_path, 'r', encoding='utf-8') as f:
        category_structure = json.load(f)
    
    # 遍历类别结构并加载对应的 Markdown 文件
    for category in category_structure['categories']:
        for subcategory in category['subcategories']:
            for item_type in subcategory['types']:
                file_path = os.path.join(directory_path, 'model_generation', category['name'], subcategory['name'], item_type['file'])
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        doc = Document(text=content, metadata={
                            "category": category['name'],
                            "subcategory": subcategory['name'],
                            "item_type": item_type['name'],
                            "file_name": item_type['file'],
                            "file_path": os.path.abspath(file_path)
                        })
                        documents.append(doc)
                    logger.info(f"Loaded file: {file_path}")
                else:
                    logger.warning(f"File not found - {file_path}")
    
    logger.info(f"Total documents loaded: {len(documents)}")
    return documents, category_structure

# 创建向量存储索引
def create_generation_index(documents):
    db_path = "./chroma_db_generation"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        logger.info("Existing generation database deleted.")
    
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("generation_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002", api_key=api_key)
    return VectorStoreIndex.from_documents(documents, storage_context=storage_context, embed_model=embed_model)

# 配置查询引擎
def configure_generation_query_engine(index):
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
def query_generation_documentation(query_engine, query):
    response = query_engine.query(query)
    if response.source_nodes:
        file_path = response.source_nodes[0].node.metadata.get('file_path')
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    return "No relevant generation information found."

class GenerationProperties(PropertyGroup):
    input_text: StringProperty(name="Generation Query", default="")

class GENERATION_OT_query(Operator):
    bl_idname = "generation.query"
    bl_label = "Query Generation DB"

    def execute(self, context):
        props = context.scene.generation_tool
        query = props.input_text
        result = query_generation_documentation(context.scene.generation_query_engine, query)
        print("Generation Query Result:", result)
        logger.info(f"Generation Query Result Length: {len(result)}")
        return {'FINISHED'}

class GENERATION_OT_generate_model(Operator):
    bl_idname = "generation.generate_model"
    bl_label = "Generate 3D Model"

    def execute(self, context):
        try:
            props = context.scene.generation_tool
            query = props.input_text
            
            # 使用LlamaDB查询相关文档
            result = query_generation_documentation(context.scene.generation_query_engine, query)
            logger.info(f"Generation DB Query Result Length: {len(result)}")

            # 将查询结果发送到GPT-4生成命令
            gpt_tool = context.scene.gpt_tool
            initialize_conversation(gpt_tool)
            messages = [{"role": msg.role, "content": msg.content} for msg in gpt_tool.messages]
            
            prompt = f"基于以下信息生成Blender命令来创建3D模型：\n\n用户查询：{query}\n\n相关生成文档：{result}\n\n请生成适当的Blender Python命令来创建3D模型，注意当前的运行函数允许导入新的库，所以请生成代码时也import相关的库。"
            
            response = generate_text_with_context(messages, prompt)
            logger.info(f"GPT-4 Generated Commands for 3D Model: {response}")

            # 执行生成的Blender命令
            execute_blender_command(response)

            # 更新对话历史
            user_message = gpt_tool.messages.add()
            user_message.role = "user"
            user_message.content = prompt

            gpt_message = gpt_tool.messages.add()
            gpt_message.role = "assistant"
            gpt_message.content = response

        except Exception as e:
            logger.error(f"Error in GENERATION_OT_generate_model.execute: {e}")
            print(f"Error: {str(e)}")

        return {'FINISHED'}

class GENERATION_PT_panel(Panel):
    bl_label = "3D Model Generation"
    bl_idname = "GENERATION_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        props = context.scene.generation_tool

        layout.prop(props, "input_text")
        layout.operator("generation.query")
        layout.operator("generation.generate_model")

def initialize_generation_db():
    db_path = "./chroma_db_generation"
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("generation_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    bpy.types.Scene.generation_query_engine = configure_generation_query_engine(index)
    logger.info("Generation DB initialized successfully.")