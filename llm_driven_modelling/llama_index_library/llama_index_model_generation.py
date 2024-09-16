# llama_index_model_generation.py

"""
This module integrates Llama Index functionality for 3D model generation in Blender.
It provides capabilities for loading, indexing, and querying generation documentation,
as well as generating 3D models based on user queries and relevant generation information.
"""

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
from llm_driven_modelling.llm.LLM_common_utils import (
    execute_blender_command,
    initialize_conversation,
    add_history_to_prompt,
)
from llm_driven_modelling.llm.gpt_module import generate_text_with_context
from llm_driven_modelling.llm.claude_module import generate_text_with_claude

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

def preprocess_markdown(content):
    """
    Extract the description part from the markdown content.

    Args:
        content (str): The markdown content to preprocess.

    Returns:
        str: The extracted description (content before the first ## heading).
    """
    return re.split(r"\n##", content)[0]

def load_generation_data(directory_path):
    """
    Load generation data from the specified directory.

    Args:
        directory_path (str): The path to the directory containing generation data.

    Returns:
        tuple: A tuple containing a list of Document objects and the category structure.
    """
    documents = []
    category_structure_path = os.path.join(
        directory_path, "model_generation", "generation_category_structure.json"
    )

    # Load category structure
    with open(category_structure_path, "r", encoding="utf-8") as f:
        category_structure = json.load(f)

    # Traverse the category structure and load corresponding Markdown files
    for category in category_structure["categories"]:
        for subcategory in category["subcategories"]:
            for item_type in subcategory["types"]:
                file_path = os.path.join(
                    directory_path,
                    "model_generation",
                    category["name"],
                    subcategory["name"],
                    item_type["file"],
                )
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Use preprocessing function to extract the description part
                        description = preprocess_markdown(content)
                        doc = Document(
                            text=description,
                            metadata={
                                "category": category["name"],
                                "subcategory": subcategory["name"],
                                "item_type": item_type["name"],
                                "file_name": item_type["file"],
                                "file_path": os.path.abspath(file_path),
                            },
                        )
                        documents.append(doc)
                    logger.info(f"Loaded file: {file_path}")
                else:
                    logger.warning(f"File not found - {file_path}")

    logger.info(f"Total documents loaded: {len(documents)}")
    return documents, category_structure

def create_generation_index(documents):
    """
    Create a vector index for the generation documents.

    Args:
        documents (list): A list of Document objects.

    Returns:
        VectorStoreIndex: The created vector index.
    """
    db_path = "./database/chroma_db_generation"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        logger.info("Existing generation database deleted.")

    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("generation_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002", api_key=api_key)
    return VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, embed_model=embed_model
    )

def configure_generation_query_engine(index):
    """
    Configure the query engine for generation retrieval.

    Args:
        index (VectorStoreIndex): The vector index for generation documents.

    Returns:
        RetrieverQueryEngine: The configured query engine.
    """
    retriever = VectorIndexRetriever(index=index, similarity_top_k=1)
    response_synthesizer = get_response_synthesizer(
        response_mode="tree_summarize", use_async=True
    )
    return RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.6)],
    )

def query_generation_documentation(query_engine, query):
    """
    Query the generation documentation using the provided query engine.

    Args:
        query_engine (RetrieverQueryEngine): The query engine to use.
        query (str): The query string.

    Returns:
        str: The relevant generation information or a default message if not found.
    """
    response = query_engine.query(query)
    if response.source_nodes:
        file_path = response.source_nodes[0].node.metadata.get("file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
    return "No relevant generation information found."

class GenerationProperties(PropertyGroup):
    """Properties for the generation query panel."""
    input_text: StringProperty(name="Generation Query", default="")
    model_choice: EnumProperty(
        name="Model",
        items=[
            ("GPT", "GPT-4", "Use GPT-4 model"),
            ("CLAUDE", "Claude-3.5", "Use Claude-3.5 model"),
        ],
        default="GPT",
    )

class GENERATION_OT_query(Operator):
    """Operator to query the generation database."""
    bl_idname = "generation.query"
    bl_label = "Query Generation DB"

    def execute(self, context):
        props = context.scene.generation_tool
        query = props.input_text
        result = query_generation_documentation(
            context.scene.generation_query_engine, query
        )
        print("Generation Query Result:", result)
        logger.info(f"Generation Query Result Length: {len(result)}")
        return {"FINISHED"}

class GENERATION_OT_generate_model(Operator):
    """Operator to generate a 3D model based on user query."""
    bl_idname = "generation.generate_model"
    bl_label = "Generate 3D Model"

    def execute(self, context):
        try:
            props = context.scene.generation_tool
            query = props.input_text
            model_choice = props.model_choice

            # Query relevant documents using LlamaDB
            result = query_generation_documentation(
                context.scene.generation_query_engine, query
            )
            logger.info(f"Generation DB Query Result {result}")
            logger.info(f"Generation DB Query Result Length: {len(result)}")

            # Prepare prompt
            prompt = f"Based on the following information, generate Blender commands to create a 3D model:\n\nUser generation request: {query}\n\nRelevant generation documentation: {result}\n\nPlease generate appropriate Blender Python commands to create the 3D model. Note that the current running function allows importing new libraries, so please include necessary import statements in the generated code."

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

            logger.info(f"{model_choice} Generated Commands for 3D Model: {response}")

            # Execute generated Blender commands
            execute_blender_command(response)

        except Exception as e:
            logger.error(f"Error in GENERATION_OT_generate_model.execute: {e}")
            print(f"Error: {str(e)}")

        return {"FINISHED"}

class GENERATION_PT_panel(Panel):
    """Panel for Llama Index Model Generation integration in Blender."""
    bl_label = "Llama Index Model Generation"
    bl_idname = "GENERATION_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        props = context.scene.generation_tool

        layout.prop(props, "input_text")
        layout.prop(props, "model_choice")
        layout.operator("generation.query")
        layout.operator("generation.generate_model")

def initialize_generation_db():
    """Initialize the generation database and query engine."""
    db_path = "./database/chroma_db_generation"
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("generation_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    bpy.types.Scene.generation_query_engine = configure_generation_query_engine(index)
    logger.info("Generation DB initialized successfully.")