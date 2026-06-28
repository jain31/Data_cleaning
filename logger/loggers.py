from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

import os
log_dir = os.path.join("logging","logging_ingestion")
def get_logger():
    os.makedirs(log_dir,exist_ok = True)
    log_file = os.path.join(log_dir,"ingestion_log.log")
    logger = logging.getLogger("ingestion")

    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        filename = log_file,
        mode = 'a',
        maxBytes = 5*1024*1024,
        backupCount = 10
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )
    logger.addHandler(handler)
    return logger

