from fastapi import FastAPI, HTTPException
from config.log_config import get_logger
from config.constant import GRAPHDB_LOGIN, GRAPHDB_USERNAME, GRAPHDB_PASSWORD, GRAPHDB_CONFIG_URL, GRAPHDB_SERVICE, DEFAULT_GRAPHDB_REPO, GRAPHDB_VISUAL_GRAPH
from config.util import clean_name, cleanStringAndEncode, encodeURIComponent, get_proper_urls, decodeComponent, removeNonEnglishWords, split_full_name, clean_description, personalize_company_name, clean_string, clean_string_v2
import requests
import json
from ariadne import QueryType
from typing import List
from pydantic import BaseModel
from datetime import datetime
import re

class configPayload(BaseModel):
    token: str
    configId:str
    query:str
    repositioryId: str

class configListPayload(BaseModel):
    token: str
    repositioryId: str

class RdfStatement(BaseModel):
    repositoryID: str
    rdfData: str
    token: str

class JavaGraphDB(BaseModel):
    data: list
    

def login():
    my_logger = get_logger("/graphdb_login")
    results = {}
    obj  = {
        "username": GRAPHDB_USERNAME,
        "password": GRAPHDB_PASSWORD        
    }    
    headers = {"Content-Type": "application/json", "Access-Control-Expose-Headers":"*"}
    try:
        response =  requests.post(GRAPHDB_LOGIN, json = obj, headers = headers)
        if response.status_code==200 :
            results['token'] = response.headers['authorization']
        else:
            raise Exception("GraphDB unable to handle request!")             
    except Exception as e:
        my_logger.error(e)
        raise Exception(e)      
    
    return results

def create_config(params: configPayload):
    my_logger = get_logger("/create_config")
    results = {}
    obj  = {
        "name" : params['configId'],
        "startGraphQuery" : params['query'],
        "startMode" : "query",
        "startQueryIncludeInferred": True,
        "startQuerySameAs" : True     
    }    
    headers = {
        "Content-Type": "application/json", 
        "Access-Control-Expose-Headers":"*",
        "Authorization": params['token'],
        "Accept": "application/json",
        "X-Graphdb-Repository": params['repositioryId']
    }
    try:
        response =  requests.post(GRAPHDB_CONFIG_URL, json = obj, headers = headers)
        if response.status_code==200 :
           results['success'] = True
        else:
            raise Exception("Unable to create config path in graphdb!")             
    except Exception as e:
        my_logger.error(e)
        raise Exception(e)      
    
    return results

def get_config_list(params: configListPayload):
    my_logger = get_logger("/create_config")
    results = {}
    headers = {
        "Authorization": params['token'],
        "Access-Control-Expose-Headers":"*",
        "X-Graphdb-Repository": params['repositioryId']
    }
    try:
        response =  requests.get(GRAPHDB_CONFIG_URL, headers = headers)
        if response.status_code==200 :
           results = response.json()
        else:
            raise Exception("Unable to create config path in graphdb!")             
    except Exception as e:
        my_logger.error(e)
        raise Exception(e)      
    
    return results

def add_rdf_statement(params: RdfStatement):
    my_logger = get_logger("/add_statement_to_default_graph")
    results = {}
    obj  = {
        "repositoryID" : params['repositoryID'],
        "rdfData" : params['rdfData']
    }    
    headers = {
        "Content-Type": "text/turtle", 
        "Access-Control-Expose-Headers":"*",
        "Authorization": params['token'],
        "Accept": "application/json"
    }
         
    try:
        response =  requests.post(f'''{GRAPHDB_SERVICE}/repositories/{params['repositoryID']}/rdf-graphs/service?default''', data = params['rdfData'], headers = headers)
        #my_logger.info('graphdb response')
        #my_logger.info(response)
        if response.status_code==200 or response.status_code==204 :
           results['success'] = True
        else:
           results['error'] = "Unable to add statements in graphdb!"
                 
    except Exception as e:
        my_logger.error(e)
        results['error'] = e
    
    return results

def update_rdf_statement(params: RdfStatement):
    my_logger = get_logger("/update_statement_to_default_graph")
    results = {"success":False,"error":""}
    obj  = {
        "repositoryID" : params['repositoryID'],
        "update" : params['rdfData']
    } 
   
    headers = {
        "Content-Type": "application/x-www-form-urlencoded", 
        "Access-Control-Expose-Headers":"*",
        "Authorization": params['token']
    }         
    try:
        response =  requests.post(f'''{GRAPHDB_SERVICE}/repositories/{params['repositoryID']}/statements''', data = obj, headers = headers)
        if response.status_code==200 or response.status_code==204 :
           results['success'] = True
        else:
           results['error'] = "Unable to update statements in graphdb!"                 
    except Exception as e:
        my_logger.error(e)
        results['error'] = e
    
    return results

def delete_record(params: dict):
    my_logger = get_logger("/delete_record")
    results = {}
   
    headers = {
        "Content-Type": "application/rdf+xml", 
        "Access-Control-Expose-Headers":"*",
        "Authorization": params['token'],
        "Accept": "application/json"
    }

    url = f'''{GRAPHDB_SERVICE}/repositories/{params['repositoryID']}/statements?update={params.get('query')}'''

    try:
        response =  requests.post(url, headers = headers)
        if response.status_code==200 or response.status_code==204 :
           results['success'] = True
        else:
           results['error'] = "Unable to delete record"
    except Exception as e:
        results['error'] = e
    
    return results 


# get company details from graphdb
# params is a dictionary type 
# return type is json
def run_query(params:dict):
    my_logger = get_logger("/run_query")
    results = {}    
    headers = {
        "Content-Type": "text/turtle", 
        "Access-Control-Expose-Headers":"*",
        "Authorization": params['token'],
        "Accept": "application/json"
    }

    try:
        response =  requests.get(
            f'''{GRAPHDB_SERVICE}/repositories/{params['repositoryID']}?query={params['query']}''',
             headers = headers
             )
       
        if response.status_code==200 :
           results = response.json()
        else:
            raise Exception("Unable to run query from graphdb!")             
    except Exception as e:
        my_logger.error(e)
        raise Exception(e) 
    
    return results

