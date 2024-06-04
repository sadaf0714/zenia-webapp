from filecmp import cmp
from subprocess import call
from unittest import result
from fastapi import FastAPI, HTTPException
from fastapi import File, UploadFile
import requests
import json
from ariadne import QueryType
from pydantic import BaseModel
from typing import List
from config.log_config import get_logger
from services import similarity_service, graphdb_service, redis_service, crawler_service, url_crawler_service,syncRedisDB, insurance_plan, reconciliation
from config.util import handle_similar_result, classify_text, array_to_comma, multiple_array_to_comma, config_query, config_graph_query, create_rdf_data, arrange_fields_output, construct_query_gpt, encodeURIComponent, parse_json_response, getSparqlConstructQueryForAttributesWithCompaniesList, split_full_name, getSparqlSelectQueryForAttributesWithCompaniesList, config_graph_query_for_claim_similarity, config_graph_query_redis, config_query_event, get_plans_construct_query, get_plans_construct_query_post
from typing import Optional
import random
from config.constant import DEFAULT_GRAPHDB_REPO, GRAPHDB_VISUAL_GRAPH, GRAPHDB_SERVICE, GRAPHQL_SERVICE, REDIS_SERVICE_URL, STANDARD_COMP_FIELDS, EMBEDDING_SERVICE_URL, STANDARD_COMP_FIELDS_LINKEDIN, STANDARD_COMP_FIELDS_DBPEDIA, RAPID_LINKEDIN_API, RAPID_API_KEY, LINKEDIN_RAPID_STATUS, EXT_GRAPHQL_SERVICE_HTTP_URL, EXT_VECTOR_SERVICE_HTTP_URL, EXT_REDIS_SERVICE_HTTP_URL, GRAPHDB_SERVICE_SHOWKG_HTTP_URL, allianzTravelCoverages, METAPHACTORY_URL
import asyncio
import uuid
import pdfplumber
import io

query = QueryType()


class newList(BaseModel):
    vectors: List[List[str]]


@query.field("getSimilaritySentences")
def resolve_get_similar_sentences(_, info, name: str, top_k: int, platform_type: str, classifications: dict, company_type: list, revenue: dict):

    if name and any(key in classifications and classifications[key] for key in ['location', 'industry', 'person', 'organization']):
        # get embedding vectors of search term
        try:
            search_term_vector = similarity_service.get_embedding(
                name, platform_type)
        except Exception as e:
            raise Exception('Similarity not found')

        text_classification = classifications

    elif not name and any(key in classifications and classifications[key] for key in ['location', 'industry', 'person', 'organization']):
        name = " ".join(" ".join(values)
                        for values in classifications.values() if values)

        try:
            search_term_vector = similarity_service.get_embedding(
                name, platform_type)
        except Exception as e:
            raise Exception('Similarity not found')

        text_classification = classifications

    elif name and any(key in classifications and (classifications[key] is None or classifications[key] == []) for key in ['location', 'industry', 'person', 'organization']):
        # get embedding vectors of search term
        try:
            search_term_vector = similarity_service.get_embedding(
                name, platform_type)
        except Exception as e:
            raise Exception('Similarity not found')

        # get text classification
        try:
            text_classification = similarity_service.get_text_classification(
                name)
        except Exception as e:
            raise Exception('Similarity not found')
    else:
        raise Exception("Input is required")

    # pass embedding vectors and get the similar matches from redis server
    # store redis result here
    redis_results = similarity_service.redis_search(
        search_term_vector, top_k, platform_type, text_classification, company_type, revenue)
    # similarity_service.get_gpt_search(redis_results,name)
    records = similarity_service.get_gpt_search(redis_results, name)
    return records['data'] 


