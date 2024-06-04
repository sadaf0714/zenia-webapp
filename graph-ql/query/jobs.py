from filecmp import cmp
from subprocess import call
from unittest import result
from fastapi import FastAPI, HTTPException
import requests
import json
from ariadne import QueryType
from pydantic import BaseModel
from typing import List
from config.log_config import get_logger
from services import similarity_service, graphdb_service, redis_service, crawler_service, url_crawler_service, job_service
from typing import Optional
import random
from config.constant import HR_USECASE_JOB_REPO, GRAPHDB_VISUAL_GRAPH, DEFAULT_GRAPHDB_REPO
from config.util import config_graph_query_candidates, config_graph_query_jobs,encodeURIComponent
import uuid

jobQuery = QueryType()

@jobQuery.field('getJobList')
def get_job_list(_, info):
    result = {'job_list':[]}
    loginReponse  = graphdb_service.login()
    resp = job_service.get_job_list({"repositoryID": HR_USECASE_JOB_REPO, "token": loginReponse.get('token')})
    if len(resp['result']) > 0:
        result['job_list'] = resp['result']
    
    return result

@jobQuery.field('getJobByName')
def get_job_info(_, info, title: str, publisher:str):
    result = {'record':{}}
    loginReponse  = graphdb_service.login()
    resp = job_service.get_job_by_title({"repositoryID": HR_USECASE_JOB_REPO, "token": loginReponse.get('token'),"title":title,"publisher":publisher})
    if resp['result']:
        result['record'] = resp['result']
    
    return result

@jobQuery.field('getCandidatesByJob')
def get_candidates_by_job(_, info, job_title: str, job_publisher: str, industry: str, top_k: int = 10):
    result = {"candidates":[]}
    response = job_service.getSimilarCandidatesByJobFromRedis(job_title, job_publisher, industry, top_k)
    if len(response['records']) > 0:
        for item in response['records']:
            #temp = 1-float(item.get("vector_score", ""))
            temp = "{:.4f}".format(item.get("vector_score", ""))
            item['vector_score'] = temp
        top_results = response['records'][:10]
        if industry == "hotel":
            top_results = response['records']
        visual_graph_url = config_graph_query_candidates(top_results)
        result['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
        result['candidates'] = response['records']   
    return result
     

@jobQuery.field('getCandidateList')
def getCandidateList(_, info):
    result = {"candidates":[]}
    loginReponse  = graphdb_service.login()
    resp = job_service.get_candidates_list({"repositoryID": HR_USECASE_JOB_REPO, "token": loginReponse.get('token')})
    if len(resp['result']) > 0:
        result['candidates'] = resp['result']
    
    return result 

@jobQuery.field('getCandidateByName')
def getCandidateByName(_, info, name: str, resume: str):
    result = {'record':{}}
    loginReponse  = graphdb_service.login()
    resp = job_service.get_candidate_details_from_redis(name, resume)
    if resp != []:
        result['record'] = {"name": resp[0]["name"],
                "skills": resp[0]["skills"]}
    
    return result

@jobQuery.field('getJobsByCandidate')
def getJobsByCandidate(_, info,  name: str, resume: str = "", industry: str = "HR", top_k: int = 10):
    result = {"job_list":[],'graph_url':""}
    resp = job_service.getSimilarJobsByCandidateFromRedis(name, resume, industry, top_k)
    if len(resp['records']) > 0:
        jobsTitles = []
        for item in resp['records']:
            temp = "{:.4f}".format(float(item.get("vector_score", "")))
            item['vector_score'] = temp
            jobsTitles.append(item.get('job_title'))
        
        jobs_string = ', '.join(['"{}"'.format(item) for item in jobsTitles])    
        query = f'''PREFIX saro: <http://w3id.org/saro#>
                 PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                 SELECT ?s ?name
                 where {{ 
                    ?s a saro:Job ;
                    rdfs:label ?name .
                    filter(?name in ({jobs_string}))
                }}'''
        query = query.replace("\n", "")
        query = encodeURIComponent(query)
        loginResponse = graphdb_service.login()
        getAllJobsURIs = graphdb_service.execute_sparql_query({"repositoryID":HR_USECASE_JOB_REPO,'token':loginResponse.get('token'),'query':query})
        
        if len(getAllJobsURIs['result']['results']['bindings']) > 0:
            for item in resp['records']:
                for item_inner in getAllJobsURIs['result']['results']['bindings']:
                    if item_inner['name']['value'] == item['job_title']:
                        item['graph_uri'] = item_inner['s']['value']
            
            top_results = resp['records'][:10]
            visual_graph_url = config_graph_query_jobs(top_results)
            result['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"

        result['job_list'] = resp['records']
    
    return result


@jobQuery.field('getSimilarJobsByJob')
def get_similar_jobs_by_job(_, info, job_title: str, job_publisher: str, industry: str = "HR", top_k: int = 100, source: str = "redis"):
    result = {"job_list":[],'graph_url':""}
    
    if source == "redis":
        result = job_service.getSimilarJobsByJob_Redis(job_title, job_publisher, industry, top_k) 
    elif source=='graph':
        result = job_service.getSimilarJobsByGraph(job_title, job_publisher, top_k)
    
    return result


@jobQuery.field('getSimilarCandidatesByCand')
def get_candidates_by_profile(_, info,  name: str, resume: str = "", industry: str= "HR", top_k: int = 100, source: str = "redis"):
    result = {"candidates":[],'graph_url':""}
    if source == "redis":
        result = job_service.getSimilarCandidatesByCandidate(name, resume, industry, top_k)
    elif source=='graph':
        result = job_service.getSimilarCandidatesByGraph(name, resume, top_k)
    
    return result 


@jobQuery.field('getJobStates')
def getJobStates(_, info):
    result = job_service.getJobStates()
    return result 


