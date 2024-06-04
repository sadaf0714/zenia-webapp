from fastapi import FastAPI, HTTPException
from config.log_config import get_logger
import requests
import json
from config.util import encodeURIComponent, get_proper_urls, decodeComponent, split_full_name, array_to_comma, clean_description, clean_name, config_graph_query_candidates, config_graph_query_jobs
from typing import List
from pydantic import BaseModel
from config.constant import GET_REDIS_JOB, REDIS_ENDPOINT, GET_REDIS_CANDIDATE, GRAPHDB_VISUAL_GRAPH, HR_USECASE_JOB_REPO, GRAPHDB_SIMILARITY_INDEX_NAME
from services import graphdb_service, similarity_service


def get_job_list(params : dict) :
    response = {'error':None, 'result':[]} 

    query = f'''
        PREFIX saro: <http://w3id.org/saro#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT (CONCAT(?job_title," | Publisher: ",?publisher) AS ?title)
        WHERE{{
            ?job a saro:Job;
                rdfs:label ?job_title ;
                saro:job_publisher ?publisher .
        }}
    '''
    query = encodeURIComponent(query)
    queryResult = graphdb_service.execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':params['token']});
    if queryResult['result'] != None:
        records = [];
        if len(queryResult['result']['results']['bindings']) > 0:
            for item in queryResult['result']['results']['bindings']:
                records.append(item['title']['value'])                      
            response['result'] = records;                     
    else:
        response['error'] = queryResult['error']  

    return response

def get_job_by_title(params : dict):
    response = {'error':None, 'result':{}}
    job_title   = params['title'] 
    publisher   = params['publisher']
    query = f'''
                PREFIX saro: <http://w3id.org/saro#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>

                select ?job ?job_title ?job_description ?publisher ?job_employment_type  ?work_experience (group_concat(distinct ?skill;separator=",") as ?skills)
                where{{
                    ?job a saro:Job;
                        rdfs:label ?job_title ;
                        saro:job_publisher ?publisher .
                    OPTIONAL{{?job  saro:job_description ?job_description.}}
                    OPTIONAL{{?job  saro:job_employment_type ?job_employment_type .}}
                   
                    OPTIONAL{{?job    saro:minimum_work_experience ?work_experience .}}
                    OPTIONAL{{?job    saro:required_expertise_in ?skill .}}

                        FILTER( ?job_title="{job_title}" && ?publisher="{publisher}")


                }}
                group by ?job ?job_title ?job_description  ?publisher ?job_employment_type  ?work_experience 
                '''
    query = encodeURIComponent(query)
    queryResult = graphdb_service.execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':params['token']});
    
    if len(queryResult['result']['results']['bindings']) > 0:
        records = {};
        for item  in queryResult['result']['results']['bindings']:
            for key in item:
                records[key] = item[key]['value']                 
        response['result'] = records;                     
    else:
        response['error'] = queryResult['error']  

    return response

def get_candidates_by_job_title(params : dict):
    response = {'error':None, 'result':[]}
    skills   = params['skills']
    skills = skills.split(',')
    newArr = []
    for ele in skills:
        val = ele.strip()
        val = val.upper()
        newArr.append(val)
     
    all_skills_arr = array_to_comma(newArr)
    all_skills_arr  = all_skills_arr.replace(','," ")
    all_skills_arr  = all_skills_arr.replace(')',"")
    all_skills_arr  = all_skills_arr.replace('(',"")
     
    query = f'''
                PREFIX saro: <http://w3id.org/saro#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX dbp: <http://dbpedia.org/property/>
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
                PREFIX dbo: <http://dbpedia.org/ontology/>

                SELECT ?name ?company_name
                    (group_concat(distinct ?certificate;separator=", ") as ?certificates)
					(group_concat(distinct ?experience;separator=", ") as ?experience_in)
					(group_concat(distinct ?expertise1;separator=", ") as ?expertise_in)
                WHERE {{ 
                    VALUES ?expertiseHave {{ {all_skills_arr} }}
                    ?person a vcard:Individual ;
                        rdfs:label ?name.
                    optional{{?person  vcard:has_expertise_in [vcard:skill [rdfs:label ?expertise1]]}} .
                    optional{{?person  vcard:experience_working_details [vcard:worked_in [rdfs:label ?experience]] }}.
                    optional{{?person  vcard:has_certificate_details [vcard:certificate [rdfs:label ?certificate]] }}.
                    optional{{
                                ?company dbo:employer ?person;
                                rdfs:label ?company_name.
                            }}
                    FILTER(UCASE(?expertise1) IN (?expertiseHave))
                
                }}
                group by ?name ?company_name
                '''
    query = encodeURIComponent(query)
    queryResult = graphdb_service.execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':params['token']});
    if len(queryResult['result']['results']['bindings']) > 0:
        records = [];
        for item  in queryResult['result']['results']['bindings']:
            tmp_arr = {}
            for key in item:
                tmp_arr[key] = item[key]['value']                 
            records.append(tmp_arr)
        response['result'] = records;                     
    else:
        response['error'] = queryResult['error']  

    return response           

