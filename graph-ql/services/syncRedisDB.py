#from redis.commands.search.field import TextField, VectorField, NumericField
#from redis.commands.search.indexDefinition import IndexDefinition, IndexType
#from sentence_transformers import SentenceTransformer
#from openai.embeddings_utils import get_embedding
from services import similarity_service,redis_service
import re
#from tqdm import tqdm
import urllib.parse as urllp
import os

import numpy as np
from datetime import datetime
from datetime import date
import pandas as pd
#import redis
import json
import codecs
import sys
import requests
# import config.constant
# #sys.path.append('../')
from config.constant import (GRAPHDB_PASSWORD, GRAPHDB_SERVICE, GRAPHDB_USERNAME,DEFAULT_GRAPHDB_REPO)
#from config.constant import (HOST, GRAPHDB_PASSWORD, GRAPHDB_SERVICE, GRAPHDB_USERNAME,DEFAULT_GRAPHDB_REPO)

# if os.getcwd() not in sys.path:
#     sys.path.append(os.getcwd())


# ENV = "local"





def encodeURIComponent(s): return urllp.quote(
    s, safe='/', encoding=None, errors=None)


# def generate_urnique_id(redis_client):
#     keys = redis_client.keys("comp:*")
#     record_ids = [int((str(key).split(":")[1]).replace("'", ""))
#                   for key in keys]
#     last_record_id = max(record_ids) if record_ids else 0
#     next_record_id = last_record_id + 1
#    # print("Record Id Should be:", next_record_id)
#     return next_record_id


def login():
    results = {}
    
    GRAPHDB_LOGIN = GRAPHDB_SERVICE + '/rest/login'
    GRAPHDB_CONFIG_URL = GRAPHDB_SERVICE + '/rest/explore-graph/config'
    GRAPHDB_VISUAL_GRAPH = GRAPHDB_SERVICE + '/graphs-visualizations?query='
    obj = {
        "username": GRAPHDB_USERNAME,
        "password": GRAPHDB_PASSWORD
    }
    headers = {"Content-Type": "application/json",
               "Access-Control-Expose-Headers": "*"}
    try:
        response = requests.post(GRAPHDB_LOGIN, json=obj, headers=headers)
        if response.status_code == 200:
            results['token'] = response.headers['authorization']
        else:
            raise Exception("GraphDB unable to handle request!")
    except Exception as e:
        print(e)

    return results


def execute_sparql_query(params: dict):
    response = {'error': None, 'result': None}
    url = f"{GRAPHDB_SERVICE}/repositories/{params['repositoryID']}?query={params['query']}"
    headers = {
        'Authorization': params['token'],
        'Accept': 'application/sparql-results+json'
    }
    try:
        resp = requests.request("GET", url, headers=headers)
        if resp.status_code == 200:
            response['result'] = resp.json()
        else:
            response['error'] = "Data not found"
    except Exception as e:
        response['error'] = e
    return response

def get_all_data_from_parent_comp(comp_url: str):
    return f"""
PREFIX dbr1: <https://www.linkedin.com/company/>
PREFIX dbr4: <https://www.zoominfo.com/company/> 
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX node: <http://property.org/node/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
select distinct ?p (group_concat( distinct ?o;separator=",") as ?o1) where {{
     ?company a dbo:Organisation; 
              dbo:source ?source .
    ?source ?p ?o .     
     
    FILTER (?company IN (<{comp_url}>))
    FILTER (?p not in (rdf:type, rdfs:label, dbo:employer, dbo:source))
    FILTER (!strstarts(str(?p), str(node:)))
}} group by ?p
"""

def sparql_query_linkedin(comp_url: str):
    return f"""
PREFIX dbr1: <https://www.linkedin.com/company/>
PREFIX dbr4: <https://www.zoominfo.com/company/> 
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
select ?parent_name ?description ?headquarters ?industry ?founded ?numOf_emp where {{ 
     ?company a dbo:Organisation; 
           dbo:source ?data . 
     optional{{ ?data dbo:description ?description . }}
     optional{{ ?data dbo:headquarters ?headquarters . }}
     optional{{ ?data dbo:industry ?industry . }}
     optional{{ ?data foaf:founded ?founded . }}
     optional{{ ?data foaf:parent_name ?parent_name . }}
     optional{{ ?data dbo:no_of_employees ?numOf_emp . }}
     FILTER (?data IN (<{comp_url}>))
}} 
"""