@query.field('getCompaniesByStatus')
def get_companies_by_status(_, info, company_list: list, query: str, case_type: str, codes: dict, events:list  = []):
    results = []
    try:
        if case_type == "normal":
            redis_companies_list = similarity_service.get_companies(company_list)
            companies_data = similarity_service.get_companies_by_status(query,redis_companies_list)

            # update status column in each company with the status value
            for info in redis_companies_list:
                info['status'] = companies_data.get(info['name'])
                company_list.remove(info['name'])

            if (len(company_list) > 0):
                for name in company_list:
                    redis_companies_list.append({"name": name,
                                                 'status': "NOT_CLASSIFIED"})

            results = redis_companies_list
        elif case_type == "classify":

            tmpArr = []
            classify_object = classify_text(query)
            
            # get active companies
            get_active_companies = (similarity_service.get_classified_companies(
                classify_object['active'], company_list, codes, events))
            if len(get_active_companies) > 0:
                for info in get_active_companies:
                    info['status'] = "ACTIVE"
                    tmpArr.append(info['name'])

            # get in-active companies
            get__inactive_companies = (similarity_service.get_classified_companies(
                classify_object['inactive'], company_list, codes, events))
            if len(get__inactive_companies) > 0:
                for info in get__inactive_companies:
                    info['status'] = "INACTIVE"
                    tmpArr.append(info['name'])

            if company_list != []:
                # Code starts to filter out the OTHER and NOT_CLASSIFIED companies
                remain_companies = []
                for comp_name in company_list:
                    if not comp_name in tmpArr:
                        remain_companies.append(comp_name)

                # getting companies list present in redis db
                in_redis_com = []
                others_com = []
                not_classfied_companies_filterd = []
                remain_companies_list_of_redis = []
                if len(remain_companies) > 0:
                    try:
                        remain_companies_list_of_redis = similarity_service.get_companies(remain_companies,events,codes)
                    except Exception as e:
                        pass

                    # for OTHERS companies
                    if len(remain_companies_list_of_redis) > 0:
                        for data in remain_companies_list_of_redis:
                            comp_name = data.get("name")
                            if comp_name in remain_companies :
                                dn_status = "OTHERS"
                                #if len(codes) > 0:
                                    #if codes.get('sic_code') != "":
                                        #dn_status = "NOT_CLASSIFIED"
                                    #if codes.get('naics_code') != "":
                                        #dn_status = "NOT_CLASSIFIED"

                                data["status"] = dn_status

                                in_redis_com.append(comp_name)
                                others_com.append(data)

                    # for not_classified companies
                    for name in remain_companies:
                        # comp_name = name.lower()
                        if not name in in_redis_com:
                            d = {"name": name, 'status': 'NOT_CLASSIFIED'}
                            not_classfied_companies_filterd.append(d)
                    # collective result of all three filterd types
                results = (get_active_companies + get__inactive_companies +
                       others_com + not_classfied_companies_filterd)

            elif company_list == []:
                all_compnies = similarity_service.get_companies(company_list, events, codes)
                all_compnay_list = []
                i =0
                j =0
                for x in all_compnies:
                    cmp_name = x['name']
                    all_compnay_list.append(cmp_name)
                    i=i+1
                    del cmp_name
                # print(f'''all_compnay_list: {all_compnay_list} \n i:{i}\n''')
                remain_companies = []
                for comp_name in all_compnay_list:
                    if not comp_name in tmpArr:
                        remain_companies.append(comp_name)
                        j = j+1
                # print(f'''remain_companies: {remain_companies} \n j:{j}\n''')

                # getting companies list present in redis db
                in_redis_com = []
                others_com = []
                remain_companies_list_of_redis = []
                if len(remain_companies) > 0:
                    try:
                        for x in all_compnies:
                            if x['name'] in remain_companies:
                                remain_companies_list_of_redis.append(x)
                    except Exception as e:
                        pass
                        #print(str(e))
                    # for OTHERS companies
                    if len(remain_companies_list_of_redis) > 0:
                        for data in remain_companies_list_of_redis:
                            comp_name = data.get("name")
                            if comp_name in remain_companies :
                                dn_status = "OTHERS"
                                data["status"] = dn_status
                                in_redis_com.append(comp_name)
                                others_com.append(data)
                results = (get_active_companies + get__inactive_companies + others_com)
    except Exception as e:
        raise Exception(e)
        
    return results


