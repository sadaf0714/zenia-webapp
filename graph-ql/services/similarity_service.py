from fastapi import FastAPI, HTTPException
from config.constant import EMBEDDING_ENDPOINT, REDIS_ENDPOINT,GPT_REORDER_ENDPOINT, REDIS_GET_COMPANIES, VECTOR_ACTIVE_CLASSIFICATION, CLASSIFIED_COMPANIES_REDIS, GET_SPARQL_BY_GPT, GRAPHDB_VISUAL_GRAPH, DEFAULT_GRAPHDB_REPO, GET_CLASSIFIED_RESULT_BY_NLP, REDIS_GET_CLAIM, ASSURANT_POC_REPO, ASSURANT_SIMILARITY_INDEX_NAME, GET_SPARQL_BY_GPT_FOR_CLAIMS
import requests
import json
from ariadne import QueryType
from models.company import Company
from typing import List
from config.log_config import get_logger
from config.util import handle_similar_result, config_graph_query, getSparqlQueryForCompanyDetails, getSparqlQueryForSimilarCompaniesByName, getSparqlQueryForEmployeesInCompanies, addPersonsDataIntoCompaniesData, config_graph_query_redis, is_key_exists_in_dictionary, config_graph_query_for_graph_similarity, get_value_from_graph_similarity_data, encodeURIComponent, config_graph_query_for_claim_similarity
from graphql import GraphQLError
from services import graphdb_service

def get_embedding(search_term, platform_type):
    
    my_logger = get_logger("/getembedding")
    
    list = []
    list.append(search_term)
    data = {"search_term": list, "type": platform_type}
    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_url = f'{EMBEDDING_ENDPOINT}/getembedding/'
    #sending request to  vector embedding micro-service
    try:
        response = requests.get(vector_embedding_url, data = json.dumps(data), headers= headers)
        if response.status_code==200 :
            return response.json().get('data').get('term_0')
        elif response.status_code==404 :
            response = response.json()
            raise Exception(response.get('error'))
        else:
           raise Exception('Similarity not found')      
    except Exception as e:
        my_logger.error(e)
        raise Exception


def redis_search(search_vectors, top_k, platform_type, text_classification, company_type, revenue, field_name=None):
    my_logger = get_logger("/redis-similarity-search")

    data = {
            "vectors": search_vectors, 
            "type": platform_type, 
            "top_k": top_k, 
            "classifications": text_classification,
            "company_type": company_type,
            "revenue": revenue,
            "field_name_for_lamma": field_name
        }

    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_url = f'{REDIS_ENDPOINT}/redis-similarity-search'
    #sending request to  vector embedding micro-service
    try:
        response = requests.get(vector_embedding_url, data = json.dumps(data), headers= headers)
        if response.status_code==200 :
            response = response.json()
            return response.get('data')
        elif response.status_code==404 :
            response = response.json()
            raise Exception(response.get('error'))
        else:
           raise Exception('Similarity not found')      
    except Exception as e:
        my_logger.error(e)
        return e


def get_text_classification(text):
    my_logger = get_logger("/get-classification")

    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_service = f'{EMBEDDING_ENDPOINT}/get-classification'

    #sending request to  vector embedding micro-service
    try:
        response = requests.get(vector_embedding_service, data = json.dumps({"search_term": text}), headers= headers)
        if response.status_code==200 :
            response = response.json()
            return response.get('data')
        elif response.status_code==404 :
            response = response.json()
            raise Exception(response.get('error'))
        else:
           raise Exception('Similarity not found')      
    except Exception as e:
        my_logger.error(e)
        return e

def get_gpt_search(redis_results,user_query):
    my_logger = get_logger("/get-gpt-similarity")
    headers = {
        "Content-Type": "application/json"
    }
    gpt_service = f'{GPT_REORDER_ENDPOINT}'
    result = {'data':[],'error':None}
    #sending request to  vector embedding micro-service
    try:
        response = requests.get(gpt_service, data = json.dumps({"query":user_query,"similarity_data": redis_results}), headers= headers)
        if response.status_code==200 :
            response = response.json()
            if len(response.get('data').get('resp')) > 0:
                records = response.get('data').get('resp')
                for item in records:
                    temp = 1-float(item.get("vector_score", ""))
                    temp = "{:.4f}".format(round(temp, 4))
                    item['vector_score'] = temp    
                result['data'] = records
            else:
                result['error'] = "Similarity not found"
        elif response.status_code==404 :
            response = response.json()
            result['error'] = response.get('error')
        else:
           result['error'] = "Similarity not found"
    except Exception as e:
        my_logger.error(e)
        result['error'] = e

    return result
    
