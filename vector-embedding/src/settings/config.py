import os
from dotenv import load_dotenv
load_dotenv()

PORT = int(os.getenv("PORT"))
HOST = os.getenv("HOST")

REF_PREFIX = "/embedding/api"
OPENAI_MODEL_NAME = "text-embedding-ada-002"
# HUGGINGFACE_MODEL_NAME = "sentence-transformers/paraphrase-distilroberta-base-v2"
# HUGGINGFACE_MODEL_NAME = "sentence-transformers/bert-base-nli-mean-tokens"
HUGGINGFACE_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
GPT_LAMMA_URL = "http://localhost:443/v1/embeddings"
GPT_LAMMA_ACCESS_TOKEN = (
    "C:/Users/Surjeet/Documents/llama.cpp/models/ggml-old-vic7b-q5_0.bin"
)
GPT_LAMMA_MODEL_NAME = "gpt-3.5-turbo"
