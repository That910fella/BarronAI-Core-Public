from loguru import logger
import sys, os

def setup_logger():
    level = os.getenv("LOG_LEVEL", "INFO")
    logger.remove()
    logger.add(sys.stdout, level=level, backtrace=False, diagnose=False,
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}")
    return logger
