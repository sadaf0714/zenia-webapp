from asyncio import exceptions
from fastapi import APIRouter
from schema.embedding import SearchTermMetadata
from schema.classification import SearchTerms, NlpClassification, SparqlGPT, NlpClassificationEntities,NearestFriendParams,PersonToPersonParams, DataExtractionParams, chatCompletion, langchainSummary
from settings.config import REF_PREFIX
from service import embedding_service, classification_service, nlp_text_classification, sparql_gpt_service,graph_path_service,langchain_summarization_service
from schema.similarity import SimilarityMetadata
from utils.search_result import handle_result
from service import gpt_service
import openai
import os
from fastapi import File, UploadFile
from pathlib import Path
from helpers.classification_helper import get_completion_new ,get_completion_huggingface

openai.api_key = os.getenv("openai.api_key")

router = APIRouter(prefix=REF_PREFIX)


@router.get("/getembedding/")
async def create_embedding(search_term_metadata: SearchTermMetadata):
    resp = embedding_service.create_embedding(search_term_metadata)
    return handle_result(resp)


@router.get("/get-classification/")
async def create_classification(search_term: SearchTerms):
    resp = classification_service.create_classification(search_term)
    return handle_result(resp)


@router.get("/get-active-classification/")
async def create_active_classification(similarity_term: SimilarityMetadata):
    resp = gpt_service.get_active_classification(similarity_term.similarity_data,similarity_term.query)
    return handle_result(resp)


@router.get("/get-similarity/")
async def create_similarity_search(similarity_term: SimilarityMetadata):
    resp = gpt_service.create_similarity_search(similarity_term)
    return handle_result(resp)


@router.post("/getClassifiedDataFromURL")
async def get_classified_data_using_NLP(params: NlpClassification):
    resp = nlp_text_classification.getClassifiedDataFromURL(params.url)
    return resp

@router.get("/getSparqlQueryFromGPT")
async def get_sparql_query_from_gpt(params: SparqlGPT):
    resp=sparql_gpt_service.get_sparql_query(params.input)
    return resp

@router.post("/getClassifiedDataFromInputText")
async def get_classified_data_using_NLP_From_Text(params: NlpClassificationEntities):
    resp = nlp_text_classification.getClassifiedDataFromInput(params.input)
    return resp

@router.post("/getClassifiedDataFromDocs/")
async def get_classified_data_from_docs(file: UploadFile = File(...)):
    resp = nlp_text_classification.getClassifiedDataFromDocs(file,Path(file.filename).suffix)
    return resp['extracted_text'] if resp['error'] == None else {}

@router.get("/getSparqlQueryFromGPTForClaimData")
async def get_sparql_query_from_gpt_for_claim_data(params: SparqlGPT):
    resp=sparql_gpt_service.get_sparql_query_for_claim(params.input)
    return resp

@router.post('/getNearestFriend')
def find_nearest_friend(params: NearestFriendParams):
    response = graph_path_service.shortestPath_closestPerson(params.searching_person,params.target_company)
    return response

@router.post('/getHigherLevelFriend')
def find_nearest_friend(params: NearestFriendParams):
    response = graph_path_service.shortestPath_for_HigherLevels(params.searching_person,params.target_company)
    return response


@router.post('/getPersonsPaths')
def find_nearest_friend(params: PersonToPersonParams):
    results = {'records':[]}
    response = graph_path_service.shortestPath_person_to_person(params.searching_person,params.target_person,params.filter_type)
    results['records'] = response
    return results

# @router.get("/getCoverageAmountFromGPTForInsuranceDocument")
# async def get_coverage_amount(params: DataExtractionParams):
#     resp=gpt_service.get_coverage_amount_from_gpt(params.text)
#     return resp
@router.get("/getCoverageAmountFromGPTForInsuranceDocument")
async def get_coverage_amount(params: DataExtractionParams):
    resp=gpt_service.get_coverage_amount_from_huggingface(params.text)
    return resp

@router.get("/getChatCompletion")
async def getChatCompletion(params: chatCompletion):
    return  get_completion_new(params.prompt, params.model)

@router.get("/getChatCompletionMistral")
async def getChatCompletionMistral(params: chatCompletion):
    return  get_completion_huggingface(params.prompt, params.model)
    
@router.post('/langchain-summarization')
def langchainSummarization(params: langchainSummary):
    response = {}
    response['summary'] = langchain_summarization_service.langchainSummary(params.pdf_url)
    return response