def execute_sparql_query(params :dict):
    response={'error':None, 'result':None}
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

#get custom properties of a company
def get_custom_properties(params : dict) :
    response={'error':None, 'result':None} 

    query = f'''
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dbp: <http://dbpedia.org/property/>
        SELECT ?ps ?os where {{ 
            ?company a dbo:Organisation ;
                    dbo:source ?data .
            ?data foaf:custom_properties ?customProperties . 
            ?customProperties ?p ?o .
            BIND(REPLACE(str(?p), "http://xmlns.com/foaf/0.1/", "") AS ?ps)
            BIND(REPLACE(str(?o), "http://property.org/resource/", "") AS ?os)
            FILTER (?data IN (<{get_proper_urls(params['source'], params['name'])}>))
            FILTER (?ps NOT IN  ("http://www.w3.org/1999/02/22-rdf-syntax-ns#type","http://www.w3.org/2000/01/rdf-schema#label"))
        }}
    '''
    query = encodeURIComponent(query)
    queryResult = execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':params['token']});
    
    if queryResult['result'] != None:
        arr = []
        for item in queryResult['result']['results']['bindings']:
            arr.append({"name":item['ps']['value'],"value":decodeComponent(item['os']['value'])})    
        
        response['result'] = arr
    else:
        response['error'] = queryResult['error']  

    return response

#get custom properties of a company
def get_company_contacts(params : dict) :
    response={'error':None, 'result':None} 

    query = f'''
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
        select DISTINCT ?name ?occupation ?social_url ?description ?source  where {{ 
            ?company a dbo:Organisation ;
                    dbo:source ?data .
            ?data dbo:source ?source .
            ?data dbo:employer ?employee .
            ?employee rdfs:label ?name .
            OPTIONAL {{
                ?employee dbo:role ?role .        	 
                ?role rdfs:label ?occupation .
            }}
            OPTIONAL {{ 
                ?employee vcard:social_url ?social_url .
            }}	
            OPTIONAL {{ 
                ?employee dbo:description ?description . 
            }}
            OPTIONAL {{ 
                ?employee vcard:occupation ?data1 . 
                ?data1 rdfs:label ?occupation .
            }}

            FILTER (?data IN (<{get_proper_urls(params['source'], params['name'])}>))
        }}
    '''
    query = encodeURIComponent(query)
    queryResult = execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':params['token']});
    
    if queryResult['result'] != None:
        records = [];
        if len(queryResult['result']['results']['bindings']) > 0:
            for item in queryResult['result']['results']['bindings']:
                first_name, last_name = split_full_name(item['name']['value'])                
                records.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "occupation": item['occupation']['value'] if "occupation" in item else  "",
                    "social_url": item['social_url']['value'] if "social_url" in item else "",
                    "description": item['description']['value'] if "description" in item else "",
                    "source": item['source']['value']
                })
            response['result'] = records;             
        
    else:
        response['error'] = queryResult['error']  

    return response


def fetch_company_info(params : dict):
    response={'error':None, 'result':None} 
    login_response = login()
    query = f'''
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dbp: <http://dbpedia.org/property/>
        SELECT ?name ?parent_name ?industry ?source ?description ?no_of_employees ?headquarters ?company_type ?social_url (group_concat(?specialities; separator  = ",") as ?specialities)  
        WHERE {{ 
            ?company a dbo:Organisation ;
                    dbo:source ?data .
            ?data foaf:parent_name ?parent_name ;
                dbp:name ?name ;
                OPTIONAL {{ ?data dbo:industry ?industry . }}
                OPTIONAL {{ ?data dbo:source ?source . }}
                OPTIONAL {{ ?data dbo:description ?description .}}
                OPTIONAL {{ ?data dbo:no_of_employees  ?no_of_employees .}}
                OPTIONAL {{ ?data dbo:headquarters ?headquarters . }}
                OPTIONAL {{ ?data dbo:company_type ?company_type .}}
                OPTIONAL {{ ?data foaf:social_url ?social_url .}}
            
            OPTIONAL {{ ?data foaf:Specialities ?specialities . }} 	
            FILTER (?data IN (<{get_proper_urls(params['source'], params['name'])}>))
        }}
        GROUP BY ?name ?parent_name ?industry ?source ?description ?no_of_employees ?headquarters ?company_type ?social_url
    '''
    
    query = encodeURIComponent(query)    
    
    mainQueryResponse = execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':login_response.get('token')});

    if mainQueryResponse['result'] != None:
        mainResult = mainQueryResponse['result']['results']['bindings']
        
        if len(mainResult) > 0:
  
            records = {};
            for item in mainResult:
                for index, val in item.items():
                    records[index] = val.get('value')
                
            response['result'] = records

            #run another query to get all custom properties
            getProperties = get_custom_properties(
                {
                    "repositoryID" : params['repositoryID'], 
                    'token' : login_response.get('token'),
                    'name' : params['name'],
                    "source" : params['source']
                })    
            if getProperties['result'] != None:
                response['result']['custom_property'] = getProperties['result']
            else:
                response['result']['custom_property'] = []
            
            #run another query to get all contact of this company
            getContacts = get_company_contacts(
                {
                    "repositoryID" : params['repositoryID'], 
                    'token' : login_response.get('token'),
                    'name' : params['name'],
                    "source" : params['source']
                })    
            if getContacts['result'] != None:
                response['result']['employer'] = getContacts['result']
            else:
                response['result']['employer'] = []

    else:
        response['error'] = mainQueryResponse['error']   

    return response


def checkparentofcompany(name):
    print(name)
    response={'error':None, 'result':None} 
    
    loginResponse=login()
    query=f'''
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX dbp: <http://dbpedia.org/property/>

    SELECT ?parent ?parent_name WHERE {{ 
        ?s a dbo:Company;
        foaf:parent_name ?pname;
        dbp:name "{name}".
        ?parent dbo:source ?s ;
                rdfs:label ?parent_name .
    }}
    '''
    query = encodeURIComponent(query)
    queryResult = execute_sparql_query({"repositoryID":DEFAULT_GRAPHDB_REPO,'query':query,'token':loginResponse['token']})
  
    if 'result' in queryResult and 'results' in queryResult['result'] and 'bindings' in queryResult['result']['results']:
        bindings = queryResult['result']['results']['bindings']
        if bindings:
            parent_info = bindings[0]
            parent = parent_info['parent']['value']
            parent_name = parent_info['parent_name']['value']
            response['result'] = {'parent': parent, 'parent_name': parent_name}
            print(response["result"])
        else:
            response['error'] = queryResult['error'] 
   
    return response