@query.field('getSimilarCompaniesByName')
def similar_article_companies(_, info, name: str, platform_type: str = "HUGGINGFACE", field_name: str = 'lamma_embedding', similar_source: str = "redis", top_k: int = 10):
    
    results = []
    if(similar_source == "graph"):
        response = similarity_service.getSimilarCompaniesByGraph(name, top_k)
    else:
        response = similarity_service.getSimilarCompaniesByRedis(name, top_k, field_name, platform_type)
        
    if response.get('graph_url'):
        results.append(response)

    return results

@query.field('showGraphDbKg')
def show_graphdb_kg(_, info, company_list: list, event:list = []):
    results = []
    platform_type = "HUGGINGFACE"
    my_logger = get_logger("/showGraphDbKg")

    if (len(company_list) > 0):
        if event:
            visual_graph_url = config_query_event(company_list)
        else:
            visual_graph_url = config_query(company_list)
        results.append({"graph_url": GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"})

    return results

@query.field('showCompanySimilarityShowKg')
def showCompanySimilarityShowKg(_, info, company_list: list):
    results = {"graph_url":""}
    my_logger = get_logger("/showCompanySimilarityShowKg")
    if (len(company_list) > 0):
        visual_graph_url = config_graph_query_redis(company_list)
        results['graph_url'] =  GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"

    return results


@query.field('getCompaniesByCrawl')
def get_companies_by_crawl(_, info, data: dict):
    platform_type = "HUGGINGFACE"
    my_logger = get_logger("/getCompaniesByCrawl")
    results = {};
     
    if data:
        param_input = data.get('input')
        param_source = data.get('source')
        param_type =  "company" if data.get('type')=="" or data.get('type')== None else data.get('type') 
         
        if param_source=="linkedin":
            param_input = param_input.replace(' ', "-").lower()

        #check which type of crawling need to do
        if param_type == "company": 
            company_data = crawler_service.fetch_company_data({"name": param_input, 'source':param_source})
             
            # print(company_data)
        elif param_type == "url":  
            company_data = url_crawler_service.get_data_from_url(param_input)
        
        results['source'] = param_source
        if company_data.get('data') != None and type(company_data.get('data')) is dict:
            if company_data.get('data').get('name') != "":
                results = arrange_fields_output(company_data.get('data'), param_source)
                
                #if param_source == "linkedin" or param_source == "dbpedia" or param_source == "yahoo_finance":
                #fetch parent_name from graphdb of given company
                cmp_name = company_data.get('data').get('name')
                if param_source == "yahoo_finance":
                    cmp_name =  results['ticker_symbol']
                graph_company_info = graphdb_service.fetch_company_info({"repositoryID":DEFAULT_GRAPHDB_REPO,'name': cmp_name,'source':param_source})
                if graph_company_info.get('result') :
                    results['parent_name'] =  graph_company_info['result']['parent_name']
                    results['graph_data'] = graph_company_info['result'];
                else:
                    results['parent_name'] =  cmp_name
                 
    if results: 
            for var in results:     
                if results[var] != "" and type(results[var]) == str :
                    results[var] =  results[var].strip()

    return results

@query.field('getEnvVariables')
def getEnvVariables(_, info):
    return [{
        "graph_db_url": GRAPHDB_SERVICE,
        "graph_db_visual_url": GRAPHDB_SERVICE_SHOWKG_HTTP_URL,
        "default_repo": DEFAULT_GRAPHDB_REPO,
        "graphql_service": EXT_GRAPHQL_SERVICE_HTTP_URL,
        "redis_service": EXT_REDIS_SERVICE_HTTP_URL,
        "vector_service": EXT_VECTOR_SERVICE_HTTP_URL,
        "standards_fields": STANDARD_COMP_FIELDS,
        "standards_fields_linkedin": STANDARD_COMP_FIELDS_LINKEDIN,
        "standards_fields_dbpedia": STANDARD_COMP_FIELDS_DBPEDIA,
        "metaphactory_url":METAPHACTORY_URL
    }]

@query.field('getCompany')
def get_single_company(_, info, name: str):
     
    my_logger = get_logger("/get_single_company")
    results = {};
     
    if name :
        comp_data = {}
        get_company_info =  similarity_service.get_companies_list([name])
        if len(get_company_info.get('data')) > 0 and get_company_info.get('success') == True:
            for info in get_company_info.get('data'):
                if name==info.get('name') :
                    results = arrange_fields_output(info)
    return results

@query.field('sparqlGPTSearch')
def sparql_query_result(_, info, input: str, sparql_query: str = None):
    result={'records':None,'error':None, 'graph_url':None}
    response = {'sparql_query': None, 'error': None}
    if sparql_query == None:
        response=similarity_service.get_sparql_query(input)
    else:
        response['sparql_query'] = sparql_query
    if response['error'] == None:
        response['sparql_query'] = response['sparql_query'].replace("'''",'')
        query = construct_query_gpt(response['sparql_query'])
        response['sparql_query'] = response['sparql_query'].replace("\n", " ").replace("'''",'')
        loginReponse  = graphdb_service.login() 
        resp=graphdb_service.execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(response['sparql_query']), "token": loginReponse.get('token')})
        if resp['error'] == None:
            result['records']=parse_json_response(resp['result'])
        else:
            result['error']=resp['error']
        if result['records'] != None and len(result['records']) > 0:
            result['graph_url']=GRAPHDB_VISUAL_GRAPH + query+"&sameAs&inference"
    else:
        result['error']=response['error']
        
    return result

