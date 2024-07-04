import os
import shutil
import logging
from llama_index_model_modification import load_modification_data, create_modification_index
from llama_index_model_generation import load_generation_data, create_generation_index
from dotenv import load_dotenv

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")

def update_modification_database():
    try:
        data_directory = './data'
        documents, _ = load_modification_data(data_directory)
        
        db_path = "./chroma_db"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            logger.info("Existing modification database deleted.")
        
        create_modification_index(documents)
        logger.info("Modification database updated successfully.")
    except Exception as e:
        logger.error(f"Error updating modification database: {str(e)}")

def update_generation_database():
    try:
        data_directory = './data'
        documents, _ = load_generation_data(data_directory)
        
        db_path = "./chroma_db_generation"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            logger.info("Existing generation database deleted.")
        
        create_generation_index(documents)
        logger.info("Generation database updated successfully.")
    except Exception as e:
        logger.error(f"Error updating generation database: {str(e)}")

def update_all_databases():
    update_modification_database()
    update_generation_database()

if __name__ == "__main__":
    update_all_databases()