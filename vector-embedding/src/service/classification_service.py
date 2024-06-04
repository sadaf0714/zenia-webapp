from distutils.log import error
from unittest import result
from urllib import response
from schema.classification import SearchTerms
from schema.response import Response
from settings.constants import UNEXPECTED_ERROR_MSG
from utils.search_result import ServiceResult
from settings.logging_config import logger
from exceptions.app_exceptions import AppException
from helpers.classification_helper import get_entity_classfication


def create_classification(search_terms: SearchTerms):
    search_term = search_terms.search_term
    logger.debug("Create classfication service started...")
    result = None

    if not search_term:
        logger.error("Invalid input format")
        result = ServiceResult(
            AppException(
                400, Response(success=False, data={}, error="Invalid input format")
            )
        )    
    else :   
        try:
            entity_classfication = get_entity_classfication(search_term)
            logger.debug("Create classfication done...")
            result = entity_classfication
        except Exception as e:
            logger.exception(e)
            result = ServiceResult(
                AppException(
                    500, Response(success=False, data={}, error=UNEXPECTED_ERROR_MSG)
                )
            )
            
    return result

