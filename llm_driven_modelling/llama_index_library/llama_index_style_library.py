# llama_index_style_library.py

"""
This module integrates Llama Index functionality for 3D model style management in Blender.
It provides capabilities for loading, indexing, and querying style documentation,
as well as applying styles to 3D models based on user queries and relevant style information.
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
    get_scene_info,
    format_scene_info,
)
from llm_driven_modelling.llm.gpt_module import generate_text_with_context
from llm_driven_modelling.llm.claude_module import generate_text_with_claude
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty, EnumProperty
from llm_driven_modelling.utils.model_viewer_module import (
    save_screenshots,
    save_screenshots_to_path,
)
from llm_driven_modelling.utils.logger_module import setup_logger, log_context

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
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


def load_style_data(directory_path):
    """
    Load style data from the specified directory.

    Args:
        directory_path (str): The path to the directory containing style data.

    Returns:
        tuple: A tuple containing a list of Document objects and the style structure.
    """
    documents = []
    style_library_path = os.path.join(directory_path, "style_library")
    structure_file_path = os.path.join(
        style_library_path, "style_library_structure.json"
    )

    with open(structure_file_path, "r", encoding="utf-8") as f:
        structure = json.load(f)

    for style in structure["styles"]:
        file_path = os.path.join(style_library_path, style["file"])
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                description = preprocess_markdown(content)
                doc = Document(
                    text=description,
                    metadata={
                        "style": style["name"],
                        "file_name": style["file"],
                        "file_path": os.path.abspath(file_path),
                    },
                )
                documents.append(doc)
            logger.info(f"Loaded style file: {file_path}")
        else:
            logger.warning(f"Style file not found - {file_path}")

    logger.info(f"Total style documents loaded: {len(documents)}")
    return documents, structure


def create_style_index(documents):
    """
    Create a vector index for the style documents.

    Args:
        documents (list): A list of Document objects.

    Returns:
        VectorStoreIndex: The created vector index.
    """
    db_path = "./database/chroma_db_styles"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        logger.info("Existing style database deleted.")

    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("style_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002", api_key=api_key)
    return VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, embed_model=embed_model
    )


def configure_style_query_engine(index):
    """
    Configure the query engine for style retrieval.

    Args:
        index (VectorStoreIndex): The vector index for styles.

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


def query_style_documentation(query_engine, query):
    """
    Query the style documentation using the provided query engine.

    Args:
        query_engine (RetrieverQueryEngine): The query engine to use.
        query (str): The query string.

    Returns:
        list: A list of relevant style documentation.
    """
    response = query_engine.query(query)
    results = []
    for node in response.source_nodes:
        file_path = node.node.metadata.get("file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                results.append(f.read())
    return results if results else ["No relevant style information found."]


class StyleProperties(PropertyGroup):
    """Properties for the style query panel."""

    input_text: StringProperty(name="Style Query", default="")
    model_choice: EnumProperty(
        name="Model",
        items=[
            ("GPT", "GPT-4", "Use GPT-4 model"),
            ("CLAUDE", "Claude-3.5", "Use Claude-3.5 model"),
        ],
        default="GPT",
    )


class STYLE_OT_query(Operator):
    """Operator to query the style database."""

    bl_idname = "style.query"
    bl_label = "Query Style DB"

    def execute(self, context):
        props = context.scene.style_tool
        query = props.input_text
        results = query_style_documentation(context.scene.style_query_engine, query)
        for i, result in enumerate(results):
            print(f"Style Query Result {i+1}:", result)
            logger.info(f"Style Query Result {i+1} Length: {len(result)}")
        return {"FINISHED"}


class STYLE_OT_apply_style(Operator):
    """Operator to apply a style to the 3D model."""

    bl_idname = "style.apply_style"
    bl_label = "Apply Style"

    def execute(self, context):
        props = context.scene.style_tool
        query = props.input_text
        model_choice = props.model_choice

        with log_context(logger, query) as log_dir:
            try:
                # Get scene information
                scene_info = get_scene_info()
                formatted_scene_info = format_scene_info(scene_info)

                # Query relevant style documentation
                style_docs = query_style_documentation(
                    context.scene.style_query_engine, query
                )

                # Generate and apply style
                self.generate_and_apply_style(
                    context,
                    query,
                    style_docs,
                    formatted_scene_info,
                    model_choice,
                    log_dir,
                )

                self.report(
                    {"INFO"}, f"Style applied successfully. Logs saved in {log_dir}"
                )
            except Exception as e:
                logger.error(f"An error occurred while applying style: {str(e)}")
                self.report(
                    {"ERROR"}, f"An error occurred while applying style: {str(e)}"
                )

        return {"FINISHED"}

    def generate_and_apply_style(
        self, context, query, style_docs, scene_info, model_choice, log_dir
    ):
        """
        Generate and apply style based on query, documentation, and scene information.

        Args:
            context (bpy.types.Context): The current Blender context.
            query (str): The user's style query.
            style_docs (list): A list of relevant style documentation.
            scene_info (str): Formatted scene information.
            model_choice (str): The chosen LLM model.
            log_dir (str): The directory to save logs and screenshots.
        """
        prompt = f"""
        Context:
        You are an AI assistant specialized in applying styles to 3D models in Blender.
        Based on the provided style query, documentation, and scene information, generate Blender Python code to apply the requested style.

        Style query: {query}

        Style documentation:
        {json.dumps(style_docs, ensure_ascii=False, indent=2)}

        Scene information:
        {scene_info}

        Task:
        Generate Blender Python code to apply the requested style to the 3D model in the scene.
        Consider the current scene information and objects when applying the style.

        Output:
        Provide only the Python code that can be directly executed in Blender, without any additional explanation.
        """

        # Generate response based on selected model
        conversation_manager = context.scene.conversation_manager
        initialize_conversation(context)
        prompt_with_history = add_history_to_prompt(context, prompt)

        if model_choice == "GPT":
            style_code = generate_text_with_context(prompt_with_history)
        elif model_choice == "CLAUDE":
            style_code = generate_text_with_claude(prompt_with_history)
        else:
            raise ValueError("Invalid model choice")

        # Update conversation history
        conversation_manager.add_message("user", prompt)
        conversation_manager.add_message("assistant", style_code)

        # Save the generated style code to a file
        with open(
            os.path.join(log_dir, "style_application_code.py"), "w", encoding="utf-8"
        ) as f:
            f.write(style_code)

        # Execute the generated Blender style commands
        try:
            execute_blender_command(style_code)
            logger.debug("Successfully applied style.")
        except Exception as e:
            logger.error(f"Error applying style: {str(e)}")
            self.report({"ERROR"}, f"Error applying style: {str(e)}")

        # Update the view
        bpy.context.view_layer.update()

        # Save screenshots after applying style
        screenshots = save_screenshots()
        screenshot_dir = os.path.join(log_dir, "style_screenshots")
        save_screenshots_to_path(screenshot_dir)
        for screenshot in screenshots:
            logger.debug(f"Style application screenshot saved: {screenshot}")


class STYLE_PT_panel(Panel):
    """Panel for Llama Index Style Library integration in Blender."""

    bl_label = "Llama Index Style Library"
    bl_idname = "STYLE_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        props = context.scene.style_tool

        layout.prop(props, "input_text")
        layout.prop(props, "model_choice")
        layout.operator("style.query")
        layout.operator("style.apply_style")


def initialize_style_db():
    """Initialize the style database and query engine."""
    db_path = "./database/chroma_db_styles"
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("style_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    bpy.types.Scene.style_query_engine = configure_style_query_engine(index)
    logger.info("Style DB initialized successfully.")
