from settings.config import (
    OPENAI_MODEL_NAME,
    HUGGINGFACE_MODEL_NAME,
    GPT_LAMMA_MODEL_NAME,
    GPT_LAMMA_ACCESS_TOKEN,
    GPT_LAMMA_URL,
)
from sentence_transformers import SentenceTransformer
from utils.search_result import ServiceResult
from schema.response import Response
from settings.logging_config import logger
import json
import requests
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


# api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("openai.api_key"))



def get_embedding(text, engine):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=engine).data[0].embedding


def get_embedding_openai(terms: list):
    idx = 0
    data = {}
    for term in terms:
        try:
            search_term_vector = get_embedding(term, engine=OPENAI_MODEL_NAME)
            
        except Exception as e:
            search_term_vector = []
            logger.error(f"Exception while getting embedding for {term}", e)
        data[f"term_{idx}"] = search_term_vector
        idx += 1
    resp = Response(success=True, data=data, error="")
    return ServiceResult(resp)


def get_embedding_hf(terms: list):
    idx = 0
    data = {}
    for term in terms:
        try:
            model = SentenceTransformer(HUGGINGFACE_MODEL_NAME)
            search_term_vector = model.encode(term).tolist()
        except Exception as e:
            search_term_vector = []
            logger.exception(f"Exception occured for {term} %s", e)
        data[f"term_{idx}"] = search_term_vector
        idx += 1
    resp = Response(success=True, data=data, error="")
    return ServiceResult(resp)


def get_embedding_lamma(terms: list):
    idx = 0
    data = {}
    for term in terms:
        try:
            payload = {"model": GPT_LAMMA_MODEL_NAME, "input": term}
            headers = {
                "Authorization": f"Bearer {GPT_LAMMA_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
            reponse = requests.post(
                GPT_LAMMA_URL, data=json.dumps(payload), headers=headers
            )
            search_term_vector = reponse.json().get("data")[0].get("embedding")
        except Exception as e:
            search_term_vector = []
            logger.exception(f"Exception occured for {term} %s", e)
        data[f"term_{idx}"] = search_term_vector
        idx += 1
    resp = Response(success=True, data=data, error="")
    return ServiceResult(resp)
