from langchain import OpenAI, PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import PyPDFLoader
import requests
import tempfile
import os

def summarize_pdf_from_url(pdf_url):
    # Fetch PDF content from the URL
    response = requests.get(pdf_url, verify=False)
    if response.status_code != 200:
        print("Failed to fetch PDF from URL:", pdf_url)
        return None
    # Save PDF content to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(response.content)
        temp_file_path = temp_file.name
    # Load PDF content using PyPDFLoader
    loader = PyPDFLoader(temp_file_path)
    docs = loader.load_and_split()
    # Load summarization chain
    llm = OpenAI(temperature=0, api_key=os.getenv("openai.api_key"))
    chain = load_summarize_chain(llm, chain_type="map_reduce")
    # Run summarization
    summary = chain.run(docs)
    # Clean up temporary file
    os.unlink(temp_file_path)
    return summary


def langchainSummary(pdf_url):
    summary = summarize_pdf_from_url(pdf_url)
    return summary
