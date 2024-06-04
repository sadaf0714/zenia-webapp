import logging
import os

logger = logging.getLogger("EmbeddingService")
logger.setLevel(logging.INFO)


# configuring the loggers

directory = "../logs"
if not os.path.exists(directory):
    os.makedirs(directory)

file_name = "embedding_service.log"
log_file_full_path = os.path.join(directory, file_name)
reqire_fields = (
    """%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"""
)
formater = logging.Formatter(reqire_fields)
handler = logging.FileHandler(log_file_full_path)
handler.setFormatter(formater)
logger.addHandler(handler)