def addcustomproperty(params:dict,uri:str):
    custom_data=''
    if params['source']== 'yahoo_finance':  
        custom_uri =f'''http://property.org/resource/{encodeURIComponent(params['name'])}_Finance_Properties'''
            
    if params['source']== 'linkedin':
        custom_uri =f'''http://property.org/resource/{encodeURIComponent(params['name'])}_LinkedIn_Properties'''
    
    if params['source']== 'dbpedia':
        custom_uri =f'''http://property.org/resource/{encodeURIComponent(params['name'])}_DBPedia_Properties'''

    if params['source']== 'others':
        custom_uri =f'''http://others.org/resource/{encodeURIComponent(params['name'])}_Others_Properties'''    
     
    custom_data += f'''<{custom_uri}> a dbo:CustomProperty ; rdfs:label "Properties".'''

    for custom_prop in params["custom_properties"]:
                name = custom_prop["name"].replace(' ','_')
                value = custom_prop["value"]
                custom_data += f'''<{uri}> foaf:custom_properties  <{custom_uri}> .'''
                value = clean_description(removeNonEnglishWords(value))
                if value!="" and not value.isspace():
                    print("value:",value)
                    
                    custom_data += f''' <{custom_uri}> foaf:{cleanStringAndEncode(name)} <http://property.org/resource/{encodeURIComponent(value)}>.
                <http://property.org/resource/{encodeURIComponent(value)}> rdfs:label "{value}" .
                foaf:{cleanStringAndEncode(name)} rdfs:label "{name}" .
                '''
    return custom_data

def addEmployeeData(params:dict,uri:str):
    emp_data=''
    employee= params['employer']
    print(employee)
    print(len(employee))
    if employee!=[]:       
            emp_data=f'''<{uri}> dbo:employees <{uri}_Employments>.
                 <{uri}_Employments> rdfs:label "Employments"; a dbo:Employment.
                     '''
            for employer in params["employer"]:               

                if 'full_name' in employer:
                    full_name= employer["full_name"]
                    name_parts = full_name.split()
                    prefixes = ["Mr.", "Mrs.", "Ms."]
                    if name_parts[0] in prefixes:
                        first_name = name_parts[0]+name_parts[1]
                        last_name = " ".join(name_parts[2:])
                    else:
                        first_name = name_parts[0]
                        last_name = " ".join(name_parts[1:])
                if 'first_name' in employer and 'last_name' in employer:
                    first_name= employer["first_name"]
                    last_name= employer["last_name"]
                    full_name= employer["first_name"]+employer["last_name"]


                emp_url=''  

                if 'social_url' in employer and employer["social_url"] !='':
                    emp_url=employer["social_url"]
                else:
                    emp_url=f'''https://property.org/resource/{encodeURIComponent(full_name)}''' 
                    emp_data+=f'''<{emp_url}> rdfs:label "{full_name}". '''

           
                emp_data+=f'''<{emp_url}> foaf:first_name "{first_name}". '''
                emp_data+=f'''<{emp_url}> foaf:last_name "{last_name}". '''            

                emp_data+=f'''<{uri}_Employments> dbo:employee <{emp_url}> .  '''
                emp_data+=f'''<{emp_url}> a vcard:Individual. '''
                
               

                if 'description' in employer and employer["description"]!='':
                    emp_data+=f'''<{emp_url}> dbo:description "{clean_description(employer["description"])} ". '''

                if 'start_month' in employer:
                    emp_data+=f'''<{emp_url}> vcard:start_month "{employer['start_month']} ". '''
                if 'start_year' in employer :
                    emp_data+=f'''<{emp_url}> vcard:start_year "{employer['start_year']} ". '''
                if 'end_month' in employer :
                    emp_data+=f'''<{emp_url}> vcard:end_month "{employer['end_month']} ". '''
                if 'end_year' in employer :
                    emp_data+=f'''<{emp_url}> vcard:end_year "{employer['end_year']} ". '''   
                if 'duration' in employer :
                    emp_data+=f'''<{emp_url}> vcard:duration "{employer['duration']} ". '''  
                if 'date_range' in employer :
                    emp_data+=f'''<{emp_url}> vcard:date_range "{employer['date_range']} ". '''  
                if 'employee_role_description' in employer :
                    emp_data+=f'''<{emp_url}> vcard:employee_role_description "{employer['employee_role_description']} ". ''' 
                if 'is_current' in employer :
                    emp_data+=f'''<{emp_url}> vcard:is_current "{employer['is_current']} ". ''' 

                if 'skills' in employer and employer['skills']!='':
                    for skill in employer['skills']:
                        emp_data += f"""<{emp_url}> vcard:skills "{skill}" . """ 

                if 'languages' in employer and employer['languages']!='' :
                    for language in employer['languages']:
                        emp_data += f"""<{emp_url}> vcard:languages "{language}" ."""
                if 'location' in employer and employer['location']!='':
                    for location in employer['location']:
                        emp_data += f"""<{emp_url}> vcard:location "{location}" ."""                                                                                                                                       



                if 'occupation' in employer and employer["occupation"]!='':
                    emp_data+=f'''<{emp_url}> vcard:experiences <{emp_url}_Experiences>.'''
                    experience_label = f"""<{emp_url}_Experiences> rdfs:label "Experiences"."""
                    emp_data += experience_label

                    experience_details = f"""<{emp_url}_Experiences> vcard:experience_details <{emp_url}-{uri}-Experinecedetails>.
                                           <{emp_url}-{uri}-Experinecedetails> a vcard:ExperienceDetails ; rdfs:label "{full_name}-{params["name"]}-Experinecedetails"; dbo:role "{employer["occupation"]}" . 
                                            <{emp_url}-{uri}-Experinecedetails> vcard:worked_in <{uri}_WorkExperience> .
                                            <{uri}_WorkExperience> rdfs:label "WorkExperience" .
                                            <{uri}_WorkExperience> vcard:work_in_company <{uri}> . 
                                            """  
                    emp_data += experience_details

    print(emp_data)
    return emp_data


