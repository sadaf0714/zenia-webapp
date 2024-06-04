import re
import copy
import requests
import csv
from datetime import datetime, timezone
import os,json
from config.util import encodeURIComponent, is_item_in_second_array, arrange_fields_output, clean_description, personalize_company_name, clean_string
from services import graphdb_service, crawler_service, similarity_service, redis_service
from config.constant import DEFAULT_GRAPHDB_REPO
import sys
import shutil
from httpx_html import AsyncHTMLSession
from urllib.parse import quote
import time


eventTitle = "live.odsc.com"
#Constant Variables & Functions 
XRapidAPIKey = "d3271a7122msh3240b1dfdc749adp1b2c38jsnd4255e0cf576"
matchingKeywords = ["machine learning","ai","artificial intelligence",'ml','llm','nlp','graph','graph database','graphdb',
                    'Natural Language Processing (NLP)','Artificial Intelligence (AI)','Natural Language Processing','Generative AI',
                    'Large Language Model','AI Applications','Machine Learning (ML)','Deep Learning','AI Research',
                    'Machine Learning Algorithms','Neural Networks','NLP (Natural Language Processing)','AI Language Models']
matchingKeywords = [item.lower() for item in matchingKeywords]
 
async def run():
 
    func_result = {
        "states":{
            "total_names":[],
            "does_not_have_company_in_json":[],
            "profiles_link_not_found":[],
            'profiles_not_found_on_linkedin':[],
            "does_not_have_company_in_linkedin_api":[],
            #"profiles_skills_not_matched":[],
            "ingestible_data":[],
            "inserted_records": [], 
            'total_inserted': 0,
            "failed_records": [],
            'total_failed':  0
        }      
    }
 

    #--------- Get all users AND their company from JSON  -------#
    records  = []
    dir_path = os.path.abspath('./')
    full_path = os.path.join(dir_path, "contacts_lead_generation/live.odsc.com") 
    path_to_json =  os.path.join(full_path, 'total_users/')
    
    i = 1
    for file_name in [file for file in os.listdir(path_to_json) if file.endswith('.json')]:
        delete_file = {}
        with open(path_to_json + file_name) as json_file:
            data = json.load(json_file)
            func_result['states']['total_names'].append(data['user']['username'])
            user_dict = {
                "name":data['user']['name'],
                "username":"",
                "jobTitle":"",
                "company":"",
                "linkedin":""
            }
            if "linkedin" in data['user']:
                if data['user']['linkedin']:
                    user_dict['linkedin'] = data['user']['linkedin']
            if "username" in data['user']:
                if data['user']['username']:
                    user_dict['username'] = data['user']['username']
            if "customFields" in data['user']:
                if "jobTitle" in data['user']['customFields']:
                    user_dict['jobTitle'] = data['user']['customFields']['jobTitle']
                if "company" in data['user']['customFields']:
                    user_dict['company'] = data['user']['customFields']['company']
            i += 1
            if user_dict['name'] and user_dict['company']:
                records.append(user_dict)
            else:
                #move this file
                delete_file = {
                    "source":f"{path_to_json}{data['user']['username']}.json",
                    "destination":f"{full_path}/does_not_have_company_in_json/{data['user']['username']}.json"
                }
                func_result['states']['does_not_have_company_in_json'].append(data['user']['username'])

        if delete_file:
            move_file(delete_file['source'], delete_file['destination'])
         
        if i > 10:
            break 
    
    #--------- Get All Users Profile Link and Profile Data and Store in a List -------#
    allProfileData = [] 
    for item in records:
        profileLink  = ""
        if item['linkedin']:
            profileLink = item['linkedin']
        else:
            #get linkedin url from google crawling
            resp = await google_crawl(f"{item['name']} {item['company']} linkedin")
            if resp:
                profileLink = resp

        if profileLink:
            #print(profileLink)
            profileData  = fetchLinkedinProfileData(profileLink) 
            if profileData and 'full_name' in profileData:
                #fetch company linkedin url 
                if profileData['company_linkedin_url'] == "" or profileData['company_linkedin_url'] == None:
                    #if not company url then search on google
                    response = await findCompanyLinkedinUrl(profileData['company'])
                    if response:
                        profileData['company_linkedin_url'] = response
                
                if profileData['company'] and profileData['company_linkedin_url']:
                    if "linkedin.com/company/" in profileData['company_linkedin_url']:
                        split_linkedin_url = profileData['company_linkedin_url'].split('linkedin.com/company/')
                        actual_name_in_url = split_linkedin_url[1]
                        actual_name_in_url = actual_name_in_url.replace("/", "")
                        profileData['company_linkedin_url'] = f'https://www.linkedin.com/company/{actual_name_in_url}'    
                        profileData['json_username'] = item['username']
                        if len(profileData['experiences']) > 0:
                                expItemOrg = profileData['experiences'][0]
                                profileData['company'] = expItemOrg['company']
                                profileData['job_role_description'] = expItemOrg['description']
                                profileData['job_title'] = expItemOrg['title']
                                profileData['date_range'] = expItemOrg['date_range']
                                profileData['duration'] = expItemOrg['duration']
                                profileData['end_month'] = expItemOrg['end_month']
                                profileData['end_year'] = expItemOrg['end_year']
                                profileData['is_current'] = expItemOrg['is_current']
                                profileData['location'] = expItemOrg['location']
                                profileData['start_month'] = expItemOrg['start_month']
                                profileData['start_year'] = expItemOrg['start_year']
                                
                                allProfileData.append(profileData) #important line   
                                del profileData['experiences'][0]
                                    
                        #if user has multiple experiences
                        if len(profileData['experiences']) > 0:
                            for expItem in profileData['experiences']:
                                itemList = {}
                                itemList = copy.copy(profileData)  
                                itemList['company'] = expItem['company']
                                itemList['job_role_description'] = expItem['description']
                                itemList['job_title'] = expItem['title']
                                itemList['date_range'] = expItem['date_range']
                                itemList['duration'] = expItem['duration']
                                itemList['end_month'] = expItem['end_month']
                                itemList['end_year'] = expItem['end_year']
                                itemList['is_current'] = expItem['is_current']
                                itemList['location'] = expItem['location']
                                itemList['start_month'] = expItem['start_month']
                                itemList['start_year'] = expItem['start_year']

                                response = await findCompanyLinkedinUrl(expItem['company'])
                                if response:
                                    if "linkedin.com/company/" in response:
                                        split_linkedin_url_1 = response.split('linkedin.com/company/')
                                        actual_name_in_url_1 = split_linkedin_url_1[1]
                                        actual_name_in_url_1 = actual_name_in_url_1.replace("/", "")
                                        itemList['company_linkedin_url'] = f'https://www.linkedin.com/company/{actual_name_in_url_1}' 
                                        
                                        allProfileData.append(itemList) #important line    
                                     

                        func_result['states']['ingestible_data'].append(item['username'])
                    else:
                        move_file(f"{path_to_json}{item['username']}.json", f"{full_path}/does_not_have_company_in_linkedin_api/{item['username']}.json")
                        func_result['states']['does_not_have_company_in_linkedin_api'].append(item['username'])          
                else:
                    move_file(f"{path_to_json}{item['username']}.json", f"{full_path}/does_not_have_company_in_linkedin_api/{item['username']}.json")
                    func_result['states']['does_not_have_company_in_linkedin_api'].append(item['username'])      
            else:
                move_file(f"{path_to_json}{item['username']}.json", f"{full_path}/profiles_not_found_on_linkedin/{item['username']}.json")
                func_result['states']['profiles_not_found_on_linkedin'].append(item['username'])  
        else:
            move_file(f"{path_to_json}{item['username']}.json", f"{full_path}/profiles_link_not_found/{item['username']}.json")
            func_result['states']['profiles_link_not_found'].append(item['username'])  

     
    #--------- Filter out those users whose skills match with our pre-defined keywords ------- #
    #ingestible_data = []
    #if len(allProfileData) > 0:
        #for profile in allProfileData:
            #isSkillMatched = checkSkillStatus(profile)
            #if isSkillMatched == True:
                #ingestible_data.append(profile)
                #func_result['states']['ingestible_data'].append(profile['linkedin_url'])
            #else:
                #func_result['states']['profiles_skills_not_matched'].append(profile['linkedin_url'])


    ingestible_data = allProfileData
     
    #----------- Ingest data into GraphDB -----------#
    if len(ingestible_data) > 0:

        #add event in the graphdb first
        i = 1
        for profile in ingestible_data:
            print(f'process ID : {i}')
            #print(profile['company'])
            #print(profile['company_linkedin_url'])
            #first check if company exists or not in db
            description = ""
            json_username = profile['json_username'] 
            print(json_username)
            if profile['about'] != "" and profile['about'] != None:
                description =  clean_description(profile['about'])
            else:
                description =  clean_description(profile['headline'])

            graphAuth = graphdb_service.login()
            isCompanyExists = graphdb_service.is_company_exists_by_uri(profile['company_linkedin_url'],DEFAULT_GRAPHDB_REPO, graphAuth['token'])
            if isCompanyExists['status'] == True:
                params = {
                    "company": profile['company'],
                    'company_linkedin_url': profile['company_linkedin_url'],
                    "social_url": profile['linkedin_url'],
                    "first_name": profile['first_name'],
                    "last_name": profile['last_name'],
                    "full_name": profile['full_name'],
                    "description": description,
                    "occupation": profile['job_title'],
                    "start_month":profile['start_month'],
                    "start_year":profile['start_year'],
                    "end_month":profile['end_month'],
                    "end_year":profile['end_year'],
                    "duration":profile['duration'],
                    "date_range":profile['date_range'],
                    "job_role_description":profile['job_role_description'],
                    "is_current": profile['is_current'],
                    "skills":profile['skills'],
                    "languages":profile['languages'],
                    "location":profile['location']
                }
                    
                response = graphdb_service.addContactInLinkedinSource(params, DEFAULT_GRAPHDB_REPO, graphAuth['token'])
                if response['success'] == True:

                    #update event in graph
                    addedEventInGraphDb = addEventInGraphDB({
                        "linkedin_url": profile['linkedin_url'],
                        "title":eventTitle,
                        "parent_company":isCompanyExists['company_uri'],
                        "name": profile['full_name']
                    });
                    
                    #update event in redis
                    redis_response = updateEventInRedis({"name": isCompanyExists['parent_name'], 'new_event':clean_string(eventTitle)}) 

                    if redis_response['success'] == False:
                        #first insert company in redis
                        syncResponse = syncCompanyDataInRedis(isCompanyExists['company_uri'])
                        if syncResponse['success'] == True:
                            #again try update event in redis
                            redis_response = updateEventInRedis({"name": isCompanyExists['parent_name'], 'new_event':clean_string(eventTitle)}) 

                    move_file(f"{path_to_json}{json_username}.json", f"{full_path}/ingested_records/{json_username}.json")
                    func_result['states']['inserted_records'].append({
                        "json_username": json_username,
                        "status":"inserted_in_graphdb",
                        "parent_uri":isCompanyExists['company_uri'],
                        "company_name":profile['company'],
                        "company_url":profile['company_linkedin_url'],
                        "user_profile_link": profile['linkedin_url'],
                        "graphdb_event_status": True if addedEventInGraphDb['success'] == True else False,
                        "redis_event_status": True if redis_response['success'] == True else False,
                    })
                    func_result['states']['total_inserted'] +=  1
                else:
                    move_file(f"{path_to_json}{json_username}.json", f"{full_path}/failed_records/{json_username}.json")
                    func_result['states']['failed_records'].append({
                        "json_username": json_username,
                        "status":"failed_graphdb_insertion",
                        "company_name":profile['company'],
                        "company_url":profile['company_linkedin_url'],
                        "user_profile_link": profile['linkedin_url']
                    })
                    func_result['states']['total_failed'] += 1
            else:
                print(f'choreo process ID : {i}')
                #if company does not exists in db
                company_name = profile['company_linkedin_url'].split("linkedin.com/company/")
                company_data = crawler_service.fetch_company_data({"name": company_name[1], 'source':"linkedin"})
                if company_data.get('data') != None and type(company_data.get('data')) is dict:
                    if company_data.get('data').get('name') != "":
                        results = arrange_fields_output(company_data.get('data'), "linkedin")
                        new_company_data_set  = {}
                        new_company_data_set['parent_name'] = profile['company']
                        new_company_data_set['custom_properties']  =  results['custom_property']
                        new_company_data_set['employer']  =  []#results['employer'] 
                        new_company_data_set['social_url'] = results['social_url']
                        new_company_data_set['name'] = profile['company']
                        new_company_data_set['source'] = "linkedin"
                        new_company_data_set['description'] =  clean_description(results["description"])
                        new_company_data_set['headquarters'] =  results["headquarters"]
                        new_company_data_set['no_of_employees'] =  results["no_of_employees"]
                        new_company_data_set['company_type'] =  results["company_type"]
                        new_company_data_set['specialities'] =  results["specialities"]
                        new_company_data_set['industry'] =  results["industry"]
                        new_company_data_set['social_url'] =   profile['company_linkedin_url']
                        
                        if profile['is_current'] == True:
                            if  results['industry'] == "" or results['industry'] == None:
                                new_company_data_set['industry'] = profile['company_industry']
                            
                            if "founded" in results:
                                if  results['founded'] == "" or results['founded'] == None:
                                    new_company_data_set['founded'] = profile['company_year_founded']
                                else:
                                    new_company_data_set['founded'] = results['founded']
                            else:
                                new_company_data_set['founded'] = profile['company_year_founded']
                        else:
                            if "founded" in results:
                                if  results['founded'] == "" or results['founded'] == None:
                                    new_company_data_set['founded'] = ""
                                else:
                                    new_company_data_set['founded'] = results['founded']
                            else:
                                new_company_data_set['founded'] = ""

                        new_company_data_set['manual'] = "Yes"
                        
                        utctimenow = datetime.now(timezone.utc)
                        new_company_data_set['timestamp'] = utctimenow.strftime('%d-%m-%YT%T')
                        
                        #reset empployer object
                        new_company_data_set['employer'].append({
                            'occupation': profile['job_title'],
                            'social_url': profile['linkedin_url'],
                            'description': description,
                            'source': 'linkedin',
                            'first_name': profile['first_name'],
                            'last_name': profile['last_name'],
                            "start_month":profile['start_month'],
                            "start_year":profile['start_year'],
                            "end_month":profile['end_month'],
                            "end_year":profile['end_year'],
                            "duration":profile['duration'],
                            "date_range":profile['date_range'],
                            "employee_role_description":profile['job_role_description'],
                            "is_current": profile['is_current'],
                            "skills":profile['skills'],
                            "languages":profile['languages'],
                            "location":profile['location']
                        })

                        for item in new_company_data_set['employer']:
                            item['full_name'] = item['first_name'] + ' ' + item['last_name']
                            if item["occupation"] == None :
                                item["occupation"] = "" 
                            #del item['first_name']
                            #del item['last_name']
                        
                        #store data in graph and redis through choreo endpoint
                        print(f'choreo process start ID : {i}')
                        time.sleep(5)
                        print("new_company_data_set: ",new_company_data_set)
                        response = graphdb_service.insertCrwaledDataintoGraphDB(new_company_data_set)
                        print(f'choreo process request end ID : {i}')
                        if 'success' in response:
                            
                            fetchAddedCompanyInfo = graphdb_service.is_company_exists_by_uri(profile['company_linkedin_url'],DEFAULT_GRAPHDB_REPO, graphAuth['token'])   
                                
                            graphdb_event_status = False
                            redis_event_status = False
                            company_uri  = ""
                            if fetchAddedCompanyInfo['status'] == True:
                                company_uri = fetchAddedCompanyInfo['company_uri']
                                #update event in graph
                                addedEventInGraphDb = addEventInGraphDB({
                                    "linkedin_url": profile['linkedin_url'],
                                    "title":eventTitle,
                                    "parent_company":fetchAddedCompanyInfo['company_uri'],
                                    "name": profile['full_name']
                                });
                                    
                                #update event in redis
                                redis_response = updateEventInRedis({"name": fetchAddedCompanyInfo['parent_name'], 'new_event':clean_string(eventTitle)})

                                if redis_response['success'] == False:
                                    #first insert company in redis
                                    syncResponse = syncCompanyDataInRedis(company_uri)
                                    if syncResponse['success'] == True:
                                        #again try update event in redis
                                        redis_response = updateEventInRedis({"name": fetchAddedCompanyInfo['parent_name'], 'new_event':clean_string(eventTitle)})


                                graphdb_event_status = True if addedEventInGraphDb['success'] == True else False
                                redis_event_status = True if redis_response['success'] == True else False
                                

                            move_file(f"{path_to_json}{json_username}.json", f"{full_path}/ingested_records/{json_username}.json")
                            func_result['states']['inserted_records'].append({
                                "json_username": json_username,
                                "status":"inserted_in_graphdb_through_choreo",
                                "parent_uri": company_uri,
                                "company_name":profile['company'],
                                "company_url":profile['company_linkedin_url'],
                                "user_profile_link": profile['linkedin_url'],
                                "graphdb_event_status": graphdb_event_status,
                                "redis_event_status": redis_event_status
                            })
                            func_result['states']['total_inserted'] +=  1
                        else:
                            move_file(f"{path_to_json}{json_username}.json", f"{full_path}/failed_records/{json_username}.json")
                            func_result['states']['failed_records'].append({
                                "json_username": json_username,
                                "status":"failed_to_insert_through_choreo",
                                "company_name":profile['company'],
                                "company_url":profile['company_linkedin_url'],
                                "user_profile_link": profile['linkedin_url']
                            }) 
                            func_result['states']['total_failed'] += 1
                            
                    else:
                        move_file(f"{path_to_json}{json_username}.json", f"{full_path}/failed_records/{json_username}.json")
                        func_result['states']['failed_records'].append({
                            "json_username": json_username,
                            "status":"name_not_found_in_crawl_company_api",
                            "company_name":profile['company'],
                            "company_url":profile['company_linkedin_url'],
                            "user_profile_link": profile['linkedin_url']
                        }) 
                        func_result['states']['total_failed'] += 1
                else:
                    move_file(f"{path_to_json}{json_username}.json", f"{full_path}/failed_records/{json_username}.json")
                    func_result['states']['failed_records'].append({
                        "json_username": json_username,
                        "status":"failed_to_crawl_company_data",
                        "company_name":profile['company'],
                        "company_url":profile['company_linkedin_url'],
                        "user_profile_link": profile['linkedin_url']
                    }) 
                    func_result['states']['total_failed'] += 1
            i = i + 1         
    return func_result

