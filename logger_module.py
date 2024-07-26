# logger_module.py

import logging
import os
from datetime import datetime
from contextlib import contextmanager

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # 添加一个 NullHandler 以防止未配置的 logger 发出警告
    logger.addHandler(logging.NullHandler())
    return logger

@contextmanager
def log_context(logger, input_text):
    # 创建日志文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.dirname(__file__), "model_generation_logs", timestamp)
    os.makedirs(log_dir, exist_ok=True)

    # 配置文件处理器
    log_file = os.path.join(log_dir, "generation_log.txt")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # 添加文件处理器到记录器
    logger.addHandler(file_handler)

    # 移除 NullHandler（如果存在）
    for handler in logger.handlers:
        if isinstance(handler, logging.NullHandler):
            logger.removeHandler(handler)

    try:
        logger.info(f"Starting model generation with input: {input_text}")
        yield log_dir
    finally:
        logger.info("Model generation process completed")
        logger.removeHandler(file_handler)
        file_handler.close()

# 设置根日志记录器，这将影响所有未明确配置的日志记录器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')