@query.field('showKgWithAttributes')
def showkg_With_Attributes(_, info, company_list: list, attributes_list: list):
    results = {}
    
    if (len(company_list) > 0 and len(attributes_list) > 0):
        sparqlQuery=getSparqlConstructQueryForAttributesWithCompaniesList(company_list,attributes_list)
        results['graph_url'] =  GRAPHDB_VISUAL_GRAPH + sparqlQuery+"&sameAs&inference"
        
    elif (len(company_list) > 0):
        visual_graph_url = config_query(company_list)
        results['graph_url'] =  GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"

    return results

@query.field('GetContactsFromGraphDB')
def GetContactsFromGraphDB(_, info, company: str):
    results = {}
    
    if company:
        query = f'''
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
                select DISTINCT ?name ?occupation ?social_url ?description ?source  where {{
                        ?company a dbo:Organisation ;
                            dbo:source ?data .
                        ?data dbo:source ?source .
                ?data dbo:employees [dbo:employee ?employee] .
                        ?employee rdfs:label ?name .
                        OPTIONAL {{?employee vcard:experiences [vcard:experience_details [
                            dbo:role ?occupation; dbo:is_current "True" ] ].  }}
                        OPTIONAL {{?employee dbo:description ?description .}}
                    
                        bind(?employee as ?social_url )
                        
                        FILTER (?company IN (<https://company.org/resource/{encodeURIComponent(company)}>))
                }}'''
        
        query = encodeURIComponent(query)
        loginReponse  = graphdb_service.login() 
        queryResponse = graphdb_service.execute_sparql_query({"token":loginReponse.get('token'), "repositoryID":DEFAULT_GRAPHDB_REPO, "query":query})
        
        data = queryResponse['result']['results']['bindings'];
        records = [];
        if len(data) > 0:
            for item in data:
                first_name, last_name = split_full_name(item['name']['value'])
                
                records.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "occupation": item['occupation']['value'] if "occupation" in item else  "",
                    "social_url": item['social_url']['value'] if "social_url" in item else "",
                    "description": item['description']['value'] if "description" in item else "",
                    "source": item['source']['value']
                })             
        results['records'] = records;       

    return results

