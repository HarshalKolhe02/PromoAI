"""
Application logging utility.
"""
import logging
import sys
from app.config import Config


def setup_logger(name: str = "promofinder") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)
    return logger


logger = setup_logger()