def get_candidates_list(params : dict) :
    response = {'error':None, 'result':[]} 

    query = f'''
        PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        select distinct (concat(?v1," | ", ?v2)as ?ca) ?candidate ?candidate_name ?graduated_in
        where{{
        ?candidate a vcard:Individual;
            rdfs:label ?candidate_name.
            optional{{?candidate vcard:graduated_in [rdfs:label ?graduated_in] .}}
            BIND(IF(BOUND(?candidate_name), ?candidate_name, "") AS ?v1)
            BIND(IF(BOUND(?graduated_in), ?graduated_in, "") AS ?v2)
        }}

    '''
    query = encodeURIComponent(query)
    queryResult = graphdb_service.execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':params['token']});
     
    if len(queryResult['result']['results']['bindings']) > 0:
        records = [];
        for item  in queryResult['result']['results']['bindings']:
            tmp_arr = {}
            for key in item:
                tmp_arr[key] = item[key]['value']                 
            records.append(tmp_arr)
        response['result'] = records;                     
    else:
        response['error'] = queryResult['error']  

    return response 

def get_candidate_by_name(params : dict):
    response = {'error':None, 'result':{}}
    name   = params['name'] 
    resume   = params['resume']
    query = f'''
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    select distinct ?name ?resume
                        (group_concat( distinct ?expertise1;separator=" , ") as ?skills) ?candidate 
                    where
                    {{
                        ?candidate a vcard:Individual;
                            rdfs:label ?name .
                        ?candidate vcard:resume ?resume . 
                        OPTIONAL{{ ?candidate  vcard:skills [vcard:expertise_details [vcard:skill [rdfs:label ?expertise1]]]}}.
                        FILTER(?name="{name}") 
                        FILTER(?resume = <{resume}>)
                    }}
                    group by ?candidate ?name ?resume 
                '''
     
    query = encodeURIComponent(query)
    queryResult = graphdb_service.execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':params['token']});
     
    if len(queryResult['result']['results']['bindings']) > 0:
        records = {};
        for item  in queryResult['result']['results']['bindings']:
            for key in item:
                records[key] = item[key]['value']                 
        response['result'] = records;                     
    else:
        response['error'] = queryResult['error']  

    return response

def get_jobs_by_candidate(params : dict):
    response = {'error':None, 'result':[]}
    skills   = params['skills']
    skills = skills.split(',')
    newArr = []
    for ele in skills:
        val = ele.strip()
        val = val.upper()
        newArr.append(val)
     
    all_skills_arr = array_to_comma(newArr)
    all_skills_arr  = all_skills_arr.replace(','," ")
    all_skills_arr  = all_skills_arr.replace(')',"")
    all_skills_arr  = all_skills_arr.replace('(',"")
     
    query = f'''
                PREFIX saro: <http://w3id.org/saro#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>

                select ?job_title ?job_description ?job_employment_type ?location ?work_experience ?company_name 
                                 (?job as ?appliy_link) ?publisher ?skill
                where{{
                    VALUES ?expertiseHave {{ {all_skills_arr} }}
                    ?job a saro:Job;
                        rdfs:label ?job_title .
                    ?job  saro:required_expertise_in ?skill .
                    OPTIONAL{{?job saro:job_publisher ?publisher.}}
                    OPTIONAL{{?job saro:job_description ?job_description.}}
                    OPTIONAL{{?job saro:job_employment_type ?job_employment_type .}}
                    OPTIONAL{{?job saro:job_location ?location .}}
                    OPTIONAL{{?job saro:minimum_work_experience ?work_experience .}}
                
                    OPTIONAL{{?company a dbo:Organisation;
                                    rdfs:label ?company_name;
                                    foaf:posted_job ?job .}}
                    FILTER(UCASE(?skill) IN (?expertiseHave))

                }}

                '''
    query = encodeURIComponent(query)
    queryResult = graphdb_service.execute_sparql_query({"repositoryID":params['repositoryID'],'query':query,'token':params['token']});
     
    if len(queryResult['result']['results']['bindings']) > 0:
        records = [];
        for item  in queryResult['result']['results']['bindings']:
            tmp_arr = {}
            for key in item:
                tmp_arr[key] = item[key]['value']                 
            records.append(tmp_arr)
        response['result'] = records;                     
    else:
        response['error'] = queryResult['error']  

    return response 