@query.field('getGraphResultsByNLPQuery')
def getGraphResultsByNLPQuery(_, info, input: str):
    result={'records':None,'error':None, 'graph_url':None}
    response=similarity_service.get_classified_result(input)
    if response['error'] == None:
        company_list=[{"company_name": item} for item in response['entities']]
        attributes_list=response['attribute']
        
        if (len(company_list) > 0 and len(attributes_list) > 0):
            construct_query=getSparqlConstructQueryForAttributesWithCompaniesList(company_list,attributes_list)
            result['graph_url'] =  GRAPHDB_VISUAL_GRAPH + construct_query+"&sameAs&inference"
            select_query=getSparqlSelectQueryForAttributesWithCompaniesList(company_list,attributes_list)
            loginReponse  = graphdb_service.login() 
            resp=graphdb_service.execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(select_query), "token": loginReponse.get('token')})
            if resp['error'] == None:
                result['records']=parse_json_response(resp['result'])
            else:
                result['error']=resp['error']
       
        elif (len(company_list) > 0):
            visual_graph_url = getSparqlConstructQueryForAttributesWithCompaniesList(company_list,[])
            result['graph_url'] =  GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
            result['records'] = company_list

    
    return result


@query.field('getAutoSuggestions')
def getAutoSuggestions(_, info, input: str, source: str):
    result= []
    my_logger = get_logger("/getAutoSuggestions")
    if source == "yahoo_finance":
        try:
            headers =  {
                "Origin":"https://finance.yahoo.com",
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"                
            }
            response = requests.get(f'https://query1.finance.yahoo.com/v1/finance/search?q={input}&quotesCount=10', headers = headers, verify=False)
            if response.status_code == 200 :
                results = response.json()
                if len(results['quotes']) > 0:
                    for info in results['quotes']:
                        result.append({"name": info['shortname'], "value": info['symbol']})    
        except Exception as e:
            my_logger.info(e)
    elif source =="dbpedia":
        try:
            headers =  {
                "Host":"lookup.dbpedia.org",
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"                
            }
            response = requests.get(f'https://lookup.dbpedia.org/api/search?maxResults=10&format=JSON&query={input}', headers = headers, verify=False)
            if response.status_code == 200 :
                results = response.json()
                if len(results['docs']) > 0:
                    for info in results['docs']:
                        label = info['label'][0].replace("<B>","")
                        label = label.replace("</B>","")
                        result.append({"name": label, "value": info['resource'][0]})    
        except Exception as e:
            my_logger.info(e)
    elif source =="linkedin":
             
            if LINKEDIN_RAPID_STATUS == "1":
                headers = {
                    'X-RapidAPI-Key': RAPID_API_KEY,
                    'X-RapidAPI-Host': 'linkedin-public-search.p.rapidapi.com',
                    'Content-Type': 'application/json',
                    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                    "Host":"linkedin-public-search.p.rapidapi.com"
                }
                try:
                    response = requests.get(f'{RAPID_LINKEDIN_API}?keyword={input}&page=1', headers=headers, data={})
                    if response.status_code == 200 :
                        records = response.json()
                        if len(records['result']) > 0:
                            all_records = records['result']
                            for info in all_records:
                                tmp_data = info['profileURL'].split('https://www.linkedin.com/company/')
                                cmp_name = tmp_data[1].replace('/', '')
                                result.append({"name": info['companyName'], "value": cmp_name})    
                except Exception as e:
                    my_logger.info(e)
            else:
                #get from redisdb keys
                data = {
                    "field":"name",
                    "source":["linkedin"],
                    "value": input
                }
                try:
                    response = requests.post(f'{REDIS_SERVICE_URL}/redis/api/get-crawl-name-suggestion', data = json.dumps(data))
                    if response.status_code == 200 :
                        results = response.json()
                        if len(results) > 0:
                            for info in results:
                                result.append({"name": info, "value": info})    
                except Exception as e:
                    my_logger.info(e)         
    return result