def insertCrwaledDataintoGraphDB(params):
#     params={
#     "ticker_symbol": "APqwC.F",
#     "parent_name": "APC.F",
#     "name": "AInc.",
#     "source": "yahoo_finance",
#     "industry": "Consumer Electronics",
#     "gross_profit": "169148000000.0",
#     "market_cap": "2606647738368",
#     "total_assets": "352583000000.0",
#     "quarterly_revenue_growth": "-0.043",
#     "no_of_employees": "",
#     "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts. In addition, the company offers various services, such as Apple Arcade, a game subscription service; Apple Fitness+, a personalized fitness service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was founded in 1976 and is headquartered in Cupertino, California.",
#     "website": "https://www.apple.com",
#     "current_year_revenue": "383285000000.0",
#     "previous_year_revenue": "394328000000.0",
#     "custom_properties": [{"name":"Company_name", "value":"Apple"},{"name":"founder", "value":"Steve Jobs"},{"name":"CEO", "value":""}],
#     "last_quarterly_revenue": "90753000000.0",
#     "second_last_quarterly_revenue": "119575000000.0",
#     "employer": [
#         {
#             "first_name": "Mr.",
#             "last_name": "Timothy D. Cook",
#             "occupation": "CEO & Director",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Mr.",
#             "last_name": "Luca  Maestri",
#             "occupation": "CFO & Senior VP",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Mr.",
#             "last_name": "Jeffrey E. Williams",
#             "occupation": "Chief Operating Officer",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Ms.",
#             "last_name": "Katherine L. Adams",
#             "occupation": "Senior VP, General Counsel & Secretary",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Ms.",
#             "last_name": "Deirdre  O'Brien",
#             "occupation": "Senior Vice President of Retail",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Mr.",
#             "last_name": "Chris  Kondo",
#             "occupation": "Senior Director of Corporate Accounting",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Mr.",
#             "last_name": "James  Wilson",
#             "occupation": "Chief Technology Officer",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Suhasini",
#             "last_name": "Chandramouli",
#             "occupation": "Director of Investor Relations",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Mr.",
#             "last_name": "Greg  Joswiak",
#             "occupation": "Senior Vice President of Worldwide Marketing",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         },
#         {
#             "first_name": "Mr.",
#             "last_name": "Adrian  Perica",
#             "occupation": "Head of Corporate Development",
#             "social_url": "",
#             "description": "",
#             "source": "yahoo_finance"
#         }
#     ],
#     "exchange": "FRsdfA"
# }
  
