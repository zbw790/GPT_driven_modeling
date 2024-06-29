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

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

def load_data(directory_path):
    documents = []
    category_structure_path = os.path.join(directory_path, 'category_structure.json')
    
    # 加载类别结构
    with open(category_structure_path, 'r', encoding='utf-8') as f:
        category_structure = json.load(f)
    
    # 遍历类别结构并加载对应的 Markdown 文件
    for category in category_structure['categories']:
        for subcategory in category['subcategories']:
            for problem in subcategory['problems']:
                file_path = os.path.join(directory_path, 'furniture', subcategory['name'].lower(), problem['file'])
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        doc = Document(text=content, metadata={
                            "category": category['name'],
                            "subcategory": subcategory['name'],
                            "problem": problem['name'],
                            "file_name": problem['file'],
                            "file_path": os.path.abspath(file_path)  # 使用绝对路径
                        })
                        documents.append(doc)
                    logger.info(f"Loaded file: {file_path}")
                else:
                    logger.warning(f"File not found - {file_path}")
    
    logger.info(f"Total documents loaded: {len(documents)}")
    return documents, category_structure

# 创建向量存储索引
def create_index(documents):
    db_path = "./chroma_db"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        logger.info("Existing database deleted.")
    
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("operation_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002", api_key=api_key)
    return VectorStoreIndex.from_documents(documents, storage_context=storage_context, embed_model=embed_model)

# 配置查询引擎
def configure_query_engine(index):
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
def query_documentation(query_engine, query):
    response = query_engine.query(query)
    if response.source_nodes:
        # 获取最相关文档的文件路径
        file_path = response.source_nodes[0].node.metadata.get('file_path')
        if file_path and os.path.exists(file_path):
            # 直接读取并返回整个文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    return "No relevant information found."

def update_index():
    try:
        data_directory = './data'
        documents, _ = load_data(data_directory)
        index = create_index(documents)
        bpy.types.Scene.query_engine = configure_query_engine(index)
        logger.info("Index updated successfully.")
    except Exception as e:
        logger.error(f"Error updating index: {str(e)}")
    return 3600  # 返回秒数，表示下次更新的间隔

class LlamaDBProperties(PropertyGroup):
    input_text: StringProperty(name="Query", default="")

class LLAMADB_OT_query(Operator):
    bl_idname = "llamadb.query"
    bl_label = "Query LlamaDB"

    def execute(self, context):
        props = context.scene.llama_db_tool
        query = props.input_text
        result = query_documentation(context.scene.query_engine, query)
        print("Query Result:", result)
        logger.info(f"Query Result Length: {len(result)}")
        return {'FINISHED'}

class LLAMADB_OT_query_with_screenshots(Operator):
    bl_idname = "llamadb.query_with_screenshots"
    bl_label = "Query with Screenshots"

    def execute(self, context):
        try:
            # 获取截图并发送到GPT-4
            screenshots_path = os.path.join(os.path.dirname(__file__), 'screenshots')
            screenshots = [os.path.join(screenshots_path, f) for f in os.listdir(screenshots_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            image_messages = []
            for screenshot in screenshots:
                base64_image = encode_image(screenshot)
                image_messages.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "low"
                        }
                    }
                )

            prompt = "所有的图片皆来自于同一模型，你觉得这个物品像什么东西，有什么问题。"
            text_message = {
                "type": "text",
                "text": prompt
            }

            request_data = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [text_message] + image_messages
                    }
                ],
                "max_tokens": 2560,
                "temperature": 0.8,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=request_data
            )
            gpt_description = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"GPT-4 Response: {gpt_description}")

            # 使用GPT-4的描述作为LlamaDB的查询输入
            result = query_documentation(context.scene.query_engine, gpt_description)
            print("Query with Screenshots Result:", result)
            logger.info(f"Query with Screenshots Result Length: {len(result)}")

        except Exception as e:
            logger.error(f"Error in LLAMADB_OT_query_with_screenshots.execute: {e}")
            print(f"Error: {str(e)}")

        return {'FINISHED'}

class LLAMADB_OT_update_index(Operator):
    bl_idname = "llamadb.update_index"
    bl_label = "Update LlamaDB Index"

    def execute(self, context):
        update_index()
        return {'FINISHED'}

class LLAMADB_PT_panel(Panel):
    bl_label = "LlamaDB Query"
    bl_idname = "LLAMADB_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        props = context.scene.llama_db_tool

        layout.prop(props, "input_text")
        layout.operator("llamadb.query")
        layout.operator("llamadb.query_with_screenshots")
        layout.operator("llamadb.update_index")

def initialize_llama_db():
    update_index()
    bpy.app.timers.register(update_index)