@query.field('getAllEvents')
def getAllEvents(_, info):
    result = []
    result = graphdb_service.get_all_events()
    return result


@query.field('getSimilarClaims')
def getSimilarClaims(_, info, claimId: str, vector_field_name: str = 'openai_embedding', top_k: int = 10):
    
    result = {"claims":[],'graph_url':""}
    response = similarity_service.getSimilarClaimsByRedis(claimId, top_k, vector_field_name)

    if 'records' in  response:
        if len(response['records']) > 0:
            for item in response['records']:
                temp = "{:.4f}".format(float(item.get("vector_score", "")))
                item['vector_score'] = temp
                item['entity'] = "http://insurance.org/claim/"+item['claimID']
                
            top_results = response['records'][:10]
            visual_graph_url = config_graph_query_for_claim_similarity(top_results)
            result['graph_url'] = GRAPHDB_VISUAL_GRAPH + visual_graph_url+"&sameAs&inference"
            result['claims'] = response['records']   
    return result

@query.field('getSimilarClaimsByGraph')
def getSimilarClaimsByGraph(_, info, claimId: str, top_k: int = 200):
    result = {"claims":[],'graph_url':""}
    if claimId:
        response = similarity_service.getSimilarClaimsByGraph(claimId, top_k)
        if len(response['claims']) > 0:
            result = response
    
    return result

@query.field('sparqlGPTSearchForClaims')
def sparql_claims_query_result(_, info, input: str):
    result={'records':None,'error':None, 'graph_url':None}
    response = {'sparql_query': None, 'error': None}
   
    response=similarity_service.get_sparql_query_for_claims(input)
    if response['error'] == None:
        loginReponse  = graphdb_service.login() 
        resp=graphdb_service.execute_sparql_query({"repositoryID": "assurant_poc", "query": encodeURIComponent(response['sparql_query']), "token": loginReponse.get('token')})

        if resp['error'] == None:
            result['records']=parse_json_response(resp['result'])
        else:
            result['error']=resp['error']
        
    else:
        result['error']=response['error']
        
    return result

@query.field('searchCompaniesByKeywords')
def searchCompaniesByKeywords(_,info,keyword:str):
    results = {'companies':[]}
    if keyword:
        list_of_companies = graphdb_service.findCompaniesByKeyword(keyword)
        if len(list_of_companies) > 0:
            results['companies'] = list_of_companies
    return results;

@query.field('searchPersonsByKeywords')
def searchPersonsByKeywords(_,info,keyword:str):
    results = {'persons':[]}
    if keyword:
        list_of_persons = graphdb_service.findPersonsByKeyword(keyword)
        if len(list_of_persons) > 0:
            results['persons'] = list_of_persons
    return results;

