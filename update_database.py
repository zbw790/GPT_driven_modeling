import os
import shutil
import logging
from llama_db_manager import load_data, create_index
from dotenv import load_dotenv

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(dotenv_path="D:/Tencent_Supernova/api/.env")

def update_database():
    try:
        data_directory = './data'
        documents, _ = load_data(data_directory)
        
        db_path = "./chroma_db"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            logger.info("Existing database deleted.")
        
        create_index(documents)
        logger.info("Database updated successfully.")
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")

if __name__ == "__main__":
    update_database()