def fetchNamesByKeyword(name):
    url = "https://linkedin-public-search.p.rapidapi.com/peoplesearch"
    headers = {
        'X-RapidAPI-Key': XRapidAPIKey,
        'X-RapidAPI-Host': "linkedin-public-search.p.rapidapi.com",
        'Content-Type': "application/json",
        "Access-Control-Allow-Origin":"*",
        "User-Agent":"PostmanRuntime/7.33.0"
    }
    querystring = {
        "keyword":name,
        "page":"1"
    }
    profileLinks = []
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            records = response.json()
            for item in records['result']:
                profileLinks.append(item['profileURL'])
    except Exception as e:
        pass
    
    return profileLinks

def fetchLinkedinProfileData(profileUrl):
    result  = {}
    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"
    headers = {
        'X-RapidAPI-Key': XRapidAPIKey,
        'X-RapidAPI-Host': "fresh-linkedin-profile-data.p.rapidapi.com",
        'Content-Type': "application/json",
        "Access-Control-Allow-Origin":"*",
        "User-Agent":"PostmanRuntime/7.33.0"
    }
    querystring = {
        "linkedin_url":profileUrl,
        "include_skills": 'true',
        "include_network_info": 'false'
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            record = response.json()
            result = record['data']
    except Exception as e:
        print(e)
        pass

    return result

def checkSkillStatus(profile):
    isMatched = False;
    if "skills" in profile:
        skills = profile['skills'].split('|')
        filtered_skills = list(filter(lambda item: item != "", skills))
        if filtered_skills:
            # Convert all elements to lowercase
            lowercase_skills = [item.lower() for item in filtered_skills]
            if is_item_in_second_array(matchingKeywords, lowercase_skills) and profile['company_linkedin_url']:
                isMatched = True
    
    return isMatched

def getNamesFromCSV():
    csvArr = []
    #--------- Get All Users From CSV and Removed the duplicate -------#
    with open('./csv_contacts_lead_generation/Webinar form Dataiku- Introducing the LLM Mesh 10-24-2023.csv', mode ='r') as file:
        # reading the CSV file
        csvFile = csv.reader(file)
        # Getting the contents of the CSV file
        for lines in csvFile:
            if len(lines) > 0:
                name = lines[0].replace('\x00', '').strip()
                if name not in csvArr:
                    #func_result['states']['total_names'].append(name)
                    csvArr.append(name)
    return csvArr

async def google_crawl(query):
    print(query)
    profile_link = ""
    asession = AsyncHTMLSession()
    try:
        results = await get_google(asession, query)
        if results:
            links = results.html.find('.pkphOe > div > a', first=True).links
            for result in links:
                if "linkedin.com" in result:
                    link = result.split('&url=')
                    if len(link) > 0:
                        link = link[1].split('&ved=')
                        profile_link = link[0]
    except Exception as e:
        print('error')
        print(e)
        pass
    print(profile_link)
    return profile_link

async def get_google(asession, query):
    page = 1 
    url = f"https://www.google.com/search?hl=en&q={quote(query)}" + (f"&start={10*(page-1)}" if page > 1 else "")
    r = ""
    try:
        r = await asession.get(url)
    except Exception as e:
        print(e)
        pass
    return r 

def move_file(source, destination):
    if os.path.exists(source):
        shutil.move(source, destination)

def addEventInGraphDB(event):
    event_title = event['title']
    parent_company = event['parent_company']
    linkedin_url = event['linkedin_url']
     

    login   = graphdb_service.login()
    rdfData = f'''
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix dbo: <http://dbpedia.org/ontology/> .
        @prefix event: <http://event.org/event/> .
        @prefix pro: <http://property.org/resource/> .

        <http://event.org/event/{clean_string(event_title)}> a dbo:Event;
            rdfs:label "{event_title}" ;
            dbo:participant <{parent_company}>, <{linkedin_url}> .
    '''
    data  = {
        "repositoryID" : DEFAULT_GRAPHDB_REPO,
        "rdfData" : rdfData,
        "token":login['token']
    }
    return graphdb_service.add_rdf_statement(data);

def updateEventInRedis(data):
    results = {"success":False}
    #first get all exists events from redis for that company
    response = similarity_service.get_companies_list([data['name']])
    if len(response['data']) > 0:
        company_data = response['data'][0]
        payload = {
            "events":""
        }
        if "events" in company_data:
            events = company_data['events']
            if events:
                events = events.split(',')
                events.append((data['new_event']))
                events = list(set(events))
                payload['events'] = ','.join(events)
            else:
                payload['events'] = data['new_event']
        else:
            payload['events'] = data['new_event']
        
        #INSERT OR UPDATE EVENTS IN REDIS COMP
        redis_resp =  redis_service.update_comp(company_data["id"], payload);
        print('redis event response')
        print(redis_resp)
        if redis_resp['success'] == True:
            results['success'] = True    
    return results
        
async def findCompanyLinkedinUrl(name):
    profile_link = ""
    query = f'{name} linkedin company'
    asession = AsyncHTMLSession()
    try:
        results = await get_google(asession, query)
        if results:
            links = results.html.find('.pkphOe > div > a', first=True).links
            for result in links:
                if "linkedin.com" in result:
                    link = result.split('&url=')
                    if len(link) > 0:
                        link = link[1].split('&ved=')
                        profile_link = link[0]
    except Exception as e:
        pass

    return profile_link

def syncCompanyDataInRedis(comParent_url):
    print(comParent_url)
    results = {"success":False}
    payload = {
        "query": "mutation syncCompanyData($comParent_url: [String], $isCrawl:Boolean!){\r\n    syncCompanyData(comParent_url: $comParent_url, isCrawl: $isCrawl){\r\n        record\r\n        error\r\n    }\r\n}",
        "variables": {"comParent_url":[comParent_url],"isCrawl":True}
    }
    headers = {
    'Content-Type': 'application/json'
    }
    url = "http://localhost:8000/graphql"
    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
       record = response.json()
       print(record)
       if "data" in record:
            if record['data'] and record['data'] != None:
                if "syncCompanyData" in record['data']:
                    if "record" in record['data']['syncCompanyData']:
                        if len(record['data']['syncCompanyData']['record']) > 0:
                            if record['data']['syncCompanyData']['record'][0]:
                                if record['data']['syncCompanyData']['record'][0]['success']:
                                    results['success'] = True
                  

    return results