from unittest import result
from schema.embedding import SearchTermMetadata
from settings.enums import EmbeddingType
from helpers.embedding_helper import (
    get_embedding_hf,
    get_embedding_lamma,
    get_embedding_openai,
)
from schema.response import Response
from settings.constants import UNEXPECTED_ERROR_MSG
from utils.search_result import ServiceResult
from settings.logging_config import logger
from exceptions.app_exceptions import AppException


def create_embedding(search_term_metadata: SearchTermMetadata):
    result = None
    search_term = search_term_metadata.search_term
    embedding_type = search_term_metadata.type
    if not search_term:
        logger.error("Invalid input format")
        result = ServiceResult(
            AppException(
              400, Response(success=False, data={}, error="Invalid input format" )
            )
        )
    else:
        try:
            if embedding_type == EmbeddingType.OPENAI:
                result = get_embedding_openai(search_term)
            elif embedding_type == EmbeddingType.HUGGINGFACE:
                result = get_embedding_hf(search_term)
            elif embedding_type == EmbeddingType.LAMMAGPT:
                result = get_embedding_lamma(search_term)
        except Exception as e:
            logger.exception(e)
            result = ServiceResult(
                AppException(
                500, Response(success=False, data={}, error=UNEXPECTED_ERROR_MSG)
                )
            )
    return result
