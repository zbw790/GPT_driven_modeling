# update_database.py

"""
This module provides functionality to update various databases used in the LLM-driven modeling system.
It includes functions to update modification, generation, component, and material databases.
"""

import os
import shutil
import logging
from llm_driven_modelling.llama_index_library.llama_index_model_modification import (
    load_modification_data,
    create_modification_index,
)
from llm_driven_modelling.llama_index_library.llama_index_model_generation import (
    load_generation_data,
    create_generation_index,
)
from llm_driven_modelling.llama_index_library.llama_index_component_library import (
    load_component_data,
    create_component_index,
)
from llm_driven_modelling.llama_index_library.llama_index_material_library import (
    load_material_data,
    create_material_index,
)
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")


def update_modification_database():
    """
    Update the modification database by loading new data and recreating the index.
    """
    try:
        data_directory = "./data"
        documents, _ = load_modification_data(data_directory)

        db_path = "./database/chroma_db_modification"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            logger.info("Existing modification database deleted.")

        create_modification_index(documents)
        logger.info("Modification database updated successfully.")
    except Exception as e:
        logger.error(f"Error updating modification database: {str(e)}")


def update_generation_database():
    """
    Update the generation database by loading new data and recreating the index.
    """
    try:
        data_directory = "./data"
        documents, _ = load_generation_data(data_directory)

        db_path = "./database/chroma_db_generation"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            logger.info("Existing generation database deleted.")

        create_generation_index(documents)
        logger.info("Generation database updated successfully.")
    except Exception as e:
        logger.error(f"Error updating generation database: {str(e)}")


def update_component_database():
    """
    Update the component database by loading new data and recreating the index.
    """
    try:
        data_directory = "./data"
        documents, _ = load_component_data(data_directory)

        db_path = "./database/chroma_db_components"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            logger.info("Existing component database deleted.")

        create_component_index(documents)
        logger.info("Component database updated successfully.")
    except Exception as e:
        logger.error(f"Error updating component database: {str(e)}")


def update_material_database():
    """
    Update the material database by loading new data and recreating the index.
    """
    try:
        data_directory = "./data"
        documents, _ = load_material_data(data_directory)

        db_path = "./database/chroma_db_materials"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            logger.info("Existing material database deleted.")

        create_material_index(documents)
        logger.info("Material database updated successfully.")
    except Exception as e:
        logger.error(f"Error updating material database: {str(e)}")


def update_all_databases():
    """
    Update all databases: modification, generation, component, and material.
    """
    update_modification_database()
    update_generation_database()
    update_component_database()
    update_material_database()


if __name__ == "__main__":
    update_all_databases()
