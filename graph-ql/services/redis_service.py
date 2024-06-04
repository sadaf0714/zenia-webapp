from fastapi import FastAPI, HTTPException
from config.log_config import get_logger
import requests
import json
from typing import List
from pydantic import BaseModel
from config.constant import STORE_DATA_URL, REDIS_UPDATE_DATA_URL, REDIS_GET_COMPANY_BY_ID ,COMPANY_DATA_URL, REDIS_UPDATE_DATA_COMP



def store(data: dict):
    results = {};
    my_logger = get_logger("/store-data-into-redis")
    headers = {
        "Content-Type": "application/json"
    } 

    try:
        response = requests.post(f'{STORE_DATA_URL}', data = json.dumps([data]), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            my_logger.info('redis response')
            my_logger.info(response)
            if(len(response['content']['inserted_companies']) > 0):
                results['success'] = True  
    except Exception as e:
        my_logger.error(e)
        raise Exception(e)

    return results

def update(comp_key: str, data: dict):
    results = {"error":"","success":False};
    my_logger = get_logger("/store-data-into-redis")
    headers = {
        "Content-Type": "application/json"
    } 
    payload = {
        "comp_key": comp_key,
        "data": data
    }
    
    try:
        response = requests.post(f'{REDIS_UPDATE_DATA_URL}', data = json.dumps(payload), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            if(response.get('success')==True):
                results['success'] = True
                results['company_name'] = response.get('content')  
            else:
                results['error'] = response.get('error') 
        else:
            results['error'] = "Unable to update record"
    except Exception as e:
        results['error'] = e
    
    return results

def update_comp(comp_key: str, data: dict):
    results = {"error":"","success":False};
    my_logger = get_logger("/store-data-into-redis")
    headers = {
        "Content-Type": "application/json"
    } 
    payload = {
        "comp_key": comp_key,
        "data": data
    }
    
    try:
        response = requests.post(f'{REDIS_UPDATE_DATA_COMP}', data = json.dumps(payload), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            if(response.get('success')==True):
                results['success'] = True
                results['company_name'] = response.get('content')  
            else:
                results['error'] = response.get('error') 
        else:
            results['error'] = "Unable to update record"
    except Exception as e:
        results['error'] = e
    
    return results

def getCompanyById(comp_key: str):
    results = {"error":"","success":False, "data":{}};
    my_logger = get_logger("/get-company-by-id")
   
    try:
        response = requests.get(f'{REDIS_GET_COMPANY_BY_ID}?id={comp_key}')
        if response.status_code == 200 :
            response = response.json()
            if response:
                results['data'] = response
                results['success'] = True
            else:
                results['error'] = "Unable to find record"
        else:
            results['error'] = "Unable to find record"
    except Exception as e:
        results['error'] = e
    
    return results




    