def get_weighted_result(summaryCandidates, categoryCandidates, wholeTextCandidates):
    categoryIdScore = {category['id']: category['vector_score'] for category in categoryCandidates}
    wholeTextIdScore = {wholeText['id']: wholeText['vector_score'] for wholeText in wholeTextCandidates}
    for summaryCandidate in summaryCandidates:
        vector_score_from_summary = float(summaryCandidate['vector_score'])
        vector_score_from_category = float(categoryIdScore.get(summaryCandidate['id']))
        vector_score_from_whole_text = float(wholeTextIdScore.get(summaryCandidate['id']))
    
        summaryCandidate['vector_score'] = (vector_score_from_summary*5 + vector_score_from_category*2 + vector_score_from_whole_text*3)/10

    results = sorted(summaryCandidates, key=lambda x: x['vector_score'], reverse=True)
    return results

def getSimilarCandidatesByJobFromRedis(job_title, job_publisher, industry, top_k):
    results = {"records":[], "error":None}
    try:
        # 1 consume redis service to get vector embedding
        redis_job = get_job_details_from_redis(job_title, job_publisher)
        if redis_job != [] and redis_job != None:
            if industry == "HR":
                vectorsForSummary = redis_job[0]['summary_embedding_jina']
                VectorsForCategory = redis_job[0]['category_embedding_openai']
                VectorsForJobDescription = redis_job[0]['job_desc_embedding']
                
                # 2 Sending summary vectors to redis search to get similar candidates based on candidates summary vectors
                similarCandidatesByJobs1 = redis_searchSimilarCandidatesByJobs(vectorsForSummary, "summary", industry, top_k)

                #Sending category vectors to redis search to get similar candidates based on candidates whole text vectors
                similarCandidatesByJobs2 = redis_searchSimilarCandidatesByJobs(VectorsForCategory, "category", industry, top_k)
                
                #Sending job description vectors to redis search to get similar candidates based on candidates whole text vectors
                similarCandidatesByJobs3 = redis_searchSimilarCandidatesByJobs(VectorsForJobDescription, "description", industry, top_k)
                
                if (len(similarCandidatesByJobs1) > 0):
                    for item in similarCandidatesByJobs1:
                        temp = 1-float(item.get("vector_score", ""))
                        temp = "{:.4f}".format(round(temp, 4))
                        item['vector_score'] = temp

                if (len(similarCandidatesByJobs2) > 0):
                    for item in similarCandidatesByJobs2:
                        temp = 1-float(item.get("vector_score", ""))
                        temp = "{:.4f}".format(round(temp, 4))
                        item['vector_score'] = temp
                
                if (len(similarCandidatesByJobs3) > 0):
                    for item in similarCandidatesByJobs3:
                        temp = 1-float(item.get("vector_score", ""))
                        temp = "{:.4f}".format(round(temp, 4))
                        item['vector_score'] = temp
                
                if len(similarCandidatesByJobs1) > 0 and len(similarCandidatesByJobs2) > 0 and len(similarCandidatesByJobs3) > 0:
                    results['records'] = get_weighted_result(similarCandidatesByJobs1, similarCandidatesByJobs2, similarCandidatesByJobs3)
                else:
                    results['error'] = "Similarity not found"

            elif industry == "hotel":
                Vectors = redis_job[0]['job_desc_embedding']
                #Sending job description vectors to redis search to get similar candidates based on candidates whole text vectors
                similarCandidatesByJobs = redis_searchSimilarCandidatesByJobs(Vectors, "description", industry, top_k)

                if (len(similarCandidatesByJobs) > 0):
                    for item in similarCandidatesByJobs:
                        temp = 1-float(item.get("vector_score", ""))
                        temp = "{:.4f}".format(round(temp, 4))
                        item['vector_score'] = float(temp)
                
                if len(similarCandidatesByJobs) > 0 :
                    results['records'] = similarCandidatesByJobs
                else:
                    results['error'] = "Similarity not found"

            else:
                results['error'] = "industry not found"
        else:
            results["error"] = "Job not found"
    except Exception as e:
        results['error'] = str(e)
    return results

