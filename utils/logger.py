import logging
import os

def get_logger():
    if not os.path.exists("logs"):
        os.mkdir("logs")
    logger = logging.getLogger("automation_logger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        filehandler = logging.FileHandler("logs/test.log")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        filehandler.setFormatter(formatter)
        logger.addHandler(filehandler)

    return logger