# llama_index_component_library.py

"""
This module integrates Llama Index functionality for component library management in Blender.
It provides capabilities for loading, indexing, and querying component documentation,
as well as generating Blender commands based on user queries and relevant component information.
"""

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
from llm_driven_modelling.llm.LLM_common_utils import (
    execute_blender_command,
    initialize_conversation,
    add_history_to_prompt,
)
from llm_driven_modelling.llm.gpt_module import generate_text_with_context
from llm_driven_modelling.llm.claude_module import generate_text_with_claude
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty, EnumProperty

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

def preprocess_markdown(content):
    """
    Preprocess markdown content by extracting the first section.

    Args:
        content (str): The markdown content to preprocess.

    Returns:
        str: The preprocessed content.
    """
    return re.split(r"\n##", content)[0]

def load_component_data(directory_path):
    """
    Load component data from the specified directory.

    Args:
        directory_path (str): The path to the directory containing component data.

    Returns:
        tuple: A tuple containing a list of Document objects and the category structure.
    """
    documents = []
    category_structure_path = os.path.join(
        directory_path, "component_library", "component_category_structure.json"
    )

    with open(category_structure_path, "r", encoding="utf-8") as f:
        category_structure = json.load(f)

    for category in category_structure["categories"]:
        for component in category["components"]:
            file_path = os.path.join(
                directory_path, "component_library", category["name"], component["file"]
            )
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    description = preprocess_markdown(content)
                    doc = Document(
                        text=description,
                        metadata={
                            "category": category["name"],
                            "component": component["name"],
                            "file_name": component["file"],
                            "file_path": os.path.abspath(file_path),
                        },
                    )
                    documents.append(doc)
                logger.info(f"Loaded component file: {file_path}")
            else:
                logger.warning(f"Component file not found - {file_path}")

    logger.info(f"Total component documents loaded: {len(documents)}")
    return documents, category_structure

def create_component_index(documents):
    """
    Create a vector index for the component documents.

    Args:
        documents (list): A list of Document objects.

    Returns:
        VectorStoreIndex: The created vector index.
    """
    db_path = "./database/chroma_db_components"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        logger.info("Existing component database deleted.")

    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("component_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002", api_key=api_key)
    return VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, embed_model=embed_model
    )

def configure_component_query_engine(index):
    """
    Configure the query engine for component retrieval.

    Args:
        index (VectorStoreIndex): The vector index for components.

    Returns:
        RetrieverQueryEngine: The configured query engine.
    """
    retriever = VectorIndexRetriever(index=index, similarity_top_k=3)
    response_synthesizer = get_response_synthesizer(
        response_mode="tree_summarize", use_async=True
    )
    return RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.65)],
    )

def query_component_documentation(query_engine, query):
    """
    Query the component documentation using the provided query engine.

    Args:
        query_engine (RetrieverQueryEngine): The query engine to use.
        query (str): The query string.

    Returns:
        list: A list of relevant component documentation.
    """
    response = query_engine.query(query)
    results = []
    for node in response.source_nodes:
        file_path = node.node.metadata.get("file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                results.append(f.read())
    return results if results else ["No relevant component information found."]

class ComponentProperties(PropertyGroup):
    """Properties for the component query panel."""
    input_text: StringProperty(name="Component Query", default="")
    model_choice: EnumProperty(
        name="Model",
        items=[
            ("GPT", "GPT-4", "Use GPT-4 model"),
            ("CLAUDE", "Claude-3.5", "Use Claude-3.5 model"),
        ],
        default="GPT",
    )

class COMPONENT_OT_query(Operator):
    """Operator to query the component database."""
    bl_idname = "component.query"
    bl_label = "Query Component DB"

    def execute(self, context):
        props = context.scene.component_tool
        query = props.input_text
        results = query_component_documentation(
            context.scene.component_query_engine, query
        )
        for i, result in enumerate(results):
            print(f"Component Query Result {i+1}:", result)
            logger.info(f"Component Query Result {i+1} Length: {len(result)}")
        return {"FINISHED"}

class COMPONENT_OT_generate_component(Operator):
    """Operator to generate component based on user query."""
    bl_idname = "component.generate_component"
    bl_label = "Generate Component"

    def execute(self, context):
        try:
            props = context.scene.component_tool
            query = props.input_text
            model_choice = props.model_choice

            # Query relevant documents using LlamaDB
            results = query_component_documentation(
                context.scene.component_query_engine, query
            )
            combined_results = "\n\n".join(results)
            logger.info(f"Component DB Query Results Length: {len(combined_results)}")

            # Prepare prompt
            prompt = f"Based on the following information, generate Blender commands to create or modify components:\n\nUser request: {query}\n\nRelevant component documentation: {combined_results}\n\nPlease generate appropriate Blender Python commands to create or modify components. Note that the current running function allows importing new libraries, so please include necessary import statements in the generated code."

            # Generate response based on selected model
            conversation_manager = context.scene.conversation_manager
            initialize_conversation(context)
            prompt_with_history = add_history_to_prompt(context, prompt)

            if model_choice == "GPT":
                response = generate_text_with_context(prompt_with_history)
            elif model_choice == "CLAUDE":
                response = generate_text_with_claude(prompt_with_history)
            else:
                raise ValueError("Invalid model choice")

            # Update conversation history
            conversation_manager.add_message("user", prompt)
            conversation_manager.add_message("assistant", response)

            logger.info(f"{model_choice} Generated Commands for Component: {response}")

            # Execute generated Blender commands
            execute_blender_command(response)

        except Exception as e:
            logger.error(f"Error in COMPONENT_OT_generate_component.execute: {e}")
            print(f"Error: {str(e)}")

        return {"FINISHED"}

class COMPONENT_PT_panel(Panel):
    """Panel for Llama Index Component Library integration in Blender."""
    bl_label = "Llama Index Component Library"
    bl_idname = "COMPONENT_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        props = context.scene.component_tool

        layout.prop(props, "input_text")
        layout.prop(props, "model_choice")
        layout.operator("component.query")
        layout.operator("component.generate_component")

def initialize_component_db():
    """Initialize the component database and query engine."""
    db_path = "./database/chroma_db_components"
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("component_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    bpy.types.Scene.component_query_engine = configure_component_query_engine(index)
    logger.info("Component DB initialized successfully.")