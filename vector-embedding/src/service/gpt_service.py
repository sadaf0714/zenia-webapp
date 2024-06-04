import json
from schema.similarity import SimilarityMetadata
from schema.response import Response
from helpers.classification_helper import get_completion, get_completion_huggingface
from utils.search_result import ServiceResult
from settings.logging_config import logger


def create_similarity_search(similarity_data: SimilarityMetadata):
    logger.info("Create Similarity Started!")
    resp = find_prompt_similarity(similarity_data.similarity_data,
                                  similarity_data.query)
    logger.info("Create Similarity Done!")
    return ServiceResult(resp)


def get_string_list(text):
    name_list = []
    for i in range(1, 5):
        word_index = text.find(str(i) + ".") + 2
        next_index = text.find(str(i+1) + ".")
        word = str(text[word_index:next_index]).strip()
        name_list.append(word)
        if i == 4:
            word = str(text[next_index + 2:]).strip()
            name_list.append(word)
    return name_list


def get_output_list(text):
    names_list, string_format = [], 0
    start_word, end_word = "[", "]"
    start_index = text.find(start_word)
    if start_index == -1:
        string_format = 1
    else:
        if text.find(end_word) == -1:
            string_format = 1
        else:
            end_index = text.find(end_word)
            final_string = str(text[start_index:end_index + 1]).strip()
            names_list += eval(final_string)
    if string_format == 1 and "Top" in text:
        names_list += get_string_list(text)
    return names_list


def get_json_list(result: str, similar_results: dict):
    resp_list = []
    if "Sorry" in result or "sorry" in result:
        pass
    else:
        resp = get_output_list(result)
        if resp:
            for items in similar_results:
                if items.get('name') in resp:
                    resp_list.append(items)
        else:
            pass
    return resp_list

def extract_output(text):
    final_string = ""
    start_word = "{"
    end_word = "}"
    start_index = text.find(start_word)
    if start_index == -1:
      return "{}"
    else:
      # start_index +=len(start_word
      end_index = text.find(end_word) + 1  
      final_string += text[start_index:end_index]
    return final_string


def get_default_json(similar_data:dict):
    temp_list,i = [],0
    for item in similar_data:
        if i <5:
            temp_list.append(item)
        i+=1
    return temp_list


def get_active_classification(json_dataset: dict, query: str):
    prompt = f"""
        You are given a json dataset containing company information. Your task is to classify the companies based on the query in the given dataset.

        Instructions:
        - Consider the data from the given dataset only.
        - Don't retrieve any company information from internet.
        - If any attribute is missing for a company, assign the appropriate tag based on the query but don't search internet.
        - Do not provide code to perform the given task.
        - Match the query with the given json dataset to determine the appropriate tags according to the dataset.
        - Provide the output in dictionary format, where the keys are company names and the values are the tags defined in the query.

        Note:
        - The classification will be based on the information available in the given dataset only.
        - The dataset may contain varying or modified attributes for a companies, and the classification should be based on those values.

        Dataset:
        {json_dataset} 

        Query:
        {query}
        """   
    response = get_completion(prompt)
    resp_dict = {}
    if "Sorry" not in response:
        resp_str = extract_output(response)
        resp_dict = eval(resp_str)
    return ServiceResult(resp_dict)


def find_prompt_similarity(json_dataset: dict, query: str):
    data = dict()
    prompt = f"""
    You are given a dataset delimited with triple backticks. Your task is to match the query in the given dataset and 
    find top five names that are most similar to the query in the dataset.
    Instructions:
     - You have to search the query in the given dataset only
     - Return top five most similar names only in the list format
     - Return empty list if you don't find any results

    Output Instructions:
        - please don't return any explaination or code.
        - please return top five similar names only from the given json_dataset.
     '''{json_dataset}'''
    query : '''{query}'''
    """
    response = get_completion(prompt)
    data["resp"] = get_json_list(response, json_dataset)
    if data['resp'] == []:
        print("NO search found returning default dataset")
        data['resp'] = get_default_json(json_dataset)
    return Response(success=True, data=data, error="")

