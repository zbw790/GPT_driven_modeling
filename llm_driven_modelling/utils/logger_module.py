# logger_module.py

"""
This module provides logging functionality for the Blender addon.
It includes a custom logger setup and a context manager for log handling.
"""

import logging
import os
from datetime import datetime
from contextlib import contextmanager
import shutil


def setup_logger(name):
    """
    Set up a logger with a null handler.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.NullHandler())
    return logger


@contextmanager
def log_context(logger, input_text):
    """
    Context manager for handling log files during model generation.

    Args:
        logger (logging.Logger): The logger to use.
        input_text (str): The input text for model generation.

    Yields:
        str: The path to the log directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_log_dir = r"D:\GPT_driven_modeling\logs\model_generation_logs"
    log_dir = os.path.join(base_log_dir, timestamp)
    os.makedirs(log_dir, exist_ok=True)

    # System log (essential information)
    system_log_file = os.path.join(log_dir, "system_log.md")
    system_handler = logging.FileHandler(system_log_file)
    system_handler.setLevel(logging.INFO)
    system_formatter = logging.Formatter(
        "## %(asctime)s - %(levelname)s\n\n%(message)s\n\n"
    )
    system_handler.setFormatter(system_formatter)

    # Debug log
    debug_log_file = os.path.join(log_dir, "debug_log.md")
    debug_handler = logging.FileHandler(debug_log_file)
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter(
        "## %(asctime)s - %(levelname)s\n\n%(message)s\n\n"
    )
    debug_handler.setFormatter(debug_formatter)

    logger.addHandler(system_handler)
    logger.addHandler(debug_handler)

    # Remove NullHandler if present
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


# Configure root logger, which affects all loggers not explicitly configured
logging.basicConfig(
    level=logging.DEBUG,
    format="## %(asctime)s - %(name)s - %(levelname)s\n\n%(message)s\n\n",
)