def sparql_query_yf(comp_url: str):
    return f"""
PREFIX dbr1: <https://www.linkedin.com/company/>
PREFIX dbr4: <https://www.zoominfo.com/company/> 
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
select ?parent_name ?revenue_doller ?previous_year_revenue ?quarterly_growth where {{ 
     ?company a dbo:Organisation; 
           dbo:source ?data . 
     ?data foaf:current_year_revenue ?revenue_doller .
     ?data foaf:previous_year_revenue ?previous_year_revenue .
     optional {{ ?data foaf:quarterly_revenue_growth ?quarterly_growth. }}
     optional{{ ?data foaf:parent_name ?parent_name . }}
     FILTER (?data IN (<{comp_url}>))
}} 
"""


def sparql_query_zoominfo(comp_url: str):
    return f"""
PREFIX dbr1: <https://www.linkedin.com/company/>
PREFIX dbr4: <https://www.zoominfo.com/company/> 
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT (GROUP_CONCAT(DISTINCT ?SICstr; SEPARATOR=", ") AS ?SIC) (GROUP_CONCAT(DISTINCT ?NAICSstr; SEPARATOR=", ") AS ?NAICS) ?parent_name ?headquarters ?industry ?founded ?numOf_emp
WHERE {{
    ?company a dbo:Organisation; 
             dbo:source ?data . 
    ?data dbo:sic ?SIC ; 
         dbo:naics ?NAICS .
    OPTIONAL {{ ?data dbo:headquarters ?headquarters . }}
    OPTIONAL {{ ?data dbo:industry ?industry . }}
    OPTIONAL {{ ?data foaf:founded ?founded . }}
    optional{{ ?data foaf:parent_name ?parent_name . }}
    OPTIONAL {{ ?data dbo:no_of_employees ?numOf_emp . }}
    FILTER (?data In (<{comp_url}>) )
    
    BIND(IF(BOUND(?SIC), STR(?SIC), "") AS ?SICstr)
    BIND(IF(BOUND(?NAICS), STR(?NAICS), "") AS ?NAICSstr)
}}
GROUP BY ?parent_name ?headquarters ?industry ?founded ?numOf_emp
"""


def sparql_query_dbpedia(comp_url: str):
    return f"""
PREFIX dbr1: <https://www.linkedin.com/company/>
PREFIX dbr4: <https://www.zoominfo.com/company/> 
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
select ?name ?description (GROUP_CONCAT(DISTINCT ?industryStr; SEPARATOR=", ") AS ?industry) ?parent_name ?headquarters ?no_of_employees ?founded_date  
where {{ 
    ?company a dbo:Organisation; 
            dbo:source ?data . 
    ?data dbp:name ?name .
    optional{{ ?data dbo:description ?description . }}
    optional{{ ?data dbo:industry ?industry . }}
    optional{{ ?data dbo:headquarters ?headquarters . }}
    optional{{ ?data dbo:no_of_employees ?no_of_employees . }}
    optional{{ ?data foaf:founded ?founded_date . }}
    optional{{ ?data foaf:parent_name ?parent_name . }}
    FILTER (?data IN (<{comp_url}>))
    
    BIND(IF(BOUND(?industry), STR(?industry), "") AS ?industryStr)
}}
group by ?parent_name ?name ?description ?headquarters ?no_of_employees ?founded_date
"""


get_parent_Comp_query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    select distinct ?company where { 
    	?company a dbo:Organisation .  
    } 
    ORDER BY (?company)
