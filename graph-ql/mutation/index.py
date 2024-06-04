from fastapi import FastAPI, HTTPException
import requests
import json
from pydantic import BaseModel
from typing import List
import uuid
from typing import Optional
from config.log_config import get_logger
from ariadne import MutationType
from services import similarity_service, graphdb_service, redis_service, crawler_service ,syncRedisDB, csvLeadGeneration_service, insertDataIntoParentNode, insurance_plan
from config.util import handle_similar_result, classify_text, array_to_comma, multiple_array_to_comma, config_query, config_graph_query, create_rdf_data, config_delete_query, clean_description, clean_name, validate_fields
from config.constant import DEFAULT_GRAPHDB_REPO, GRAPHDB_VISUAL_GRAPH, GRAPHDB_SERVICE, GRAPHQL_SERVICE, REDIS_SERVICE_URL
from datetime import datetime, timezone
import asyncio


mutation = MutationType()


@mutation.field('storeDataInRedisGraphDb')
def store_data_in_redis_graphdb(_, info, data = dict):
    my_logger = get_logger("/storeDataInRedisGraphDb")  
    results = {};
    if data: 
          for var in data:     
                if data[var] != "" and type(data[var]) == str :
                    data[var] =  data[var].strip()
    
    #check the required fields
    check_validation = validate_fields(data);

    if check_validation != "":
       results['error'] = check_validation
    else:
 

        #Generate vector embedding and some default fields            
        description = clean_description(data.get('description'))
        data['description'] = description
        
        ##set timestamp
        utctimenow = datetime.now(timezone.utc)
        data['timestamp'] = utctimenow.strftime('%d-%m-%YT%T')
        
        
        my_logger.info(json.dumps(data))
         
        #insert data in graphdb
        response = graphdb_service.insertCrwaledDataintoGraphDB( data)
        my_logger.info(response)
        visual_graph_url = config_query([{"name":data['parent_name']}])
        results['graph_url']  = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"               
    
    return results


# @mutation.field('syncCompanyData')
# def sync_data_in_redisdb(_, info, comParent_url = list):
#     if (comParent_url != None) :
#         result = syncRedisDB.insert_company_into_redis(comParent_url)
#     else :
#         result = "Data sync is not completed (Either no body present or no data in Graph)"
#     return result

#  *******************  Parent post data *******************

@mutation.field('syncCompanyData')
def sync_company_data(_, info, comParent_url: list, isCrawl:bool):

    result = {"record":None, "error":None}
    
    if (comParent_url != None) :
        result['record'] = syncRedisDB.insert_company_into_redis(comParent_url,isCrawl)
    else :
        result['error'] = "Data sync is not completed (Either no body present or no data in Graph)"

    return result

@mutation.field('csvLeadGeneration')
def csvLeadGeneration(_, info):
    return csvLeadGeneration_service.run()

@mutation.field('insertParentData')
def insert_parent_data(_, info, comParent_url: list, isCrawl:bool):

    result = {"record":[], "error":[]}
    if (comParent_url != None) :
        result = insertDataIntoParentNode.insert_data_on_parent(comParent_url,isCrawl)
        print(result)
    else :
        result['error'] = "Data insertion on parent is not completed (Either no body present or no data in Graph)"

    return result

@mutation.field('addParentGliefNode')
def addParentGliefNode(_, info, gleif_id: str, name:str, company_uri:str):
    return graphdb_service.addGliefParentNodeInGraphDb({"gleif_id":gleif_id,'name':name,'company_uri':company_uri}) 


@mutation.field('markWinningQuote')
def markWinningQuote(_, info, request_uri: str, plan_uri: str, plan_name:str, bestPlanReason:list):
    response = {"success":False, "error":""}

    result = insurance_plan.markWinningQuote(request_uri, plan_uri, plan_name, bestPlanReason) 

    asyncio.create_task(insurance_plan.updateSummaryReason(plan_uri))

    if result['success']:
        response['success'] = True
    else:
        response['error'] = "Something went wrong!"
    return response

@mutation.field('koreAIDataLoader')
def koreAIDataLoader(_, info, pdf_files: list):
    response = {"success":False, "error":""}
    url = "https://kitten-expert-mostly.ngrok-free.app/api/rag_llama2/dataLoader"
    
    payload = json.dumps({"pdf_files": pdf_files})
    headers = {
        'Content-Type': 'application/json'
    }
    koreAIResp = requests.request("POST", url, headers=headers, data=payload, verify=False)
    
    if koreAIResp.status_code == 200:
        json_data = koreAIResp.json()
        if json_data=="Done!":
            response['success'] = True
        else:
            response['error'] = "Something went wrong!"
    else:
        response['error'] = "Something went wrong!"
    
    return response
