import re
import time
import openai
from utils.constant2 import ontology, sample_rdf_data, prefixes, claims_ontology

from settings.logging_config import logger
import openai
import os
import re
from openai import OpenAI
from dotenv import load_dotenv
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image, GenerationConfig, Content
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models

load_dotenv()
# openai.api_key = os.getenv("openai.api_key")
# api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("openai.api_key"))



#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/vector-embedding/zeniagraph-422017-12b451faeb6f.json"

# # Retrieve the value of the environment variable
var = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# # # Check if the environment variable is set and print its value
# if var:
#     print(f"The environment variable 'GOOGLE_APPLICATION_CREDENTIALS' is set to: {var}")
# else:
#     print(f"The environment variable 'GOOGLE_APPLICATION_CREDENTIALS' is not set.")
    

class Gemini:

    def __init__(self, streaming: bool = False):

        safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        # Load the model
        self.model = GenerativeModel("gemini-1.5-pro-preview-0409")
        self.streaming = streaming

        # Generation config
        self.config = GenerationConfig(
            temperature=0.01,
            top_p=0.8,
            top_k=32,
            candidate_count=1,
            max_output_tokens=4096,
        )

        # Safety config
        self.safety_config =safety_settings


    def invoke(self, prompt: str):

        # Format the user input as a Content object
        user_input = Content(
            role="user",
            parts=[
                Part.from_text(prompt),
            ]
        )

        response = self.model.generate_content(
            contents=user_input,
            generation_config=self.config,
            safety_settings=self.safety_config,
            stream=self.streaming,
            tools=[]
        )

        return response
    
def get_completion_gemini(prompt, model="gemini-1.5-pro-preview-0409"):
    response={'error':None, 'data':None}
    try:
        PROJECT_ID = "zeniagraph-422017"
        REGION = "us-east4"
        vertexai.init(project=PROJECT_ID, location=REGION)
        
        model = Gemini(streaming=False)
        resp = model.invoke(prompt)
        # print(resp)
        # print(resp.text)
        if resp != "" and resp != None:
            response['data']=resp.text
        else:
            response['error']="Data not found"
    except Exception as e:
        response['error']=e
        logger.exception(e)

    return response

def get_completion(prompt, model="gpt-3.5-turbo"):
    response={'error':None, 'data':None}
    messages = [{"role": "user", "content": prompt}]
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0, 
        )
        
        if resp != "" and resp != None:
            response['data']=resp.choices[0].message.content.strip()
        else:
            response['error']="Data not found"
    except Exception as e:
        response['error']=e
        logger.exception(e)

    return response

def update_prefix(sparql_query):
    #Adding all the prefixes
    prefix_index = sparql_query.find("SELECT")  # index of the SELECT keyword
    query_part = sparql_query[prefix_index:]  # SELECT query part
    sparql_query = prefixes + query_part

    listofPredicatesWithTheRightPrefix=["dbo:industry","dbp:name","dbo:source","foaf:Specialities","foaf:ticker","dbo:description","dbo:no_of_employees","dbo:headquarters","dbo:company_type","foaf:founded","foaf:social_url","foaf:total_assets","foaf:gross_profit","foaf:website","foaf:market_cap","foaf:last_quarterly_revenue","foaf:second_last_quarterly_revenue","dbo:sic","dbo:naics","foaf:quarterly_revenue_growth","foaf:long_business_summary","foaf:parent_name","foaf:company_type","foaf:revenue","foaf:social_followers","foaf:company_size","foaf:current_year_revenue","foaf:previous_year_revenue","foaf:profile_url","foaf:ticker-symbol"]

    where_clause = re.search(r'WHERE\s*\{(.+?)\}', sparql_query, re.DOTALL)
    if where_clause:
        where_text = where_clause.group(1)
        predicates_with_prefixes = re.findall(r'(\S+:\S+)\s+', where_text)


        for predicate in predicates_with_prefixes:
            matching_indices = [index for index, s in enumerate(listofPredicatesWithTheRightPrefix) if predicate.split(":")[1] in s]
            if matching_indices != []:
                sparql_query=sparql_query.replace(predicate,listofPredicatesWithTheRightPrefix[matching_indices[0]])

    if "?company" in sparql_query:
        sparql_query = sparql_query.replace("WHERE {","WHERE {\n?company dbo:source ?source.")
        if "?company dbo:source ?source." in sparql_query:
            sparql_query = sparql_query.replace("SELECT ","SELECT ?source ")

    return sparql_query

def extract_sparql_query(text):
    pattern = r"```sparql\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)
    #match = match.replace('\n', '')
    if match:
        query = match.group(1).strip()
        query_without_newlines = query.replace('\n', ' ')
        return query_without_newlines
    else:
        return None

def get_gpt_prompt(task):
    gptPrompt=f"""You are given an ontology and a sample_rdf_data followed by the ontology delimited with triple backticks.

    Task : '''{task}'''

    Note : Output should be the sparql query only no explanation needed.

    Instruction :
    Please ensure that the queries are logically correct and syntactically valid SPARQL queries.
    Please ensure that the prefixes are same in the sparql query as ontology.
    If you have to find the company name then use the parent_name predicate, company names are stored in the parent_name predicate.



    sample_rdf_datt : '''{sample_rdf_data}'''
    ontology : '''{ontology}'''
    """
    return gptPrompt


def get_sparql_query(input):
    response={'error':None, 'sparql_query':None}
    if input != "" and input != None:
        input = "write me a SPARQL query to " + input
        promptForGpt = get_gpt_prompt(input)
        #res=get_completion(promptForGpt)
        res=get_completion_gemini(promptForGpt)
        if res['error'] == None:
            #query = res['data']
            query = extract_sparql_query(res['data'])
            #query=update_prefix(res['data'])
            if "SELECT" in query or "select" in query:
               response['sparql_query']=query
            else:
                response['error'] = "Invalid Sparql Query"
        else:
            response['error']=res['error']
    else:
        response['error']="No input found"
    return response

def get_gpt_prompt_for_claim_data(task):
    gptPrompt=f"""You are given an ontology  followed by the ontology delimited with triple backticks.

    Task : '''{task}'''

    Note : Output should be the sparql query only no explanation needed.

    Instruction :
    Please ensure that the queries are logically correct and syntactically valid SPARQL queries.
    Start each value in clauses with capital letter like Pending.
    Whenever you use person name in clause then dont include space in between.
    Please ensure that the prefixes are same in the sparql query as ontology.
    Please read the ontology very carefully as it will give you the more details about the data and its structure.
    You need to write generic query according to the structure which satisfy the desired task.


    ontology : '''{claims_ontology}'''
    """
    return gptPrompt

def get_sparql_query_for_claim(input):
    response={'error':None, 'sparql_query':None}
    if input != "" and input != None:
        input = "write me a SPARQL query to " + input
        promptForGpt = get_gpt_prompt_for_claim_data(input)
        #res=get_completion(promptForGpt)
        res=get_completion_gemini(promptForGpt)
        if res['error'] == None:
            query=res['data']
            if "SELECT" in query or "select" in query:
               response['sparql_query']=query
            else:
                response['error'] = "Invalid Sparql Query"
        else:
            response['error']=res['error']
    else:
        response['error']="No input found"
    return response