# def get_prompt_for_coverage_amount_extraction(sample_data):
#     prompt = f"""You are given a travelling policy pdf delimited with triple backticks.Extract the amounts related to following travel insurance coverages from the given text:

#     1. Trip Cancellation coverage
#     2. Trip Interruption
#     3. Medical Evacuation
#     4. Emergency Medical
#     5. Baggage Loss
#     6. Flight Accident
#     7. Accidental Death

#     Ensure that if any of these details are not mentioned in the text, the output should be marked as null or none for that particular detail. Provide only the relevant information without adding any extra details. 
#     Format the output as a simple JSON string wiht only key values no nesting or uniqueness in keys.

#     Policy Document: '''{sample_data}'''
   
#      """
#     return prompt

def get_prompt_for_coverage_amount_extraction(data):
    prompt = f"""you are given a insurance data, in this data there are few coverages and their coverage amount is mentioned.

    data: {data}
    task: From the given data you have to find the coverage amount of these coverages only ["Trip Cancellation coverage", "Trip Interruption", "Medical Evacuation", "Emergency Medical", "Baggage Loss", "Flight Accident", "Accidental Death"]

    Instruction:
    - Read the data carefully then find coverage amount for only given coverages.
    - Please dont give the response before you complete the task.
    - Ensure that if coverage amount of any coverage is not given in this data then strictly, return 0 or null for that coverage.
    - Provide only the relevant information without adding any extra details.
    - Please ensure that coverage amount should be strictly in numbers only with '$' sign, no alphabets need to be included.


    return format:
    {{
        "Trip Cancellation coverage": "coverage amount",
        "Trip Interruption": "coverage amount",
        "Medical Evacuation": "coverage amount",
        "Emergency Medical": "coverage amount",
        "Baggage Loss": "coverage amount",
        "Flight Accident": "coverage amount",
        "Accidental Death": "coverage amount"
    }}

    """
    # prompt = f"""you are given a insurance data, in this data there are few coverages and their coverage amount is mentioned.

    # data: {data}

    # task: From the given data you have to find the coverage amount of these coverages only ["Trip Cancellation coverage", "Trip Interruption", "Medical Evacuation", "Emergency Medical", "Baggage Loss", "Flight Accident", "Accidental Death"]

    # Instruction:
    # - Read the data carefully then find coverage amount for only given coverages.
    # - Please dont give the response before you complete the task.
    # - Ensure that if coverage amount of any coverage is not given in this data then, return 0 or null for that coverage.
    # - Provide only the relevant information without adding any extra details.
    # - In output please add the numbers(amount) only.
    # - I need only the number after '$' sign in the coverage amount, nothing extra.


    # return format:
    # {{
    #     "Trip Cancellation coverage": "coverage amount",
    #     "Trip Interruption": "coverage amount",
    #     "Medical Evacuation": "coverage amount",
    #     "Emergency Medical": "coverage amount",
    #     "Baggage Loss": "coverage amount",
    #     "Flight Accident": "coverage amount",
    #     "Accidental Death": "coverage amount"
    # }}
    #  """
    return prompt

def get_coverage_amount_from_gpt(text:str):
    resp = {'error':None, 'result':None}
    try:
        prompt = get_prompt_for_coverage_amount_extraction(text)
        result = get_completion(prompt,'gpt-3.5-turbo')
        resp['result'] = json.loads(result)
    except Exception as e:
        resp['error'] = str(e)
    
    return resp

def get_coverage_amount_from_huggingface(text:str):
    resp = {'error':None, 'result':None}
    try:
        prompt = get_prompt_for_coverage_amount_extraction(text)
        result = get_completion_huggingface(prompt,'mistralai/Mistral-7B-Instruct-v0.2')
        resp['result'] = json.loads(result)
    except Exception as e:
        resp['error'] = str(e)
    
    return resp