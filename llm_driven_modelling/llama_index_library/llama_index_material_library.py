# llama_index_material_library.py

"""
This module integrates Llama Index functionality for material library management in Blender.
It provides capabilities for loading, indexing, and querying material documentation,
as well as generating and applying materials based on user queries and scene information.
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


def load_material_data(directory_path):
    """
    Load material data from the specified directory.

    Args:
        directory_path (str): The path to the directory containing material data.

    Returns:
        tuple: A tuple containing a list of Document objects and the material structure.
    """
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
    """
    Create a vector index for the material documents.

    Args:
        documents (list): A list of Document objects.

    Returns:
        VectorStoreIndex: The created vector index.
    """
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
    """
    Configure the query engine for material retrieval.

    Args:
        index (VectorStoreIndex): The vector index for materials.

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


def query_material_documentation(query_engine, query):
    """
    Query the material documentation using the provided query engine.

    Args:
        query_engine (RetrieverQueryEngine): The query engine to use.
        query (str): The query string.

    Returns:
        list: A list of relevant material documentation.
    """
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
    Extract JSON data from Claude's response, removing comments and non-JSON content.

    Args:
        response (str): The response from Claude.

    Returns:
        str: The extracted JSON data as a string.
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
    """Properties for the material query panel."""

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
    """Operator to query the material database."""

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
    """Operator to generate and apply materials to the generated model."""

    bl_idname = "material.apply_materials"
    bl_label = "Apply Materials"
    bl_description = "Apply materials to the generated model"

    def execute(self, context):
        props = context.scene.model_generation_tool
        user_input = props.input_text

        with log_context(logger, user_input) as log_dir:
            try:
                # Get scene information
                scene_info = get_scene_info()
                formatted_scene_info = format_scene_info(scene_info)

                # Step 1: Analyze scene information and determine required materials
                material_requirements = self.analyze_scene_for_materials(
                    formatted_scene_info
                )

                # Step 2: Query relevant material documentation
                material_docs = self.query_material_docs(material_requirements)

                # Step 3: Generate and apply materials
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
        """
        Analyze the scene and determine required materials for each object.

        Args:
            scene_info (str): Formatted scene information.

        Returns:
            dict: A dictionary of object names and their required material types.
        """
        prompt = f"""
        Context:
        You are an AI assistant specialized in analyzing 3D scenes and determining required materials.
        Based on the provided scene information and model description, determine the material type needed for each object.

        Scene information:
        {scene_info}

        Task:
        Analyze each object in the scene and determine the material type they might need.
        Consider the object's name, shape, and possible use.

        Output:
        Provide a JSON object with object names as keys and suggested material types as values.
        Note that some materials are built-in for the Blender scene, such as Camera, which do not need additional materials:
        {{
            "Table_Top": "wood",
            "Table_Leg": "metal",
            "Chair_Seat": "fabric",
            "Lamp_Shade": "glass"
        }}

        Provide only the JSON object, without any additional explanation.
        """
        response = generate_text_with_claude(prompt)
        return json.loads(response)

    def query_material_docs(self, material_requirements):
        """
        Query material documentation based on material requirements.

        Args:
            material_requirements (dict): A dictionary of object names and their required material types.

        Returns:
            list: A list of unique material documents.
        """
        material_docs = {}
        unique_docs = set()  # To store unique documents

        for obj_name, material_type in material_requirements.items():
            query = f"Material type: {material_type}"
            results = query_material_documentation(
                bpy.types.Scene.material_query_engine, query
            )

            # Filter and add only unique documents
            unique_results = []
            for result in results:
                if result not in unique_docs:
                    unique_docs.add(result)
                    unique_results.append(result)

            material_docs[obj_name] = unique_results

        # Combine all unique documents into a single list
        all_unique_docs = list(unique_docs)

        return all_unique_docs

    def generate_and_apply_materials(
        self, context, material_requirements, material_docs, log_dir
    ):
        """
        Generate and apply materials based on requirements and documentation.

        Args:
            context (bpy.types.Context): The current Blender context.
            material_requirements (dict): A dictionary of object names and their required material types.
            material_docs (list): A list of relevant material documentation.
            log_dir (str): The directory to save logs and screenshots.
        """
        logger.info(f"Material requirements: {material_requirements}")
        logger.info(f"Material documentation: {material_docs}")
        prompt = f"""
        Context:
        You are an AI assistant specialized in generating materials for 3D models.
        Based on the provided material requirements and related documentation, generate Blender Python code to create and apply materials.

        Note:
        1. Do not use "Subsurface", "Sheen", "Emission", "Transmission" as direct input parameters.
           These are composite parameters that need to be achieved through other allowed parameters.
        2. For color and vector type inputs, always use list format instead of single float values. For example:
           - For color inputs (like Base Color, Specular Tint, etc.), use a list of 4 values: [R, G, B, A]
           - For vector inputs (like Normal), use a list of 3 values: [X, Y, Z]
           - For single value inputs, use float directly

        Material requirements:
        {json.dumps(material_requirements, ensure_ascii=False, indent=2)}

        Material documentation:
        {json.dumps(material_docs, ensure_ascii=False, indent=2)}

        Task:
        Generate appropriate materials for each object and create Blender Python code to apply these materials.
        Use the Principled BSDF shader and only use the following allowed input parameters:

        Allowed Principled BSDF input parameters:
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
        Provide Python code that can be directly executed in Blender. The code should:
        1. Create new materials for each object
        2. Set various parameters for the materials
        3. Apply the materials to the corresponding objects
        4. Use nodes to create more complex material effects (such as wood grain, metal texture, etc.)

        Provide only the Python code, without any additional explanation.
        """
        material_code = generate_text_with_claude(prompt)

        # Save the generated material code to a file
        with open(
            os.path.join(log_dir, "material_application_code.py"), "w", encoding="utf-8"
        ) as f:
            f.write(material_code)

        # Execute the generated Blender material commands
        try:
            execute_blender_command(material_code)
            logger.debug("Successfully applied materials.")
        except Exception as e:
            logger.error(f"Error applying materials: {str(e)}")
            self.report({"ERROR"}, f"Error applying materials: {str(e)}")

        # Update the view
        self.update_blender_view(context)

        # Save screenshots after applying materials
        screenshots = save_screenshots()
        screenshot_dir = os.path.join(log_dir, "material_screenshots")
        save_screenshots_to_path(screenshot_dir)
        for screenshot in screenshots:
            logger.debug(f"Material application screenshot saved: {screenshot}")

    def update_blender_view(self, context):
        """
        Update the Blender view to reflect changes.

        Args:
            context (bpy.types.Context): The current Blender context.
        """
        # Ensure changes are immediately visible
        bpy.context.view_layer.update()
        logger.debug("Blender view updated.")


class MATERIAL_PT_panel(Panel):
    """Panel for Llama Index Material Library integration in Blender."""

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
    """Initialize the material database and query engine."""
    db_path = "./database/chroma_db_materials"
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("material_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    bpy.types.Scene.material_query_engine = configure_material_query_engine(index)
    logger.info("Material DB initialized successfully.")