#     params={
#     "custom_properties": [
#         {
#             "name": "CEO",
#             "value": "Keshav sharma"
#         }
#     ],
#     "name": "metacube",
#     "parent_name": "metacube",
#     "industry": "IT",
#     "headquarters": "Jaipur",
#     "revenue_dollar": "1000000000",
#     "quarterly_growth": "30",
#     "annual_growth": "40",
#     "no_of_employees": "123456",
#     "source": "others",
#     "operating_years": "20",
#     "SIC": "87686",
#     "NAICS": "78687",
#     "description": "Metacube software PVT LTD",
#     "manual": "Yes"
# }


    print("params: ",params)
    loginResponse = login()
    response  = {}
    if "token" in loginResponse:
        rdfs_data = f'''
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix dbp: <http://dbpedia.org/property/> .
        @prefix dbo: <http://dbpedia.org/ontology/> .
        @prefix com: <https://company.org/resource/> .
        @prefix dbr1: <https://www.linkedin.com/company/> .
        @prefix dbr2: <https://dbpedia.org/resource/> .
        @prefix dbr3: <https://www.salesforce.com/company/> .
        @prefix dbr4: <https://www.zoominfo.com/company/> .
        @prefix other: <https://www.othersource.com/company/> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix pro: <http://property.org/resource/> .
        @prefix node: <http://property.org/node/>.
        @prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
        @prefix yahoo: <https://finance.yahoo.com/quote/> .

        '''
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        print(params["source"])
        if params['source']== 'yahoo_finance':
            uri =f'''https://finance.yahoo.com/quote/{params['ticker_symbol']}'''
            rdfs_data +=f'''<{uri}>  rdfs:label "{params['name']}_Finance". '''
            rdfs_data +=f'''<{uri}>  dbp:name "{params['name']}". '''

        if params['source']== 'linkedin':
            if 'social_url' in params and params['social_url']!="":
                uri =f'''{params['social_url']}'''
            else:
                 uri =f'''https://www.linkedin.com/company/{encodeURIComponent(params['name'].lower().replace(" ","-").replace(".","-"))}'''    

            rdfs_data +=f'''<{uri}>  rdfs:label "{params['name']}_LinkedIn". '''
            rdfs_data +=f'''<{uri}>  dbp:name "{params['name']}". '''

        
        if params['source']== 'dbpedia':
            uri =f'''https://dbpedia.org/resource/{encodeURIComponent(params['name'].replace(' ', '_'))}'''
            rdfs_data +=f'''<{uri}>  rdfs:label "{params['name']}_DBPedia". '''
            rdfs_data +=f'''<{uri}>  dbp:name "{params['name']}". '''  

        if params['source']== 'others':
            uri =f'''https://www.othersource.com/company/{encodeURIComponent(params['name'])}'''
            rdfs_data +=f'''<{uri}>  rdfs:label "{params['name']}_Others". '''
            rdfs_data +=f'''<{uri}>  dbp:name "{params['name']}". '''     

            
        rdfs_data +=f''' <{uri}> a dbo:Company;
                                dbo:source "{params['source']}";
                                node:timestamp <https://property.org/resource/{encodeURIComponent(formatted_time)}> .
                       <https://property.org/resource/{encodeURIComponent(formatted_time)}> rdfs:label "{formatted_time}" . '''
        
        if 'manual' in params and params['manual']!="":
            rdfs_data +=f'''<{uri}> foaf:manual <http://property.org/resource/{params['manual']}>.'''
        else:
            rdfs_data +=f'''<{uri}> foaf:manual <http://property.org/resource/No>.'''



        parent_info = checkparentofcompany(params['name'])
        if parent_info['error'] is None:
            if parent_info['result'] is not None:
                parent = parent_info['result']['parent']
                parent_name = parent_info['result']['parent_name']
                rdfs_data +=f'''<{uri}> foaf:parent_name "{parent_name}".
                                <{parent}> dbo:source <{uri}>.'''
            else:
                rdfs_data +=f'''<{uri}> foaf:parent_name "{params['parent_name']}".
            <https://company.org/resource/{encodeURIComponent(params['parent_name'])}> dbo:source <{uri}> ; a dbo:Organisation ; rdfs:label "{params['parent_name']}" .'''


        if 'description' in params and params['description']!='':
            rdfs_data +=f'''<{uri}> dbo:description "{clean_description(params['description'])}".'''

        if 'no_of_employees' in params and params['no_of_employees']!="":
            rdfs_data +=f'''<{uri}> dbo:no_of_employees "{params['no_of_employees']}"^^xsd:integer;
                                    node:no_of_employees <http://property.org/resource/{params['no_of_employees']}> .'''
        
         
            
        if 'headquarters' in params and params['headquarters']!="":
            rdfs_data +=f'''<{uri}> dbo:headquarters "{params['headquarters']}";
                                    node:headquarters  <http://property.org/resource/{encodeURIComponent(params['headquarters'])}>.
                                    <http://property.org/resource/{encodeURIComponent(params['headquarters'])}> rdfs:label "{params['headquarters']}" .'''
        if 'founded' in params and params['founded']!="":
            rdfs_data +=f'''<{uri}> dbo:founded "{params['founded']}";
                                    node:founded  <http://property.org/resource/{encodeURIComponent(params['founded'])}>.
                                    <http://property.org/resource/{encodeURIComponent(params['founded'])}> rdfs:label "{params['founded']}" .'''  
        if 'profile_url' in params and params['profile_url']!="":
            rdfs_data +=f'''<{uri}> dbo:profile_url "{params['profile_url']}";
                                    node:profile_url  <{params['profile_url']}>.'''            


        if 'industry' in params and params['industry']!='':
            if isinstance(params['industry'], str):  # If industry is a single string
                industry = params['industry']  
                rdfs_data += f' <{uri}> dbo:industry "{industry}";'
                rdfs_data += f' node:industry <http://property.org/resource/{encodeURIComponent(industry)}> .'
                rdfs_data += f' <http://property.org/resource/{encodeURIComponent(industry)}> rdfs:label "{industry}" .'
            elif isinstance(params['industry'], list):  # If industry is a list of strings
                for industry in params['industry']:
                    
                    rdfs_data += f' <{uri}> dbo:industry "{industry}";'
                    rdfs_data += f' node:industry <http://property.org/resource/{encodeURIComponent(industry)}> .'
                    rdfs_data += f' <http://property.org/resource/{encodeURIComponent(industry)}> rdfs:label "{industry}" .'

        if 'specialities' in params and params['specialities']!='':
            if params['specialities']:
                if isinstance(params['specialities'], str):  # If specialities is a single string
                    specialities = params['specialities']  
                    rdfs_data += f' <{uri}> foaf:specialities "{specialities}".'
                
                elif isinstance(params['specialities'], list):  # If specialities is a list of strings
                    for specialities in params['specialities']:                   
                        rdfs_data += f' <{uri}> foaf:specialities "{specialities}".'

        if 'company_type' in params and params['company_type']!='':
            rdfs_data +=f'''<{uri}> foaf:company_type "{params['company_type']}". '''

        # if params['industry']:
        #     rdfs_data +=f'''<{uri}> dbo:industry "{params['industry']}";
        #                             node:industry <http://property.org/resource/{encodeURIComponent(params['industry'])}> .
        #     <http://property.org/resource/{encodeURIComponent(params['industry'])}> rdfs:label "{params['industry']}" .'''


        if 'ticker_symbol' in params and params['ticker_symbol']!='':
            rdfs_data +=f'''<{uri}> foaf:ticker-symbol "{params['ticker_symbol']}-{params['exchange']}";
                                    node:ticker-symbol <http://property.org/resource/{params['ticker_symbol']}-{params['exchange']}> . '''   
        if 'website' in params and params['website']!='':
            rdfs_data +=f'''<{uri}> foaf:website "{params['website']}";
                                    node:website <{params['website']}> .'''    
        if 'quarterly_revenue_growth' in params and params['quarterly_revenue_growth']!='':
            quarterly_revenue_growth_percentage=float(params['quarterly_revenue_growth']) * 100
            rdfs_data +=f'''<{uri}> foaf:quarterly_revenue_growth "{params['quarterly_revenue_growth']}^^xsd:float";
            node:quarterly_revenue_growth <http://property.org/resource/{encodeURIComponent(f"{quarterly_revenue_growth_percentage:.2f} %")}> .
            <http://property.org/resource/{encodeURIComponent(f"{quarterly_revenue_growth_percentage:.2f} %")}> rdfs:label "{quarterly_revenue_growth_percentage:.2f} %" .'''
        
        if 'last_quarterly_revenue' in params and 'second_last_quarterly_revenue' in params:
            latest_quarterly_revenue = float(params['last_quarterly_revenue'])
            second_latest_quarterly_revenue = float(params['second_last_quarterly_revenue'])
            annual_revenue_growth_percentage = ((latest_quarterly_revenue - second_latest_quarterly_revenue) / second_latest_quarterly_revenue) * 100

            rdfs_data +=f'''<{uri}> foaf:annual_revenue_growth "{annual_revenue_growth_percentage}"^^xsd:float;
            node:annual_revenue_growth <http://property.org/resource/{encodeURIComponent(f"{annual_revenue_growth_percentage:.2f} %")}> .
            <http://property.org/resource/{encodeURIComponent(f"{annual_revenue_growth_percentage:.2f} %")}> rdfs:label "{annual_revenue_growth_percentage:.2f} %" .'''
         
        if 'total_assets' in params and params['total_assets']!='':
            total_assets= float(params['total_assets']) / 1000000
            rdfs_data +=f'''<{uri}> foaf:total_assets "{params['total_assets']}"^^xsd:integer ;
            node:total_assets <http://property.org/resource/{encodeURIComponent(f"{total_assets:.2f} M")}>.
            <http://property.org/resource/{encodeURIComponent(f"{total_assets:.2f} M")}> rdfs:label "{total_assets:.2f} M" .'''

        if 'gross_profit' in params and params['gross_profit']!='':
            gross_profit= float(params['gross_profit']) / 1000000
            rdfs_data +=f'''<{uri}> foaf:gross_profit "{params['gross_profit']}"^^xsd:integer ;
            node:gross_profit <http://property.org/resource/{encodeURIComponent(f"{gross_profit:.2f} M")}>.
            <http://property.org/resource/{encodeURIComponent(f"{gross_profit:.2f} M")}> rdfs:label "{gross_profit:.2f} M" .'''

        if 'market_cap' in params and params['market_cap']!='':
            market_cap= float(params['market_cap']) / 1000000
            rdfs_data +=f'''<{uri}> foaf:market_cap "{params['market_cap']}"^^xsd:integer ;
            node:market_cap <http://property.org/resource/{encodeURIComponent(f"{market_cap:.2f} M")}>.
            <http://property.org/resource/{encodeURIComponent(f"{market_cap:.2f} M")}> rdfs:label "{market_cap:.2f} M" .'''

        if 'last_quarterly_revenue' in params and params['last_quarterly_revenue']!='':
            last_quarterly_revenue= float(params['last_quarterly_revenue']) / 1000000
            rdfs_data +=f'''<{uri}> foaf:last_quarterly_revenue "{params['last_quarterly_revenue']}"^^xsd:integer ;
            node:last_quarterly_revenue <http://property.org/resource/{encodeURIComponent(f"{last_quarterly_revenue:.2f} M")}>.
            <http://property.org/resource/{encodeURIComponent(f"{last_quarterly_revenue:.2f} M")}> rdfs:label "{last_quarterly_revenue:.2f} M" .'''

        if 'second_last_quarterly_revenue' in params and params['second_last_quarterly_revenue']!='':
            second_last_quarterly_revenue= float(params['second_last_quarterly_revenue']) / 1000000
            rdfs_data +=f'''<{uri}> foaf:second_last_quarterly_revenue "{params['second_last_quarterly_revenue']}"^^xsd:integer ;
            node:second_last_quarterly_revenue <http://property.org/resource/{encodeURIComponent(f"{second_last_quarterly_revenue:.2f} M")}>.
            <http://property.org/resource/{encodeURIComponent(f"{second_last_quarterly_revenue:.2f} M")}> rdfs:label "{second_last_quarterly_revenue:.2f} M" .'''


        if'current_year_revenue' in params and params['current_year_revenue']!='':
            current_year_revenue= float(params['current_year_revenue']) / 1000000
            rdfs_data +=f'''<{uri}> foaf:current_year_revenue "{params['current_year_revenue']}"^^xsd:integer ;
            node:current_year_revenue <http://property.org/resource/{encodeURIComponent(f"{current_year_revenue:.2f} M")}>.
            <http://property.org/resource/{encodeURIComponent(f"{current_year_revenue:.2f} M")}> rdfs:label "{current_year_revenue:.2f} M" .'''

        if 'previous_year_revenue' in params and params['previous_year_revenue']!='':
            previous_year_revenue= float(params['previous_year_revenue']) / 1000000
            rdfs_data +=f'''<{uri}> foaf:previous_year_revenue "{params['previous_year_revenue']}"^^xsd:integer ;
            node:previous_year_revenue <http://property.org/resource/{encodeURIComponent(f"{previous_year_revenue:.2f} M")}>.
            <http://property.org/resource/{encodeURIComponent(f"{previous_year_revenue:.2f} M")}> rdfs:label "{previous_year_revenue:.2f} M" .'''
         
        if 'employer' in params and params['employer']!='':
            emp_data=addEmployeeData(params,uri)
            rdfs_data +=emp_data                   

        if "custom_properties" in params and params['custom_properties']!='':
            data=addcustomproperty(params,uri)
            print(data)
            rdfs_data += data    