def get_companies(company_list: list, events:list = [], codes: dict = {}):
    
    result = []
    my_logger = get_logger("/get-companies-graphql")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to  vector redis service to fetch all matched companies
    payload = {
        "company_list":company_list,
        "events":events,
        "codes":codes
    }
    try:
        response = requests.get(f'{REDIS_GET_COMPANIES}', data = json.dumps(payload), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            result = response.get('data')
        elif response.status_code == 404 :
            my_logger.error(response.get('error'))
        else:
            my_logger.error('No companies found')      
    except Exception as e:
        my_logger.error(e)
        pass

    return result

def get_companies_by_status(query: str, company_list: list):
    
    my_logger = get_logger("/get_companies_by_status")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to  vector embedding micro-service to fetch companies by their status
    try:
        response = requests.get(f'{VECTOR_ACTIVE_CLASSIFICATION}', data = json.dumps({"similarity_data":company_list, 'query': query}), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            if len(response) > 0:
               return response;     
            else:
                raise Exception('No companies found')     
        elif response.status_code == 404 :
            response = response.json()
            raise Exception(response.get('error'))
        else:
            raise Exception('No companies found')      
    except Exception as e:
        my_logger.error(e)
        raise Exception(e)      
    
def get_classified_companies(criteria: list, company_list: list, codes: dict, events:list = []):
    results = []
    my_logger = get_logger("/get-classified-companies")
    headers = {
        "Content-Type": "application/json"
    }
    payload  = {
        "company_list": company_list,
        "classifications": criteria,
        'codes': codes,
        "events": events
    }
    
    #sending request to vector redis service to fetch criteria matched companies
    try:
        response = requests.get(f'{CLASSIFIED_COMPANIES_REDIS}', data = json.dumps(payload), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            if len(response.get('data')) > 0:
               results =  response.get('data')
            else:
                raise Exception('No companies found')     
    except Exception as e:
        my_logger.error(e)
        raise Exception(e)

    return results    

def get_companies_list(company_list: list):
    results = { "data":[]}
    my_logger = get_logger("/get-companies-graphql")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to  vector redis service to fetch all matched companies
    try:
        response = requests.get(f'{REDIS_GET_COMPANIES}', data = json.dumps({"company_list":company_list}), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            results['success'] = True;
            results['data'] = response.get('data');
        elif response.status_code == 404 :
            response = response.json()
            results['error'] = response.get('error')
        else:
            results['error'] = "No companies found"
              
    except Exception as e:
        my_logger.error(e)
        results['error'] = e
       
    return results

def get_sparql_query(input: str):
    results = {'error':None, 'sparql_query':None}
    my_logger = get_logger("/get-sparql-qery")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to  vector embedding service to fetch the sparql query by gpt
    try:
        response = requests.get(f'{GET_SPARQL_BY_GPT}', data = json.dumps({"input":input}), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            if response['error'] == None:
                results['sparql_query'] = response.get('sparql_query')
            else:
                results['error'] = response.get('error')
        elif response.status_code == 404 :
            response = response.json()
            results['error'] = response.get('error')
        else:
            results['error'] = "No data found"
              
    except Exception as e:
        my_logger.error(e)
        results['error'] = e
    return results


def getSimilarCompaniesByRedis(name: str, top_k: int, field_name: str, platform_type: str):
    results = {}
    try:
        # 1 consume redis service to get given company article
        redis_companies = get_companies([name])
        article = redis_companies[0]['get_emb']
        industry = redis_companies[0]['industry']
        location = redis_companies[0]['headquarters']

        if platform_type == "HUGGINGFACE":
            vectors = redis_companies[0]['huggingface_embedding']
        elif platform_type == "OPENAI":
            vectors = redis_companies[0]['openai_embedding']
        elif platform_type == "LAMMAGPT":
            if field_name == 'lamma_embedding':
                vectors = redis_companies[0]['lamma_embedding']
            elif field_name == 'lamma_embedding2':
                vectors = redis_companies[0]['lamma_embedding2']
            elif field_name == 'lamma_embedding3':
                vectors = redis_companies[0]['lamma_embedding3']

        # 3 send that vectors to  redis search to get similar companies
        similar_companies = redis_search(vectors, top_k, platform_type, 
                                {"location": [location], "industry": [industry]}, [], {"min": 0, "max": 0},field_name)
        
        # print(similar_companies)
       
        if (len(similar_companies) > 0):
            for item in similar_companies:
                temp = 1-float(item.get("vector_score", ""))
                temp = "{:.4f}".format(round(temp, 4))
                item['vector_score'] = temp
            visual_graph_url = config_graph_query_redis(similar_companies)
            results['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
            results['records'] = similar_companies;
    except Exception as e:
        results['error'] = e
    print(results['graph_url'])
    return results

def createStandardOutput(similarCompanies):
    records =[]
    for company in similarCompanies:
        companyName = company["companyName"]["value"]
        if(any(companyName == record["name"]  for record in records )):
            continue

        try:
            records.append({
                "name": companyName if (is_key_exists_in_dictionary(company, "companyName") ) else None,
                "vector_score": company["score"]["value"] if (is_key_exists_in_dictionary(company, "score") ) else None,
                "SIC": get_value_from_graph_similarity_data({"company":companyName,"field":"sic"},similarCompanies),
                "NAICS": get_value_from_graph_similarity_data({"company":companyName,"field":"naics"},similarCompanies),
                "id": company["documentID"]["value"] if (is_key_exists_in_dictionary(company, "documentID") ) else None,
                "industry": get_value_from_graph_similarity_data({"company":companyName,"field":"industry"},similarCompanies),
                "headquarters": get_value_from_graph_similarity_data({"company":companyName,"field":"headquarter"},similarCompanies),
                "no_of_employees": get_value_from_graph_similarity_data({"company":companyName,"field":"numberOfEmployees"},similarCompanies),
                "founded": get_value_from_graph_similarity_data({"company":companyName,"field":"founded"},similarCompanies),
                "annual_growth": company["annualgrowth"]["value"] if (is_key_exists_in_dictionary(company, "annualgrowth") ) else None,
                "quarterly_growth": get_value_from_graph_similarity_data({"company":companyName,"field":"quarterly_revenue_growth"},similarCompanies),
                "description": get_value_from_graph_similarity_data({"company":companyName,"field":"description"},similarCompanies),
                "operating_years": get_value_from_graph_similarity_data({"company":companyName,"field":"operating_years"},similarCompanies),
        })
        except Exception as e:
            pass
    return records




def getSimilarCompaniesByGraph(name: str, resultsLimit: int):
    results = {}
    try:
        # 1. get access token
        loginReponse  = graphdb_service.login()
        
        # 2. get company details like industry, location and URI.
        companyDetails = graphdb_service.run_query({"token":loginReponse.get('token'),"query":getSparqlQueryForCompanyDetails({"company_name":name}),"repositoryID":DEFAULT_GRAPHDB_REPO})
        companyURI = companyDetails["results"]["bindings"][0]["companySourceURI"]["value"]

        # 3. we need to fetch the similar companies from graphdb index
        similarCompanies = graphdb_service.run_query({"token":loginReponse.get('token'),"query":getSparqlQueryForSimilarCompaniesByName(companyURI,resultsLimit),"repositoryID":DEFAULT_GRAPHDB_REPO})
        if( len(similarCompanies["results"]["bindings"]) == 0):
            raise Exception('No companies found')
        
        similarCompaniesWithStandardOutput = createStandardOutput(similarCompanies["results"]["bindings"])
        personsData = graphdb_service.run_query({"token":loginReponse.get('token'),"query":getSparqlQueryForEmployeesInCompanies(similarCompaniesWithStandardOutput),"repositoryID":DEFAULT_GRAPHDB_REPO})
                 
        similarCompaniesWithStandardOutput = addPersonsDataIntoCompaniesData(similarCompaniesWithStandardOutput,personsData)
        visual_graph_url = config_graph_query_for_graph_similarity(similarCompaniesWithStandardOutput)
        results['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
        results['records']  = similarCompaniesWithStandardOutput
    except Exception as e:
        results['error'] = e

    return results     


def get_classified_result(input: str):
    results = {'error':None, 'attribute':None, 'entities':None}
    my_logger = get_logger("/get-classified-result")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to  vector embedding service to fetch the classified results by NLP
    try:
        response = requests.post(f'{GET_CLASSIFIED_RESULT_BY_NLP}', data = json.dumps({"input":input}), headers=headers )
        if response.status_code == 200 :
            response = response.json()
            results['attribute'] = response.get('attribute')
            results['entities'] = response.get('entities')
        elif response.status_code == 404 :
            results['error'] = "Data not found"
        else:
            results['error'] = "No data found"
    except Exception as e:
        my_logger.error(e)
        results['error'] = e
    return results

def get_claim(claimId:str):
    
    result = {}
    my_logger = get_logger("/get-claim-graphql")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to vector redis service to fetch claims
    payload = {
        "claimId":claimId
    }
    try:
        response = requests.post(f'{REDIS_GET_CLAIM}', data = json.dumps(payload), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            result = response.get('data')
    except Exception as e:
        my_logger.error(e)
        pass
    return result

def getSimilarClaimsByRedis(claimId: str, top_k: int, vector_field: str):
    results = {}
    # 1 consume redis service to get claim details
    redis_claims = get_claim(claimId)
    if redis_claims:
        try:
            vectors = redis_claims[0][vector_field]

            # 2 send that vectors to redis search to get similar companies
            similarClaims = redis_searchSimilarClaims(vectors, vector_field, top_k)

            if (len(similarClaims) > 0):
                for item in similarClaims:
                    temp = 1-float(item.get("vector_score", ""))
                    temp = "{:.4f}".format(round(temp, 4))
                    item['vector_score'] = temp
                results['records'] = similarClaims
        except Exception as e:
            results['error'] = e
    else:
        results['error'] = "Claim not found"

    return results


def redis_searchSimilarClaims(search_vectors, vector_field, top_k):
    my_logger = get_logger("/redis-similarity-search-for-claims")

    data = {
            "vectors": search_vectors,
            "vector_field": vector_field,
            "top_k": top_k
        }
        

    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_url = f'{REDIS_ENDPOINT}/get-similar-claims'
    #sending request to  vector embedding micro-service
    try:
        response = requests.get(vector_embedding_url, data = json.dumps(data), headers= headers)
        #print(response)
        if response.status_code==200 :
            response = response.json()
            return response.get('data')
        elif response.status_code==404 :
            response = response.json()
            raise Exception(response.get('error'))
        else:
           raise Exception('Similarity not found')      
    except Exception as e:
        my_logger.error(e)
        return e

def getSimilarClaimsByGraph(claimId: str, top_k: int):
    results = {"claims":[],'graph_url':""}
    try:
        # 1. get access token
        loginReponse  = graphdb_service.login()
         
        # 2. get claim details by claim id
        claimDetail = graphdb_service.run_query({"token":loginReponse.get('token'),"query":getClaimDetailByTitle({"claimId":claimId}),"repositoryID":ASSURANT_POC_REPO})
        if len(claimDetail["results"]["bindings"]) > 0:
            claimURI = claimDetail["results"]["bindings"][0]["claimURI"]["value"]
         
            # 3. we need to fetch the similar claims from graphdb index
            similarClaims = graphdb_service.run_query({"token":loginReponse.get('token'),"query":getSparqlQueryForSimilarClaims(claimURI,top_k),"repositoryID":ASSURANT_POC_REPO})
             
            if( len(similarClaims["results"]["bindings"]) > 0):
                data = similarClaims["results"]["bindings"]
                records = []
                for itemKey, item in enumerate(data):
                    temp = {}
                    for innerKey, innerItem in item.items():
                        temp[innerKey] = innerItem['value']
                    records.append(temp)    
                results['claims']  = records

                top_results = results['claims'][:10] 
                visual_graph_url = config_graph_query_for_claim_similarity(top_results)
                
                results['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
                
    except Exception as e:
        print(e)
        pass

    return results 


def getClaimDetailByTitle(params: dict):
    query = f''' 
        PREFIX c: <http://example.org/insurance#>
        SELECT * where {{
            ?claimURI a c:Claim ;
            c:claimID  ?claimId ;        
            c:claimTitle ?claimTitle .
            FILTER (?claimId="{params['claimId']}")
        }}'''
    return encodeURIComponent(query)

def getSparqlQueryForSimilarClaims(claimURI: str, top_k: int):
    query =f'''
        PREFIX :<http://www.ontotext.com/graphdb/similarity/>
        PREFIX inst:<http://www.ontotext.com/graphdb/similarity/instance/>
        PREFIX psi:<http://www.ontotext.com/graphdb/similarity/psi/>
        PREFIX c: <http://example.org/insurance#>

        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?entity ?vector_score ?claimID ?claimTitle ?claimDescription ?claimDate ?incidentDescription 
            ?claimStatus ?claimAmount ?claimStatusReason ?personName ?policyPlanName
            ?injuryInformation ?witnessInformation ?adjusterNotes ?incidentType ?incidentLocation ?incidentTime ?incidentDate
            ?vehicle ?licensePlate ?premiumAmount ?coverageStartDate ?coverageEndDate

        {{
            ?search a inst:{ASSURANT_SIMILARITY_INDEX_NAME} ;
                psi:searchEntity <{claimURI}>;
                psi:searchPredicate <http://www.ontotext.com/graphdb/similarity/psi/any>;
                :searchParameters "-numsearchresults {top_k}";
                psi:entityResult ?result .
            ?result :value ?entity ;
                    :score ?vector_score .
            ?entity a c:Claim ;
                    c:claimID ?claimID;
                    c:claimTitle ?claimTitle;
                    c:claimDescription ?claimDescription;
                    c:incidentDescription ?incidentDescription ;
                    c:claimStatus ?claimStatus ;
                    c:claimAmount ?claimAmount ;    
                    c:claimStatusReason ?claimStatusReason;
                    c:claimDate ?claimDate;
                    c:policy [c:policyPlan ?policyPlanName] ;
                    c:policy [c:premiumAmount ?premiumAmount] ;
                    c:policy [c:coverageStartDate ?coverageStartDate] ;
                    c:policy [c:coverageEndDate ?coverageEndDate] ;
                    c:injuryInformation ?injuryInformation;
                    c:witnessInformation ?witnessInformation;
                    c:adjusterNotes ?adjusterNotes;
                    c:incidentType ?incidentType;
                    c:incidentLocation ?incidentLocation;
                    c:incidentTime ?incidentTime;
                    c:incidentDate ?incidentDate;
                    c:insured [rdfs:label ?personName] ;
                    c:vehicle [rdfs:label ?vehicle] ;
                    c:vehicle [c:licensePlate ?licensePlate] .
                    
        }}'''
    return encodeURIComponent(query)

def get_sparql_query_for_claims(input: str):
    results = {'error':None, 'sparql_query':None}
    my_logger = get_logger("/get-sparql-qery-for-claims")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to  vector embedding service to fetch the sparql query by gpt
    try:
        response = requests.get(f'{GET_SPARQL_BY_GPT_FOR_CLAIMS}', data = json.dumps({"input":input}), headers = headers)

        if response.status_code == 200 :
            response = response.json()
            if response['error'] == None:
                results['sparql_query'] = response.get('sparql_query')
            else:
                results['error'] = response.get('error')
        elif response.status_code == 404 :
            response = response.json()
            results['error'] = response.get('error')
        else:
            results['error'] = "No data found"
              
    except Exception as e:
        my_logger.error(e)
        results['error'] = e
    return results

def get_chat_completion(prompt, model):
    my_logger = get_logger("/get_chat_completion")
    result = {"error":None,"data":""}
    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_service = f'{EMBEDDING_ENDPOINT}/getChatCompletion'
    try:
        response = requests.get(vector_embedding_service, data = json.dumps({"prompt": prompt,'model':model}), headers= headers)
        if response.status_code==200 :
            response = response.json()
            if response.get('data') != "":
                result['data'] =  response.get('data')
            if response.get('error') != "":
                result['error'] =  response.get('error')    
    except Exception as e:
        result['error'] = e
        
    return result

def get_chat_completion_mistral(prompt, model):
    my_logger = get_logger("/get_chat_completion_mistral")
    result = {"error":None,"data":""}
    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_service = f'{EMBEDDING_ENDPOINT}/getChatCompletionMistral'
    try:
        response = requests.get(vector_embedding_service, data = json.dumps({"prompt": prompt,'model':model}), headers= headers)
        if response.status_code==200 :
            response = response.json()
            if response.get('data') != "":
                result['data'] =  response.get('data')
            if response.get('error') != "":
                result['error'] =  response.get('error')    
    except Exception as e:
        result['error'] = e
        
    return result

def getLangChainSummarization(pdf_url):
    my_logger = get_logger("/get_lanchain_summarization")
    summary = ""
    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_service = f'{EMBEDDING_ENDPOINT}/langchain-summarization'
    try:
        response = requests.post(vector_embedding_service, data = json.dumps({"pdf_url": pdf_url}), headers= headers)
        if response.status_code==200 :
            response = response.json()
            if response['summary'] != "":
               summary = response['summary']
    except Exception as e:
        my_logger.info(e)
        pass
        
    return summary