@query.field('getInsurancePlans')
def getInsurancePlans(_, info, agentName:str, agentEmail:str, travellers:list, endDate:str,primaryDestination:str, startDate:str, stateResidence
:str, totalTripCost:str):
    my_logger = get_logger("/getInsurancePlans")
    result = {"plans":[],'graph_url':"", "params":{}}
    result['params']  =  {
        "agentEmail": agentEmail,
        "agentName":agentName,
        "travellers":travellers,
        "endDate":endDate,
        "primaryDestination":primaryDestination, 
        "startDate":startDate, 
        "stateResidence":stateResidence, 
        "totalTripCost":totalTripCost
    }
    # add plan 1
    isTravelAllianzPlan = insurance_plan.getAllianzTravelPlan(result['params'])
    if isTravelAllianzPlan:
        result['plans'].append(isTravelAllianzPlan)
 
    # add plan 2
    isTravelGuardPlan = insurance_plan.getTravelGuardPlan(result['params'])
    if isTravelGuardPlan:
        result['plans'].append(isTravelGuardPlan)


    if len(result['plans']) > 0:
        graph_data = {"input_info": result['params'], 'plans':result['plans']}
        graphdbResponse = insurance_plan.insertDataIntoGraphDBRest(graph_data)
        
        if "success" in graphdbResponse:
            result['graph_url'] = GRAPHDB_VISUAL_GRAPH + get_plans_construct_query(result['plans']) +"&sameAs&inference"   
        
        #Call the extraction function asynchronously
        asyncio.create_task(insurance_plan.data_extraction({'plans':result['plans'],"input_info": result['params']}))

        #run query in graphdb to check summary exists or not
        checkSummaryStatus = insurance_plan.getSummaryStatus(result['plans'])
        if str(result['plans'][0]['productId']) not in checkSummaryStatus:
            #Call the summarization allianza function asynchronously
            asyncio.create_task(insurance_plan.getLangChainSummarization(result['plans'][0]))

        if str(result['plans'][1]['productId']) not in checkSummaryStatus:
            #Call the summarization travelGuard function asynchronously
            asyncio.create_task(insurance_plan.getLangChainSummarization(result['plans'][1]))

    return result

@query.field('compareInsurancePlans')
def compareInsurancePlans(_, info, plans:dict, inclusions: list):
    result = {"plans": plans,'graph_url':"", "bestPlan": dict}

    if len(result['plans']) > 0:  
        # get the inclusions
        for item in result['plans']:
            item['inclusions'] = []
            item['exclusions'] = []
            item['allAvailableInclusions'] = []
            if item['carrier'] == "https://www.allianztravelinsurance.com":
                quote = item['quote']
                for coverage in allianzTravelCoverages:
                    cov = {}
                    cov["coverageName"] = coverage['id']
                    #Extracting coverage amount using openai (gpt-3.5-turbo)
                    cov['coverageAmount'] = insurance_plan.find_coverage_amount_by_coverage_name(coverage["coverageName"],quote) if coverage['coverageName'] != "" else ""
                    # cov['coverageDetails'] = []
                    item['inclusions'].append(cov)
                    if cov['coverageAmount'] != "" and cov['coverageAmount'] != None and cov['coverageAmount'] != "0":
                        item['allAvailableInclusions'].append(cov['coverageName'])
            if "https://www.travelguard.com" in item['carrier']:
                travelGuardPlanPDFUrl = item["pdfUrl"]
                item['inclusions'] = insurance_plan.extractCoverageAmountUsingGpt(travelGuardPlanPDFUrl)
                for inc in item['inclusions']:
                    if inc['coverageAmount'] != "" and inc['coverageAmount'] != None and inc['coverageAmount'] != "0":
                        item['allAvailableInclusions'].append(inc['coverageName'])
        
        
        #get inclusions exclusions from graphdb for plans
        getInclusionsExclusionAndSummaryForPlans = insurance_plan.getInclusionExclusionSummaryForAllPlansFromGraphDB(result['plans'])
        result['plans'] = getInclusionsExclusionAndSummaryForPlans['plans']

        #If any plan doesn't contain any inclusion from the input inclusion list then this statement will remove that plan
        filteredPlans = [plan for plan in result['plans'] if all(elem in plan['allAvailableInclusions'] for elem in inclusions)]
        
        if len(filteredPlans) == 1:
            result['bestPlan'] = filteredPlans[0]
            bestPlanWithReason = insurance_plan.getTheReasonForBestPlan(result['bestPlan'], result['plans'])
            result['bestPlan'] = bestPlanWithReason['bestPlan']
        elif len(filteredPlans) > 0:
            bestPlan = insurance_plan.getBestPlan2(filteredPlans)
            if bestPlan['error'] == None:
                result['bestPlan'] = bestPlan['best_plan']
                
                #Addeding bestPlan by bestplanID
                for item in result['plans']:
                    if result['bestPlan']['productId'] == item['productId']:
                        result['bestPlan'] = item

                bestPlanWithReason = insurance_plan.getTheReasonForBestPlan(result['bestPlan'], result['plans'])
                result['bestPlan'] = bestPlanWithReason['bestPlan']
            else:
                result['error'] = bestPlan['error']
        else:
            result['bestPlan'] = {}
        
        result['graph_url'] = GRAPHDB_VISUAL_GRAPH + get_plans_construct_query_post(result['plans']) +"&sameAs&inference"
    else:
        result['error'] = "Input is not correct"
     
    return result

