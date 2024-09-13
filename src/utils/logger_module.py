# logger_module.py

import logging
import os
from datetime import datetime
from contextlib import contextmanager
import shutil


def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.NullHandler())
    return logger


@contextmanager
def log_context(logger, input_text):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_log_dir = r"D:\GPT_driven_modeling\logs\model_generation_logs"
    log_dir = os.path.join(base_log_dir, timestamp)
    os.makedirs(log_dir, exist_ok=True)

    # 系统日志（必要信息）
    system_log_file = os.path.join(log_dir, "system_log.md")
    system_handler = logging.FileHandler(system_log_file)
    system_handler.setLevel(logging.INFO)
    system_formatter = logging.Formatter(
        "## %(asctime)s - %(levelname)s\n\n%(message)s\n\n"
    )
    system_handler.setFormatter(system_formatter)

    # 调试日志
    debug_log_file = os.path.join(log_dir, "debug_log.md")
    debug_handler = logging.FileHandler(debug_log_file)
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter(
        "## %(asctime)s - %(levelname)s\n\n%(message)s\n\n"
    )
    debug_handler.setFormatter(debug_formatter)

    logger.addHandler(system_handler)
    logger.addHandler(debug_handler)

    # 移除 NullHandler（如果存在）
    for handler in logger.handlers:
        if isinstance(handler, logging.NullHandler):
            logger.removeHandler(handler)

    try:
        logger.info(f"Starting model generation with input: {input_text}")
        yield log_dir
    finally:
        logger.info("Model generation process completed")
        logger.removeHandler(system_handler)
        logger.removeHandler(debug_handler)
        system_handler.close()
        debug_handler.close()


# 设置根日志记录器，这将影响所有未明确配置的日志记录器
logging.basicConfig(
    level=logging.DEBUG,
    format="## %(asctime)s - %(name)s - %(levelname)s\n\n%(message)s\n\n",
)