#Some extra fields that come into others source

        if 'SIC' in params and params['SIC']!="":
            rdfs_data+=f'''<{uri}> dbo:sic "{params['SIC']}" . 
                           <{uri}> node:sic <http://property.org/resource/{params['SIC']}> . '''    

        if 'NAICS' in params and params['NAICS']!="":
            rdfs_data+=f'''<{uri}> dbo:naics "{params['NAICS']}" . 
                           <{uri}> node:naics <http://property.org/resource/{params['NAICS']}> .'''  
            
        if 'sic' in params and params['sic']!="":
            rdfs_data+=f'''<{uri}> dbo:sic "{params['sic']}" . 
                           <{uri}> node:sic <http://property.org/resource/{params['sic']}> .'''   
                         
        if 'naics' in params and params['naics']!="":
            rdfs_data+=f'''<{uri}> dbo:naics "{params['naics']}" . 
                           <{uri}> node:naics <http://property.org/resource/{params['naics']}> .'''        


        if 'operating_years' in params and params['operating_years']!="":
            current_year = datetime.now().year
            founded=current_year - int(params['operating_years'])
            rdfs_data+=f'''<{uri}> foaf:founded "{founded}" . 
                           <{uri}> node:founded <http://property.org/resource/{founded}> . '''   
            
        if'revenue_dollar' in params and params['revenue_dollar']!='':
            current_year_revenue= float(params['revenue_dollar']) / 1000000
            rdfs_data +=f'''<{uri}> foaf:current_year_revenue "{params['revenue_dollar']}"^^xsd:integer ;
            node:current_year_revenue <http://property.org/resource/{encodeURIComponent(f"{current_year_revenue:.2f} M")}>.
            <http://property.org/resource/{encodeURIComponent(f"{current_year_revenue:.2f} M")}> rdfs:label "{current_year_revenue:.2f} M" .'''

        if 'quarterly_growth' in params and params['quarterly_growth']!='':
            if float(params['quarterly_growth']) < 1 :
                quarterly_revenue_growth_percentage=float(params['quarterly_growth']) * 100
            else:
                quarterly_revenue_growth_percentage=float(params['quarterly_growth'])

            rdfs_data +=f'''<{uri}> foaf:quarterly_revenue_growth "{params['quarterly_growth']}^^xsd:float";
            node:quarterly_revenue_growth <http://property.org/resource/{encodeURIComponent(f"{quarterly_revenue_growth_percentage:.2f} %")}> .
            <http://property.org/resource/{encodeURIComponent(f"{quarterly_revenue_growth_percentage:.2f} %")}> rdfs:label "{quarterly_revenue_growth_percentage:.2f} %" .'''
           
        if 'annual_growth' in params and params['annual_growth']!='':
            if float(params['annual_growth']) < 1 :
                annual_revenue_growth_percentage=float(params['annual_growth']) * 100
            else:
                annual_revenue_growth_percentage=float(params['annual_growth'])

            rdfs_data +=f'''<{uri}> foaf:annual_revenue_growth "{params['annual_growth']}^^xsd:float";
            node:annual_revenue_growth <http://property.org/resource/{encodeURIComponent(f"{annual_revenue_growth_percentage:.2f} %")}> .
            <http://property.org/resource/{encodeURIComponent(f"{annual_revenue_growth_percentage:.2f} %")}> rdfs:label "{annual_revenue_growth_percentage:.2f} %" .'''
           


        print(rdfs_data)

        graphDBResponse = add_rdf_statement({'repositoryID':DEFAULT_GRAPHDB_REPO,'rdfData':rdfs_data,'token':loginResponse['token']})
        if 'success' in graphDBResponse:
            response['success'] = True
        
    return response