"""

def get_lead_query(comp: str):
    return f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
	PREFIX dbOrg: <https://company.org/resource/>
	select distinct ?lead where {{ 
     	?company a dbo:Organisation; 
           	foaf:custom_lead ?lead .
    }} 
	values ?company {{<{comp}>}}
"""


def get_source_query(comp: str):
    return f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
	PREFIX dbOrg: <https://company.org/resource/>
	select distinct ?source where {{ 
     	?company a dbo:Organisation; 
           	dbo:source ?source .
    }} 
	values ?company {{<{comp}>}}
"""

# ==================== UTILITY FUNCTIONS ====================
def get_value(response, key):
    if response != [] :
        try:
            if response['result']['results']['bindings']!=[]:
                return response['result']['results']['bindings'][0][key]['value']
            else:
                return None
        except (KeyError, IndexError):
            return None
    else :
       return None

def remove_prefix_iri(s: str):
    s = s.replace("http://dbpedia.org/ontology/", "")
    s = s.replace("http://xmlns.com/foaf/0.1/", "")
    s = s.replace("http://dbpedia.org/property/", "")
    return s

# def get_dict(resp: dict):
#     res_dict = {}
#     if resp['result']['results']['bindings']:
#         for x in resp['result']['results']['bindings']:
#             res_dict[remove_prefix_iri(str(x['p']['value']))] = codecs.decode(x['o1']['value'], 'unicode_escape')
#       #  data = json.dumps(app_dict, indent=len(resp['result']['results']['bindings']))
#         return data
#     else:    
#         return ""

# ------------------- Get Parent Company Name / List Here -------------------

def insert_company_into_redis(com_url:list,isCrawl:bool):
    comp_list = []
    b=False
    graphdb_login_res = login()
    
    if com_url==[] and isCrawl==False:
        parent_resp = execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
             get_parent_Comp_query), "token": graphdb_login_res.get('token')})
        for binding in parent_resp["result"]["results"]["bindings"]:
            company_uri = binding["company"]["value"]
            comp_list.append(company_uri)
            
    else :
        b=isCrawl
        comp_list=com_url  
    
    responsefromRedis=gettingAllDatafromSources(comp_list,graphdb_login_res,b)
    return responsefromRedis



# =========== current year ===========



def get_year(d):
    year_pattern = r"^\d{4}$"
    year_month_pattern = r"^\d{4}-\d{2}$"
    month_year_pattern = r"^\d{2}-\d{4}$"

    # Check if the date string matches the year pattern
    if d == None:
        return None
    elif re.match(year_pattern, d):
        return d  # The date string contains only a year, return the year
    elif re.match(year_month_pattern, d):
        # The date string contains a year and month, return the year
        return d.split('-')[0]
    elif re.match(month_year_pattern, d):
        # The date string contains a month and year, return the year
        return d.split('-')[1] 
    else:
        # Attempt to extract the year from a full date string
        try:
            date_obj = datetime.datetime.strptime(d, "%Y-%m-%d")
            return date_obj.year
        except Exception as e:
            try:
                date_obj = datetime.datetime.strptime(d, "%d-%m-%Y")
                return date_obj.year
            except Exception as e:
                return None


# ------------------- Get Parent Company Name / List Here -------------------
def gettingAllDatafromSources(comp_list,graphdb_login_res,b):
    temp_list = []
    error_comp = []
    today = date.today()
    c_year = today.strftime("%Y")
#with tqdm(total=len(comp_list), desc=f'Featching Data From GraphDB...', unit='doc') as pbar:
    for comp in comp_list:
            if comp.replace("https://company.org/resource", "") != "/":
                try:
                    source_list: str
                    dbp_resp=[]
                    linkedin_resp=[]
                    yf_resp=[]
                    zoominfo_resp=[]
                    query = get_source_query(comp)
                    
                    source_resp = execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
                    query), "token": graphdb_login_res.get('token')})
                   
                # all_data_res = execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
                #     get_all_data_from_parent_comp(comp)), "token": graphdb_login_res.get('token')})
                    for binding in source_resp["result"]["results"]["bindings"]:
                        source_uri = binding["source"]["value"]
                        if 'https://www.zoominfo.com' in source_uri:
                            zoominfo_resp = execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
                                sparql_query_zoominfo(source_uri)), "token": graphdb_login_res.get('token')})
                        elif 'https://finance.yahoo.com' in source_uri:
                            yf_resp = execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
                                sparql_query_yf(source_uri)), "token": graphdb_login_res.get('token')})
                        elif 'https://www.linkedin.com' in source_uri:
                            linkedin_resp = execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
                                sparql_query_linkedin(source_uri)), "token": graphdb_login_res.get('token')})
                        else:
                            dbp_resp = execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
                                sparql_query_dbpedia(source_uri)), "token": graphdb_login_res.get('token')})

                    app_dict = {}
                    if b:
                        app_dict['name'] = get_value(dbp_resp, 'parent_name')  or get_value(linkedin_resp, 'parent_name') or get_value(zoominfo_resp, 'parent_name') or get_value(yf_resp, 'parent_name') or ""
                        app_dict['description'] = f"""{get_value(dbp_resp, 'description')}\n{get_value(linkedin_resp, 'description')}""" or "NA"
                        app_dict['industry'] = get_value(dbp_resp, 'industry') or get_value(linkedin_resp, 'industry') or get_value(zoominfo_resp, 'industry') or get_value(yf_resp, 'industry') or "NA"
                        app_dict['headquarters'] = get_value(linkedin_resp, 'headquarters') or get_value(dbp_resp, 'headquarters') or get_value(zoominfo_resp, 'headquarters') or "NA"
                        app_dict['no_of_employees'] = get_value(linkedin_resp, 'numOf_emp') or get_value(zoominfo_resp, 'numOf_emp') or get_value(dbp_resp, 'no_of_employees') or get_value(yf_resp, 'no_of_employees') or 0
                        founded_year = get_value(zoominfo_resp, 'founded') or get_value(linkedin_resp, "founded") or get_year(get_value(dbp_resp, "founded_date")) or 0
                        if founded_year==0:
                            app_dict['operating_years']=0
                        else :
                            app_dict['operating_years'] = int(c_year) - int(founded_year)
                        app_dict['revenue_dollar'] = get_value(yf_resp, 'revenue_doller') or 0
                        app_dict['quarterly_growth'] = round(float(get_value(yf_resp, 'quarterly_growth'))*100, 2) if get_value(yf_resp, 'quarterly_growth')!=None else  0.0
                        if get_value(yf_resp, 'revenue_doller')!=None and get_value(yf_resp, 'previous_year_revenue')!=None :
                            app_dict['annual_growth'] = round(((int(get_value(yf_resp, 'revenue_doller')) - int(get_value(yf_resp, 'previous_year_revenue'))) / int(get_value(yf_resp, 'previous_year_revenue')))*100, 2) or 0.0
                        else:
                            app_dict['annual_growth']=0.0
        
                        app_dict['SIC'] = get_value(zoominfo_resp, 'SIC')  or get_value(dbp_resp, 'SIC') or  get_value(linkedin_resp, 'SIC') or 0 
                        app_dict['NAICS'] = get_value(zoominfo_resp, 'NAICS') or get_value(dbp_resp, 'NAICS') or  get_value(linkedin_resp, 'NAICS') or 0
                        temp_var = app_dict
                        
                        app_dict['get_emb'] = str(temp_var)
                
                        temp_list.append(app_dict)
                    else:
                        app_dict['name'] = get_value(dbp_resp, 'name')
                        app_dict['description'] = f"""{get_value(dbp_resp, 'description')}\n{get_value(linkedin_resp, 'description')}"""
                        app_dict['industry'] = get_value(dbp_resp, 'industry') or get_value(linkedin_resp, 'industry') or get_value(zoominfo_resp, 'industry') 
                        app_dict['headquarters'] = get_value(linkedin_resp, 'headquarters') or get_value(dbp_resp, 'headquarters') or get_value(zoominfo_resp, 'headquarters')
                        app_dict['no_of_employees'] = get_value(linkedin_resp, 'numOf_emp') or get_value(zoominfo_resp, 'numOf_emp') or get_value(dbp_resp, 'no_of_employees')
                        founded_year = get_value(zoominfo_resp, 'founded') or get_value(linkedin_resp, "founded") or get_year(get_value(dbp_resp, "founded_date"))
                        app_dict['operating_years'] = int(c_year) - int(founded_year)
                        app_dict['revenue_dollar'] = get_value(yf_resp, 'revenue_doller')
                        app_dict['quarterly_growth'] = round(float(get_value(yf_resp, 'quarterly_growth'))*100, 2)
                        app_dict['annual_growth'] = round(((int(get_value(yf_resp, 'revenue_doller')) - int(get_value(yf_resp, 'previous_year_revenue'))) / int(get_value(yf_resp, 'previous_year_revenue')))*100, 2)
                        app_dict['SIC'] = get_value(zoominfo_resp, 'SIC')
                        app_dict['NAICS'] = get_value(zoominfo_resp, 'NAICS')
                        temp_var = app_dict
                        app_dict['get_emb'] = str(temp_var)
                
                        temp_list.append(app_dict)  

                    del zoominfo_resp, yf_resp, linkedin_resp, dbp_resp

                except Exception as e:
                    error_comp.append(f"{comp}:{e}")


    errorWrite(error_comp)
    Result=createDataFrame_and_insertion(temp_list,b)
    return Result


 #       pbar.update(1)

def errorWrite(error_comp):
    file_path = 'error_comp.txt'

    try:
        # Open the file
        with open(file_path, 'w') as file:
            # Write to the file
            for item in error_comp:
                try:
                    file.write(f'{item}\n')
                except Exception as e:
                    print(f"Error writing to file: {str(e)}")
                    # Handle the specific error writing case if needed

    except Exception as e:
        print(f"An error occurred while opening the file: {str(e)}")
    finally:
        # Ensure the file is closed, even if an exception occurred
        try:
            file.close()
        except Exception as e:
            print(f"Error closing the file: {str(e)}")
    


# ======================= GENERATING DATAFRAME FROM JSON DATA=======================
def createDataFrame_and_insertion(temp_list,b):
    df = pd.DataFrame(temp_list)
    df['huggingface_embedding'] = None
# df['openai_embedding'] = None
# df['lamma_embedding'] = None
#print("Dataframe / Dataset generated for the json data.")
#print(df)

# ======================= GENERATING HUGGING FACE EMBEDDING HERE FOR DATAFRAME =======================
# model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
# with tqdm(total=len(df), desc=f'Generating Embedding for Huggingface into Dataframe', unit='doc') as pbar:
#     for index, row in df.iterrows():
#         HuggingFace_embedding = model.encode(row['get_emb'])
#         df.at[index, 'huggingface_embedding'] = HuggingFace_embedding
#         pbar.update(1)
#     # df['huggingface_embedding'] = df['get_emb'].apply(
#     #     lambda x: model.encode(x))
# print("Huggging face embedding generated for the dataset.")

#============================GENERATING HUGGING FACE EMBEDDING HERE FOR DATAFRAME USING API==========
#with tqdm(total=len(df), desc=f'Generating Embedding for Huggingface into Dataframe', unit='doc') as pbar:
    for index, row in df.iterrows():
            HuggingFace_embedding = similarity_service.get_embedding(row['get_emb'],'HUGGINGFACE')
            df.at[index, 'huggingface_embedding'] = HuggingFace_embedding
#        pbar.update(1)
 #       df['huggingface_embedding'] = df['get_emb'].apply(
  #       lambda x: get_embedding(x,'HUGGINGFACE'))
#print("Huggging face embedding generated for the dataset.")
    response=[]
    if b :
        for index, row in df.iterrows():
            if row['name'] != "" :
                company_list= []
                company_list.append(row['name'])
                result=similarity_service.get_companies_list(company_list)
                if result['data'] == []:
                    response.append(redis_service.store(row.to_dict()))
                else :
                    for obj in result['data'] :
                        comp_id=obj['id']
                        response.append(redis_service.update(comp_id, row.to_dict()))
        return response


    else :
         response.append(redis_service.store(df))
         return response

    #redisRes=redis_client_platformData(df)
    #return redisRes
# ======================= GENERATING OPENAI EMBEDDING HERE FOR DATAFRAME =======================
# openai.api_key = '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'
# with tqdm(total=len(data), desc=f'Generating Embedding for OpenAi into Dataframe', unit='doc') as pbar:
#     for index, row in df.iterrows():
#         openai_embedding = get_embedding(
#             row['description'], engine='text-embedding-ada-002')
#         df.at[index, 'openai_embedding'] = openai_embedding
#         pbar.update(1)
#     # df['openai_embedding'] = df['description'].apply(
#     #     lambda x: get_embedding(x, engine='text-embedding-ada-002'))
# print("OpenAi embedding generated for the dataset.")

# ======================= GENERATING LAMMA GPT EMBEDDING HERE FOR DATAFRAME =======================

# def get_lamma_embedding(value: str):
#     data = {"model": GPT_LAMMA_MODEL_NAME, "input": value}
#     headers = {
#         "Authorization": f"Bearer {GPT_LAMMA_ACCESS_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     reponse = requests.post(
#         GPT_LAMMA_URL, data=json.dumps(data), headers=headers)
#     search_term_vector = reponse.json().get("data")[0].get("embedding")
#     return search_term_vector

# df['lamma_embedding'] = df['description'].apply(lambda x: get_lamma_embedding(x))
# print("Lamma gpt embedding generated for the dataset.")

# def redis_client_platformData(df):

#     redis_client = None

# # ======================= MAKING CONNECTION WITH LOCAL / SERVVER REDIS DB HERE =======================
#     if PLATFORM == 'server':
#         pool = redis.ConnectionPool(
#             host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0)
#         redis_client = redis.Redis(connection_pool=pool)
#         redis_client.ping


# # ======================= MAKING CONNECTION WITH REDIS CLOUD DB HERE =======================
#     elif PLATFORM == 'cloud':
#         redis_client = redis.Redis(
#             host=REDIS_HOST,
#             port=REDIS_PORT,
#             password=REDIS_PASSWORD)


# # OPENAI_VECTOR_DIM = len(df['openai_embedding'][0])  # length of the vectors
#     HUGGINGFACE_VECTOR_DIM = len(
#         df['huggingface_embedding'][0])                 # length of the vectors
# # LAMMA_VECTOR_DIM = len(df['lamma_embedding'][0])  # length of the vectors
#     VECTOR_NUMBER = len(df)                             # initial number of vectors
#     INDEX_NAME = "embedding-company-index"              # name of the search index
#     PREFIX = "comp"                                     # prefix for the document keys
#     DISTANCE_METRIC = "COSINE"


# # ======================= DEFINING REDISEARCH FIELDS FOR EACH OF THE COLUMNS IN THE DATASET HERE =======================
#     fields = [TextField(name="name"), TextField(name="description"), TextField(name="industry"), TextField(name="headquarters"), NumericField(name="revenue_dollar"), NumericField("no_of_employees"), NumericField("annual_growth"), NumericField("quarterly_growth"), NumericField("operating_years"), TextField("NAICS"), TextField("SIC"),
#           #   VectorField("openai_embedding", "HNSW", {"TYPE": "FLOAT32", "DIM": OPENAI_VECTOR_DIM,
#           #               "DISTANCE_METRIC": DISTANCE_METRIC, "INITIAL_CAP": VECTOR_NUMBER, "M": 40, "EF_CONSTRUCTION": 200}),
#           #   VectorField("lamma_embedding", "HNSW", {"TYPE": "FLOAT32", "DIM": LAMMA_VECTOR_DIM,
#           #               "DISTANCE_METRIC": DISTANCE_METRIC, "INITIAL_CAP": VECTOR_NUMBER, "M": 40, "EF_CONSTRUCTION": 200}),
#             VectorField("huggingface_embedding", "HNSW", {"TYPE": "FLOAT32", "DIM": HUGGINGFACE_VECTOR_DIM, "DISTANCE_METRIC": DISTANCE_METRIC, "M": 40, "EF_CONSTRUCTION": 200})]


# # ======================= GENERATING REDISEARCH INDEX HERE =======================

#     if PLATFORM == 'server':
#    # print('Running Init Script for Local/Server Redis DB ...')
#     # Check if index exists
#         try:
#             redis_client.ft(INDEX_NAME).info()
#       #  print("Index already exists")
#         except:
#         # Create RediSearch Index
#             redis_client.ft(INDEX_NAME).create_index(fields=fields, definition=IndexDefinition(
#                 prefix=[PREFIX], index_type=IndexType.HASH))

#         def index_documents(client: redis.Redis, prefix: str, documents: pd.DataFrame):
#             p = client.pipeline(transaction=False)
#             records = documents.to_dict(orient='index')
#             exist_id = generate_urnique_id(redis_client)
#      #   with tqdm(total=len(documents), desc=f'Ingesting Data into RedisDB', unit='doc') as pbar:
#             for idx in records.keys():
#                     company = records[idx]
#                     key = f"{prefix}:{str(exist_id + idx)}"
#                 # company["openai_embedding"] = np.array(
#                 #     company["openai_embedding"], dtype=np.float32).tobytes()
#                 # company["lamma_embedding"] = np.array(
#                 #     company["lamma_embedding"], dtype=np.float32).tobytes()
#                     company["huggingface_embedding"] = company["huggingface_embedding"].astype(
#                         np.float32).tobytes()
#                     p.hset(key, mapping=company)
#             #    pbar.update(1)
#                     p.execute()

#         index_documents(redis_client, PREFIX, df)
#         return "DATA INGESTED INTO REDIS SERVER / LOCAL DB"
#  #   print("================================== DATA INGESTED INTO REDIS SERVER / LOCAL DB =====================================")


#     elif PLATFORM == 'cloud':
#     #print('Running Init Script for Cloud Redis DB ...')
#     # Create RediSearch Index
#         redis_client.ft(INDEX_NAME).create_index(fields=fields, definition=IndexDefinition(
#             prefix=[PREFIX], index_type=IndexType.HASH))

#         p = redis_client.pipeline(transaction=False)
#         records = df.to_dict(orient='index')
#         exist_id = generate_urnique_id(redis_client)
#     #with tqdm(total=len(df), desc=f'Ingesting Data into RedisDB', unit='doc') as pbar:
#         for idx in records.keys():
#                 company = records[idx]
#                 key = f"{PREFIX}:{str(exist_id + idx)}"
#                 company["huggingface_embedding"] = company["huggingface_embedding"].astype(
#                     np.float32).tobytes()
#                 p.hset(key, mapping=company)
#         #    pbar.update(1)
#                 p.execute()
#         return "DATA INGESTED INTO REDIS CLOUD DB"
   # print("================================== DATA INGESTED INTO REDIS CLOUD DB =====================================")



#========================= function for get embedding=======================
#  
# def get_embedding(search_term, platform_type):
    
#  #   my_logger = get_logger("/getembedding")
    
#     list = []
#     list.append(search_term)
#     data = {"search_term": list, "type": platform_type}
#     headers = {
#         "Content-Type": "application/json"
#     }
#     vector_embedding_url = f'{EMBEDDING_ENDPOINT}/getembedding/'
#     #sending request to  vector embedding micro-service
#     try:
#         response = requests.get(vector_embedding_url, data = json.dumps(data), headers= headers)
#         if response.status_code==200 :
#             return response.json().get('data').get('term_0')
#         elif response.status_code==404 :
#             response = response.json()
#             raise Exception(response.get('error'))
#         else:
#            raise Exception('Similarity not found')      
#     except Exception as e:
#     #    my_logger.error(e)
#         raise Exception