@query.field('searchAllCompaniesByKeywords')
def searchAllCompaniesByKeywords(_,info,keyword:str):
    results = {'companies':[]}
    if keyword:
        list_of_companies = graphdb_service.findCompaniesByKeywordWithSource(keyword)
        if len(list_of_companies) > 0:
            results['companies'] = list_of_companies
    return results;



@query.field("reconcileEntities")
def reconcileEntities(_, info, company:str):
    post_dict = []
    if company:
        queries = {}
        for i, company in enumerate(company):
            query_key = f"q{i + 1}"
            query = {
                "query": company['name'],
                "properties": [
                    {
                        "pid": "headquarters",
                        "v": company['headquarters']
                    }
                ],
                "type_strict": "should"
            }
            queries[query_key] = query
        post_dict = reconciliation.reconcile_entities(queries)
    return {"records": post_dict}

# functions to call shortest path endpoints in vector embedding repo
@query.field('callShortestPathEnpoints')
def call_shortest_path_endpoints(_, info, method:str,input:dict):
    result = {"records":{}}
    url = EMBEDDING_SERVICE_URL +"/embedding/api/"+ method
    print("Hitting the API : ",url)

    body = json.dumps(input)

    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=body)
    result['records'] = response.json()['data']
    return result

 
# function to call all redis endpoints in vector-redis repo 
@query.field('callRedisEnpoints')
def call_redis_endpoints(_, info, method:str,input:dict):
    result = {"records":{}}
    
    #  ask about urls shetan ji 
    url = REDIS_SERVICE_URL +"/redis/api/"+ method
    print("Hitting the API : ",url)
    body = input
    headers = {
        'Content-Type': 'application/json'
    }
    # JOBS - Similar Job by Job
    if method == "get-job-by-title":
        response = requests.request("POST", url, headers=headers, data=json.dumps(body))
        result['records'] = response.json()['data']
    # Classification and Similar Companies
    elif method == "get-name-suggestion":
        response = requests.request("POST", url, headers=headers, data=json.dumps(body))
        result['records'] = response.json()
    # JOBS - Recruiters get all jobs
    elif method == "get-all-jobs-from-redis":
        response = requests.request("GET",url,headers=headers, params=body)
        result['records'] = response.json()['data']
    # JOBS - Candidates get all candidates
    elif method == "get-all-candidate-from-redis":
        response = requests.request("GET", url, headers=headers, params=body)
        result['records'] = response.json()['data']
    # Insurance Claims - Classification filter
    elif method == "get-all-claims":
        response = requests.request("GET", url, headers=headers, data=body)
        result['records'] = response.json()['data']
    else:
        print("Invalid Response",method)
        result['records'] = {"InvalidMethodError":method}
    return result

@query.field('callEmbeddingEndpoints')
def callEmbeddingEndpoints(_, info, method:str, input:dict):
    result = {"records":{}}
    url = EMBEDDING_SERVICE_URL +"/embedding/api/"+ method
    body = input
    if method == "getClassifiedDataFromURL":
        headers = {
           'Content-Type': 'application/json' 
        }
        response = requests.request("POST", url, headers=headers, data=json.dumps(body))
        result['records'] = response.json()
    
    return result