def insert_data_graphdb_by_java(params: JavaGraphDB):
    my_logger = get_logger("/insert_data_graphdb_by_java")
    results = {}
    
    getToken = get_oauth_token_java() 
    if getToken.get('success'):
        
        headers = {
            "Content-Type": "application/json", 
            'Authorization': 'Bearer ' + getToken.get('access_token')
        }   
        
        try:
            response =  requests.post('https://95ac80e0-eb64-4ec7-9ca8-eb86eb3d627d-prod.e1-us-east-azure.choreoapis.dev/atcx/wso2service/jsonintegration-ad2/v1', data = json.dumps([params['data']]), headers = headers)
            my_logger.info('java endpoint response')
            my_logger.info(response)
    
            if response.status_code==200:
                results['success'] = True
                results['data'] = response
            else:
                results['error'] = "Unable to add statements in graphdb!"
                    
        except Exception as e:
            my_logger.error(e)
            results['error'] = e
    else:
        results['error'] = getToken['error']
    
    return results

def get_oauth_token_java():
    my_logger = get_logger("/get_oauth_token_java")
    results = {}
    payload = {
        "client_secret":"r2EZQPF_OYV96rwMrBf7lG2gEI3udTYPOIsCFn7pnTMa",
        "client_id":"nVLBRsu3oGtwOn6645E4EqXUJs4a",
        "grant_type":"client_credentials"
    } 
    headers = {
        "Content-Type": "application/x-www-form-urlencoded", 
        "Access-Control-Expose-Headers":"*",
        "Accept": "*/*",
    }  

    try:
        response =  requests.post('https://api.asgardeo.io/t/metacube/oauth2/token', headers = headers, data=payload)
        if response.status_code==200:
           results['success'] = True
           response  = response.json()
           results['access_token'] = response['access_token'];
        else:
           results['error'] = "Unable to get token"
                 
    except Exception as e:
        my_logger.error(e)
        results['error'] = e
    
    return results 

def is_company_exists(name, repo, token):
    result = {"status":False, "error":""}
    query = f'''PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbp: <http://dbpedia.org/property/>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>

                select * where{{
                    ?com a dbo:Organisation;
                        dbo:source ?source .
                    ?source rdfs:label "{name}_LinkedIn" ;
                        foaf:parent_name ?parent_name .
            }}'''
    query = encodeURIComponent(query)
    try:
        queryResult = execute_sparql_query({"repositoryID":repo,'query':query,'token':token});
        if len(queryResult['result']['results']['bindings']) > 0:
            record= queryResult['result']['results']['bindings'][0]
            result['status'] = True
            result['parent_name'] = record['parent_name']['value']
            result['company_uri'] = record['com']['value']
    except Exception as e:
        result['error'] = str(e)
    
    return result

def addContactInLinkedinSource(data, repo, token):
    result = {"success":False}
     
    company_linkedin_url = data['company_linkedin_url']
    #split_company_linkedin_url = company_linkedin_url.split('https://www.linkedin.com/company/')
    #split_company_linkedin_url = "https://www.linkedin.com/company/" + encodeURIComponent(split_company_linkedin_url[1])
     
    first_name = clean_string_v2(data['first_name'])
    company_name = clean_string_v2(data['company'])
    last_name = clean_string_v2(data['last_name'])
    full_name = clean_string_v2(data['full_name'])
    social_url = data['social_url']
    description = clean_description(data['description'])
    occupation = data['occupation']
    skills = data['skills']
    location = data['location']
    languages = data['languages']
    is_current = data['is_current']
    job_role_description = ""
    if data['job_role_description']:
        job_role_description = clean_description(data['job_role_description'])

    start_month = data['start_month']
    start_year = data['start_year']
    end_month = data['end_month']
    end_year = data['end_year']
    duration = data['duration']
    date_range = data['date_range']

    has_exp_link = f'{social_url}-{company_linkedin_url}-{clean_string(occupation)}-Experinecedetails'
    
    query = f'''PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX pro: <http://property.org/resource/>
        Insert Data {{
            
            <{company_linkedin_url}> dbo:employer <{social_url}> .
            <{social_url}> a vcard:Individual .
            <{social_url}> rdfs:label "{full_name}" .
            <{social_url}> foaf:first_name "{first_name}" .
            <{social_url}> foaf:last_name "{last_name}" .
            <{social_url}> dbo:description "{description}" .
            <{social_url}> vcard:skills "{skills}" .
            <{social_url}> vcard:languages "{languages}" .
            <{social_url}> vcard:location "{location}" .	

            <{social_url}> vcard:has_experience_details <{has_exp_link}> . 	
            
            <{has_exp_link}> rdfs:label "{full_name}-{company_name}-{clean_string_v2(occupation)}-Experinecedetails" . 
            <{has_exp_link}> dbo:employed_in <{company_linkedin_url}> .
            <{has_exp_link}> dbo:role "{occupation}" .
            <{has_exp_link}> dbo:is_current "{is_current}" .
            <{has_exp_link}> dbo:start_month "{start_month}" .
            <{has_exp_link}> dbo:start_year "{start_year}" .
            <{has_exp_link}> dbo:end_month "{end_month}" .
            <{has_exp_link}> dbo:end_year "{end_year}" .
            <{has_exp_link}> dbo:duration "{duration}" .
            <{has_exp_link}> dbo:date_range "{date_range}" .
            <{has_exp_link}> dbo:employee_role_description "{job_role_description}" .

        }}'''
    
    
    try:
        queryResult = update_rdf_statement({"repositoryID":repo,'rdfData':query,'token':token});
        print(queryResult)
        if queryResult['success'] == True:
            result['success'] = True
    except Exception as e:
        print(e)
        pass

    return result

