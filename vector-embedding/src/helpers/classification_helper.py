import openai
import json
from utils.search_result import ServiceResult
from schema.response import Response
from settings.logging_config import logger
from openai import OpenAI
import os
from dotenv import load_dotenv
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GenerationConfig,
    TextStreamer,
    pipeline,
)
import accelerate
import transformers
import torch
from langchain import HuggingFacePipeline
from langchain.chains import ConversationalRetrievalChain
from torch import cuda, bfloat16
load_dotenv()

# openai.api_key = os.getenv("openai.api_key")
# api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("openai.api_key"))

#huggingface model prompt function
def get_completion_huggingface(prompt, model_id="mistralai/Mistral-7B-Instruct-v0.2"):
    device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

    bnb_config = transformers.BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=bfloat16
    )
    model_config = transformers.AutoConfig.from_pretrained(
        model_id
    )
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        config=model_config,
        #quantization_config=bnb_config,
        device_map='auto',
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    pipe = pipeline("text-generation",
                  model=model,
                  tokenizer = tokenizer,
                  max_new_tokens = 1024,
                  do_sample=True,
                  eos_token_id=tokenizer.eos_token_id,
                  pad_token_id=tokenizer.eos_token_id,
                  temperature = 0.001)
    llm = HuggingFacePipeline(pipeline =pipe)
    qa = ConversationalRetrievalChain.from_llm(
      llm=llm,
      retriever=self.retriever,
      # return_source_documents=True,
      memory=self.memory,
      combine_docs_chain_kwargs={"prompt": self.prompt}

    )
    messages = [{"role": "user", "content": prompt}]
    response = qa({"question":messages})
    return response['answer']

# openAi prompt function
def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content.strip()

# openAi prompt function 2
def get_completion_new(prompt, model="gpt-3.5-turbo"):
    result = {"error":"", "data":""}
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    try:
        result['data'] = response.choices[0].message.content.strip()
    except Exception as e:
        result['error'] = e

    return result    
# this function extracts query response from prompt output          
# returns a dictionary of tagged entities 
def extract_output(text):
    final_string = ""
    start_word = "{"
    end_word = "}"
    start_index = text.find(start_word)
    if start_index == -1 and text != "":
      final_string += text
    elif start_index == -1 and text == "":
        final_string += ""
    else:
      # start_index +=len(start_word
      end_index = text.rindex(end_word) + 1
      final_string += text[start_index:end_index]
    return final_string


# this function is a prompt to convert out query text into english translation
# returns a string of english sentence
def get_english_language(lang_check):
    # this query is used to transform language
    prompt = f"""
    Translate the following text to English and output the english translation only: ```{lang_check}```"""
    response = get_completion(prompt)
    return response


def gpt_prompt_classification(txt):
    prompt = f"""
      [NER] classify all industry,locations,person,organizations from the following query
      which is delimited with triple backticks? and provide output in dictionary format with the following keys:
      industry,location,person,organization.
      Review text: '''{txt}'''
      """
    response = get_completion(prompt)
    return response.strip()


# this function performs NER on our query for both industry and location
# returns a list of tagged entities
def perform_named_enity_classfication(text):
    logger.info(f"Performing named entity..{text}")
    try:
        resp_dict = {"industry":[],"location":[],"person":[],"organization":[]}
        eng_text = get_english_language(text)
        resp = gpt_prompt_classification(eng_text)
        print(resp)
        if "Sorry" and "sorry" not in resp:
            result = json.loads(extract_output(resp))
            if result:
                for k,v in result.items():
                    resp_dict[k] = []
                    if type(v) is list:
                        for item in v:
                            if type(item) is dict:
                                resp_dict[k].append(item['text'])
                            elif item != "" and str(item) != "N/A" and str(item) != "null" and str(item) != "None":
                                resp_dict[k].append(item)
                    else:
                        if v != "" and str(v) != "N/A" and str(v) != "null" and str(v) != "None":
                            resp_dict[k].append(v)
    except Exception as e:
        logger.exception(e)
    return resp_dict
      

def get_entity_classfication(search_term):
    data = {}
    try:
        data = perform_named_enity_classfication(search_term)
    except Exception as e:
        logger.exception(e)
        data["location"] = list()
        data["industry"] = list()
    resp = Response(success=True, data=data, error="")
    return ServiceResult(resp)











# def classify_industry_type(text):
#     tagged_entities = []
#     prompt = f"""
#     [NER] Extract industry type from the following query
#     which is delimited with triple backticks? and only include all the industry types seperated with ',' in queryResponse
#     Review text: '''{text}'''
#     """
#     response = get_completion(prompt)
#     # print("Prompt response :- ",response)
#     output = extract_output(response)
#     # print("\n Output extracted :",output)
#     tagged_entities = str(output).strip().split(',')
#     return tagged_entities


# def classify_locations(text):
#     tagged_entities = []
#     prompt = f"""
#     [NER] Extract locations,places from the following query
#     which is delimited with triple backticks? and only include all the named entities seperated with ',' in queryResponse
#     Review text: '''{text}'''
#     """
#     response = get_completion(prompt)
#     # print("Prompt response :- ",response)
#     output = extract_output(response)
#     # print("\n Output extracted :",output)
#     tagged_entities = str(output).strip().split(',')
#     return tagged_entities