def getSimilarJobsByCandidateFromRedis(name, resume, industry, top_k):
    results = {}
    try:
        # 1 consume redis service to get vector embedding
        redis_job = get_candidate_details_from_redis(name, resume)
        vectors = redis_job[0]['extracted_text_embedding']
            
        # 2 send that vectors to redis search to get similar companies
        similarJobsByCandidate = redis_searchSimilarJobsByCandidate(vectors, industry, top_k)
        if (len(similarJobsByCandidate) > 0):
            for item in similarJobsByCandidate:
                temp = 1-float(item.get("vector_score", ""))
                temp = "{:.4f}".format(round(temp, 4))
                item['vector_score'] = temp
            results['records'] = similarJobsByCandidate
    except Exception as e:
        results['error'] = e

    return results

def get_job_details_from_redis(job_title, job_publisher):
    my_logger = get_logger("/get-job-data")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to vector redis service to fetch JOB data
    try:
        response = requests.post(f'{GET_REDIS_JOB}', data = json.dumps({"job_title":job_title, "job_publisher": job_publisher}), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            return response.get('data')
        elif response.status_code == 404 :
            response = response.json()
            raise Exception(response.get('error'))
        else:
            raise Exception('No companies found')      
    except Exception as e:
        my_logger.error(e)
        raise Exception(e)

def get_candidate_details_from_redis(name, resume):
    my_logger = get_logger("/get-candidate-data")
    headers = {
        "Content-Type": "application/json"
    }
    #sending request to vector redis service to fetch CANDIDATE data
    try:
        response = requests.get(f'{GET_REDIS_CANDIDATE}', data = json.dumps({"name":name, "resume":resume}), headers = headers)
        if response.status_code == 200 :
            response = response.json()
            return response.get('data')
        elif response.status_code == 404 :
            response = response.json()
            raise Exception(response.get('error'))
        else:
            raise Exception('No companies found')      
    except Exception as e:
        my_logger.error(e)
        raise Exception(e)
    

def redis_searchSimilarCandidatesByJobs(search_vectors, vector_field, industry, top_k):
    my_logger = get_logger("/redis-similarity-search-for-candidatesByJob")

    data = {
            "vectors": search_vectors,
            "vector_field": vector_field,
            "industry": industry,
            "top_k": top_k
        }

    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_url = f'{REDIS_ENDPOINT}/get-candidates-by-job'
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

def redis_searchSimilarJobsByCandidate(search_vectors, industry, top_k):
    my_logger = get_logger("/redis-similarity-search-for-JobsByCandidate")

    data = {
            "vectors": search_vectors,
            "industry": industry,
            "top_k": top_k
        }

    headers = {
        "Content-Type": "application/json"
    }
    vector_embedding_url = f'{REDIS_ENDPOINT}/get-jobs-by-candidate'
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


def getSimilarJobsByJob_Redis(job_title, job_publisher, industry, top_k):
    results = {"job_list":[],'graph_url':""}
    try:
        # 1 consume redis service to get vector embedding
        redis_job = get_job_details_from_redis(job_title, job_publisher)      
        vectors = redis_job[0]['job_desc_embedding']
                
        # 2 send that vectors to redis search to get similar jobs
        similarJobs = redis_searchSimilarJobsByCandidate(vectors, industry, top_k)
        if (len(similarJobs) > 0):
            jobsTitles = []
            for item in similarJobs:
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
                for item in similarJobs:
                    for item_inner in getAllJobsURIs['result']['results']['bindings']:
                        if item_inner['name']['value'] == item['job_title']:
                            item['graph_uri'] = item_inner['s']['value']

            results['job_list'] = similarJobs
            top_results = similarJobs[:10]    
            visual_graph_url = config_graph_query_jobs(top_results)
            results['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"

            
    except Exception as e:
        print(e)
        pass

    return results

def getSimilarCandidatesByCandidate(name, resume, industry, top_k):
    results = {"candidates":[],'graph_url':""}
    try:
        # 1 consume redis service to get vector embedding
        redis_job = get_candidate_details_from_redis(name, resume)
        vectors = redis_job[0]['extracted_text_embedding']
                
        # 2 send that vectors to redis search to get similar jobs
        similarCandidates = redis_searchSimilarCandidatesByJobs(vectors, 'description', industry, top_k)
        if (len(similarCandidates) > 0):
            for item in similarCandidates:
                temp = 1-float(item.get("vector_score", ""))
                temp = "{:.4f}".format(round(temp, 4))
                item['vector_score'] = temp
            results['candidates'] = similarCandidates
            top_results = results['candidates'][:10] 
            visual_graph_url = config_graph_query_candidates(top_results)
            results['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
    except Exception as e:
        print(e)
        pass
    print(results['graph_url'])
    return results

def getSimilarCandidatesByGraph(name, resume , top_k):
     
    results = {"candidates":[],'graph_url':""}
    try:
        # 1. get access token
        loginResponse  = graphdb_service.login()
         
        # 2. get candidate detail by name
        candidateDetail = get_candidate_by_name({"token":loginResponse.get('token'),"name":name,'resume':resume,"repositoryID":HR_USECASE_JOB_REPO})
         
        if candidateDetail["result"]["name"]:
            candidateURI = candidateDetail["result"]["candidate"]
         
            # 3. we need to fetch the similar candidates from graphdb index
            similarCandidates = graphdb_service.run_query({"token":loginResponse.get('token'),"query":getSimilarFindCandidateSparQL(candidateURI,top_k),"repositoryID":HR_USECASE_JOB_REPO})
             
            if( len(similarCandidates["results"]["bindings"]) > 0):
                data = similarCandidates["results"]["bindings"]
                records = []
                for itemKey, item in enumerate(data):
                    temp = {}
                    for innerKey, innerItem in item.items():
                        if innerKey == "score":
                            innerKey = "vector_score"
                            score_value = float(innerItem['value'])
                            score_value = "{:.4f}".format(round(score_value, 4))
                            innerItem['value'] = score_value
                        temp[innerKey] = innerItem['value']
                    records.append(temp)   

                results['candidates']  = records

                top_results = results['candidates'][:10] 
                visual_graph_url = config_graph_query_candidates(top_results)
                
                results['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
                
    except Exception as e:
        print(e)
        pass

    return results

def getJobStates():
    result = {"most_applied_jobs":[],"job_applications":[]}
    # 1. get access token
    loginResponse  = graphdb_service.login()
     
    query1 = f'''PREFIX saro: <http://w3id.org/saro#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>

                select ?job ?job_title (count(?appliedBy) as ?appliers)
                where{{
                    ?job a saro:Job;
                        rdfs:label ?job_title ;
                        saro:appliedBy ?appliedBy .
                }}
                GROUP by ?job ?job_title
                        order by desc(?appliers )'''
    query1 = encodeURIComponent(query1)
    most_applied_job = graphdb_service.run_query({"token":loginResponse.get('token'),"query":query1,"repositoryID":HR_USECASE_JOB_REPO})
    
    if len(most_applied_job['results']['bindings']) > 0:
        data = most_applied_job['results']['bindings']
        for item in data:
            result['most_applied_jobs'].append({
                    'job_title':item['job_title']['value'],
                    'job_uri': encodeURIComponent(item['job']['value']),
                    'appliers':item['appliers']['value']
                 })

    query2 = f'''PREFIX saro: <http://w3id.org/saro#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix dbo: <http://dbpedia.org/ontology/>
                select distinct ?candidate (count(?job) as ?jobs) ?name 
                where
                {{
                    ?candidate a vcard:Individual .  
                    ?job a saro:Job;
                    saro:appliedBy ?candidate .
                    ?candidate rdfs:label ?name .
                    
                }}
                group by ?candidate ?name 
                order by desc(?jobs)'''
    query2 = encodeURIComponent(query2)
    job_applications = graphdb_service.run_query({"token":loginResponse.get('token'),"query":query2,"repositoryID":HR_USECASE_JOB_REPO})

    if len(job_applications['results']['bindings']) > 0:
        data2 = job_applications['results']['bindings']
        for item in data2:
            result['job_applications'].append({
                    'name':item['name']['value'],
                    'candidate_uri':encodeURIComponent(item['candidate']['value']),
                    'applied_jobs':item['jobs']['value']
                 })

    return result

def getSimilarFindCandidateSparQL(candidateUri, top_k):
     
    query =f'''
        PREFIX :<http://www.ontotext.com/graphdb/similarity/>
        PREFIX similarity-index:<http://www.ontotext.com/graphdb/similarity/instance/>
        PREFIX psi:<http://www.ontotext.com/graphdb/similarity/psi/>
        PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT ?entity ?score ?name ?category ?summary (group_concat(?skill;separator=",") as ?skills) ?resume ?label
        {{
            ?search a similarity-index:{GRAPHDB_SIMILARITY_INDEX_NAME} ;
                psi:searchEntity <{candidateUri}>;
                psi:searchPredicate <http://www.ontotext.com/graphdb/similarity/psi/any>;
                :searchParameters "-numsearchresults {top_k}";
                psi:entityResult ?result .
            ?result :value ?entity ;
                    :score ?score .
            ?entity a vcard:Individual .
            ?entity rdfs:label ?name .
            ?entity dbo:name ?label .
            optional{{ ?entity dbo:category ?category .}}
            optional{{ ?entity dbo:summary ?summary .}}
            optional{{?entity vcard:resume ?resume .}}
            optional{{ ?entity vcard:skills [vcard:expertise_details [vcard:skill [rdfs:label ?skill]]] .}}
        }}
        group by  ?entity ?score ?name ?category ?summary  ?resume ?label
                    
        '''
    return encodeURIComponent(query)
 

def getSimilarJobsByGraph(job_title, job_publisher, top_k):
    results = {"job_list":[],'graph_url':""}
    try:
        # 1. get access token
        loginResponse  = graphdb_service.login()
         
        # 2. get job detail by title and publisher
        jobDetail = get_job_by_title({"token":loginResponse.get('token'),"title":job_title,'publisher':job_publisher,"repositoryID":HR_USECASE_JOB_REPO})
         
        if jobDetail["result"]["job_title"]:
            jobUri = jobDetail["result"]["job"]
         
            # 3. we need to fetch the similar jobs from graphdb index
            similarJobs = graphdb_service.run_query({"token":loginResponse.get('token'),"query":getSimilarJobsSparql(jobUri,top_k),"repositoryID":HR_USECASE_JOB_REPO})
             
            if( len(similarJobs["results"]["bindings"]) > 0):
                data = similarJobs["results"]["bindings"]
                records = []
                for itemKey, item in enumerate(data):
                    temp = {}
                    for innerKey, innerItem in item.items():
                        if innerKey =="score":
                            innerKey = "vector_score"
                            score_value = float(innerItem['value'])
                            score_value = "{:.4f}".format(round(score_value, 4))
                            innerItem['value'] = score_value
                        if innerKey =="entity":   
                            temp['graph_uri'] = innerItem['value']
                        temp[innerKey] = innerItem['value']
                                               
                    records.append(temp)   

                results['job_list']  = records

                top_results = results['job_list'][:10] 
                visual_graph_url = config_graph_query_jobs(top_results)
                
                results['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
                
    except Exception as e:
        print(e)
        pass

    return results

def getSimilarJobsSparql(job_uri, top_k):
    query = f'''PREFIX :<http://www.ontotext.com/graphdb/similarity/>
        PREFIX similarity-index:<http://www.ontotext.com/graphdb/similarity/instance/>
        PREFIX psi:<http://www.ontotext.com/graphdb/similarity/psi/>
        PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
        PREFIX saro: <http://w3id.org/saro#>

        SELECT ?entity ?job_title ?score ?category ?summary ?minimum_work_experience ?job_publisher ?job_employment_type ?job_description (group_concat(?skill;separator=",") as ?skills)  
        {{
            ?search a similarity-index:{GRAPHDB_SIMILARITY_INDEX_NAME} ;
                psi:searchEntity <{job_uri}>;
                psi:searchPredicate <http://www.ontotext.com/graphdb/similarity/psi/any>;
                :searchParameters "-numsearchresults {top_k}";
                psi:entityResult ?result .
            ?result :value ?entity ;
                    :score ?score .
            ?entity a saro:Job ;
                rdfs:label ?job_title .
            ?entity saro:category ?category .
            ?entity saro:summary ?summary .
            optional{{ ?entity saro:minimum_work_experience ?minimum_work_experience .}}
            optional{{ ?entity saro:job_publisher ?job_publisher .}}
            optional{{ ?entity saro:job_description ?job_description .}}
            optional{{ ?entity saro:job_employment_type ?job_employment_type .}}
            optional{{ ?entity saro:required_expertise_in ?skill .}}
        }}
        group by ?entity ?job_title ?score ?category ?summary ?minimum_work_experience ?job_publisher ?job_employment_type ?job_description
                    
        '''
    return encodeURIComponent(query)