def get_all_events():
    result = []
    loginResponse = login()
     
    query = f'''PREFIX event: <http://event.org/event/>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT distinct ?event ?name WHERE {{
                    ?event a dbo:Event ;
                        rdfs:label ?name .
                }}'''
    query = encodeURIComponent(query)
    try:
        queryResult = execute_sparql_query({"repositoryID":DEFAULT_GRAPHDB_REPO,'query':query,'token':loginResponse['token']});
        if queryResult['result']['results']['bindings']:
            data = queryResult['result']['results']['bindings']
            for item in data:
                result.append({"name":item["name"]['value'],'uri':item["event"]['value']})
    except Exception as e:
        pass
    
    return result

def is_company_exists_by_uri(uri, repo, token):
    result = {"status":False, "error":""}
    query = f'''PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbp: <http://dbpedia.org/property/>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>

                select * where{{
                    ?com a dbo:Organisation;
                        dbo:source ?source .
                    ?source 
                        foaf:parent_name ?parent_name .
                        FILTER (?source IN (<{uri}>))
            }}'''
    query = encodeURIComponent(query)
    try:
        queryResult = execute_sparql_query({"repositoryID":repo,'query':query,'token':token});
        if len(queryResult['result']['results']['bindings']) > 0:
            record= queryResult['result']['results']['bindings'][0]
            result['status'] = True
            result['parent_name'] = record['parent_name']['value']
            result['company_uri'] = record['com']['value']
    except Exception as e:
        result['error'] = str(e)
    
    return result

def findCompaniesByKeyword(keyword):
    response = []
    query = f'''PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT ?name
                WHERE {{ 
                    ?s a dbo:Organisation ;
                    dbo:source ?company .
                    ?company rdfs:label ?name .
                    FILTER (regex(?name, "{keyword}", "i") && STRSTARTS(str(?company), "https://www.linkedin.com"))
                     
                }}
                LIMIT 10'''
    token = login()
    output = execute_sparql_query({"repositoryID":DEFAULT_GRAPHDB_REPO,'token':token['token'],'query': encodeURIComponent(query)})
     
    if 'result' in output:
        if 'results' in output['result']:
            if 'bindings' in output['result']['results']:
                if len(output['result']['results']['bindings']) > 0:
                    for item in output['result']['results']['bindings']:
                        response.append(item['name']['value'])

    return response

def findPersonsByKeyword(keyword):
    response = []
    query = f'''PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
                SELECT *
                WHERE {{ 
                    ?s a vcard:Individual ;
                    rdfs:label ?name .
                    FILTER(regex(?name, "{keyword}", "i"))
                }}
                LIMIT 10'''
     
    token = login()
    output = execute_sparql_query({"repositoryID":DEFAULT_GRAPHDB_REPO,'token':token['token'],'query': encodeURIComponent(query)})
    if output['result'] is not None:
        if len(output['result']['results']['bindings']) > 0:
            for item in output['result']['results']['bindings']:
                response.append(item['name']['value'])
                

    return response

def findCompaniesByKeywordWithSource(keyword):
    response = []
    query = f'''PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX dbp: <http://dbpedia.org/property/>
                SELECT ?com ?name ?source ?headquarter
                WHERE {{
                    ?company a dbo:Organisation ;
                            dbo:source ?com .
                        ?com a dbo:Company;
                            rdfs:label ?name ;
                            dbo:source ?source .
                            OPTIONAL {{ ?com dbo:headquarters ?headquarter . }}
                        FILTER (regex(?name, "{keyword}", "i")  )
                        
                    {{
                        SELECT ?company (COUNT(?source) AS ?numSources)
                        WHERE {{
                            ?company dbo:source ?source .
                        }}
                        GROUP BY ?company
                        HAVING (COUNT(?source) = 1)
                    }}
                }}
                LIMIT 30'''
    token = login()
    output = execute_sparql_query({"repositoryID":DEFAULT_GRAPHDB_REPO,'token':token['token'],'query': encodeURIComponent(query)})
     
    if 'result' in output:
        if 'results' in output['result']:
            if 'bindings' in output['result']['results']:
                if len(output['result']['results']['bindings']) > 0:
                    for item in output['result']['results']['bindings']:
                        response.append({
                            "uri":item['com']['value'],
                            "name":item['name']['value'],
                            "source":item['source']['value'],
                            "headquarter":item['headquarter']['value'] if "headquarter" in item else ""
                        })

    return response

def addGliefParentNodeInGraphDb(params):
    response = {'success':False}
     
    rdfData = f'''
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                delete{{
                    ?org ?p ?o .
                    ?p1 ?p2 ?org .
                }}
                insert{{
                    <{params['gleif_id']}> ?p ?o.
                    ?p1 ?p2 <{params['gleif_id']}>.
                }}
                where{{
                    ?org a dbo:Organisation ;
                        dbo:source <{params['company_uri']}> .
                    ?org ?p ?o .
                    optional{{  ?p1 ?p2 ?org .}}
                        
                }}
            '''
    token = login()
    output = update_rdf_statement({"repositoryID":'sample-master-repo-v2','token':token['token'],'rdfData': rdfData})
    if output['success'] : 
        response['success']=True
        

    return response