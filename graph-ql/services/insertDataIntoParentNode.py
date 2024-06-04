# from tqdm import tqdm
import urllib.parse as urllp
import os
# import numpy as np
from datetime import datetime
from datetime import date
# import pandas as pd
# import redis
import sys
import requests
import urllib.parse as urllib
import re
import string
# HOST = '127.0.0.1'
#HOST = '34.207.82.200'
# ENV = "local"
from config.constant import (GRAPHDB_PASSWORD, GRAPHDB_SERVICE, GRAPHDB_USERNAME,DEFAULT_GRAPHDB_REPO)
# GRAPHDB_SERVICE = "http://127.0.0.1:7200"
#GRAPHDB_SERVICE = "http://34.207.82.200:7200"

# GraphDB Instance Username and Password
# GRAPHDB_USERNAME = 'admin'
# GRAPHDB_PASSWORD = '1234' #'root'

# # Default GraphDB Repository Name
# DEFAULT_GRAPHDB_REPO = "MASTER-REPO-V2"




def encodeURIComponent(s): return urllp.quote(
    s, safe='/', encoding=None, errors=None)



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

def update_sparql_query(params: dict):
    response = {'error': None, 'status': False}
    url = f"{GRAPHDB_SERVICE}/repositories/{params['repositoryID']}/statements?update={params['query']}"
    headers = {
        'Authorization': params['token']
    }
    try:
        resp = requests.request("POST", url, headers=headers)
        if resp.status_code == 200 or resp.status_code == 204:
            response['status'] = True
            
        else:
            response['error'] = "Data not found"
    except Exception as e:
        response['error'] = e
    return response


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
     optional{{ ?data foaf:parent_name ?parent_name . }}
     optional{{ ?data foaf:founded ?founded . }}
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
select ?parent_name ?revenue_dollar ?previous_year_revenue ?quarterly_growth ?annual_growth where {{ 
     ?company a dbo:Organisation; 
           dbo:source ?data . 
     ?data foaf:current_year_revenue ?revenue_dollar .
     ?data foaf:previous_year_revenue ?previous_year_revenue .
     optional {{ ?data foaf:quarterly_revenue_growth ?quarterly_growth. }}
     optional{{ ?data foaf:parent_name ?parent_name . }}
     optional {{ ?data foaf:annual_revenue_growth ?annual_growth. }}
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
select ?name ?parent_name ?description (GROUP_CONCAT(DISTINCT ?industryStr; SEPARATOR=", ") AS ?industry) ?headquarters ?no_of_employees ?founded_date  
where {{ 
    ?company a dbo:Organisation; 
            dbo:source ?data . 
    ?data dbp:name ?name .
    optional{{ ?data dbo:description ?description . }}
    optional{{ ?data dbo:industry ?industry . }}
    optional{{ ?data dbo:headquarters ?headquarters . }}
    optional{{ ?data dbo:no_of_employees ?no_of_employees . }}
    optional{{ ?data foaf:parent_name ?parent_name . }}
    optional{{ ?data foaf:founded ?founded_date . }}
    FILTER (?data IN (<{comp_url}>))
    
    BIND(IF(BOUND(?industry), STR(?industry), "") AS ?industryStr)
}}
group by ?name ?description ?parent_name ?headquarters ?no_of_employees ?founded_date
"""


get_parent_Comp_query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    select distinct ?company where { 
    	?company a dbo:Organisation .  
    } 
    ORDER BY (?company)
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


def insert_data_on_parent(com_url:list,isCrawl:bool):
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
    
    responsefromsource=gettingAllDatafromSources(comp_list,graphdb_login_res,b)
    return responsefromsource

# graphdb_login_res = login()

# # ------------------- Get Parent Company Name / List Here -------------------
# comp_list = []
# parent_resp = execute_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
#     get_parent_Comp_query), "token": graphdb_login_res.get('token')})
# for binding in parent_resp["result"]["results"]["bindings"]:
#     company_uri = binding["company"]["value"]
#     comp_list.append(company_uri)


# =========== current year ===========
# today = date.today()
# c_year = today.strftime("%Y")


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
                
                


# ----------------- For testing running for single company -------------
# comp_list =[]
# comp_list.append('https://company.org/resource/Adobe%20Inc.')


# ------------------- Get Parent Company Name / List Here -------------------
def gettingAllDatafromSources(comp_list,graphdb_login_res,b):
    temp_list = []
    error_comp = []
    today = date.today()
    c_year = today.strftime("%Y")
    # with tqdm(total=len(comp_list), desc=f'Featching Data From GraphDB...', unit='doc') as pbar:
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
                    app_dict['name'] = get_value(dbp_resp, 'parent_name')  or get_value(linkedin_resp, 'parent_name') or get_value(zoominfo_resp, 'parent_name') or get_value(yf_resp, 'parent_name')
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
                    app_dict['quarterly_growth'] = get_value(yf_resp, 'quarterly_growth') or 0
                    # app_dict['annual_growth'] = round(((int(get_value(yf_resp, 'revenue_doller')) - int(get_value(yf_resp, 'previous_year_revenue'))) / int(get_value(yf_resp, 'previous_year_revenue')))*100, 2)
                    app_dict['annual_growth'] = get_value(yf_resp, 'annual_growth') or 0
                    app_dict['SIC'] = get_value(zoominfo_resp, 'SIC')  or get_value(dbp_resp, 'SIC') or  get_value(linkedin_resp, 'SIC') or 0 
                    app_dict['NAICS'] = get_value(zoominfo_resp, 'NAICS') or get_value(dbp_resp, 'NAICS') or  get_value(linkedin_resp, 'NAICS') or 0
                    app_dict['parent']=comp
                    temp_list.append(app_dict)
                else:
                    app_dict['name'] = get_value(dbp_resp, 'name')
                    app_dict['description'] = f"""{get_value(dbp_resp, 'description')}\n{get_value(linkedin_resp, 'description')}"""
                    app_dict['industry'] = get_value(dbp_resp, 'industry') or get_value(linkedin_resp, 'industry') or get_value(zoominfo_resp, 'industry')
                    app_dict['headquarters'] = get_value(linkedin_resp, 'headquarters') or get_value(dbp_resp, 'headquarters') or get_value(zoominfo_resp, 'headquarters')
                    app_dict['no_of_employees'] = get_value(linkedin_resp, 'numOf_emp') or get_value(zoominfo_resp, 'numOf_emp') or get_value(dbp_resp, 'no_of_employees')
                    founded_year = get_value(zoominfo_resp, 'founded') or get_value(linkedin_resp, "founded") or get_year(get_value(dbp_resp, "founded_date"))
                    app_dict['operating_years'] = founded_year
                    app_dict['revenue_dollar'] = get_value(yf_resp, 'revenue_doller')
                    app_dict['quarterly_growth'] = get_value(yf_resp, 'quarterly_growth')
                    # app_dict['annual_growth'] = round(((int(get_value(yf_resp, 'revenue_doller')) - int(get_value(yf_resp, 'previous_year_revenue'))) / int(get_value(yf_resp, 'previous_year_revenue')))*100, 2)
                    app_dict['annual_growth'] = get_value(yf_resp, 'annual_growth')
                    app_dict['SIC'] = get_value(zoominfo_resp, 'SIC')
                    app_dict['NAICS'] = get_value(zoominfo_resp, 'NAICS')
                    app_dict['parent']=comp
                    temp_list.append(app_dict)    
            except Exception as e:
                error_comp.append(f"{comp}:{e}")

            # pbar.update(1)

    errorWrite(error_comp)
    InsertResult=InsertParentData(temp_list,b,graphdb_login_res)
    return InsertResult

#for error companies
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




#to encode description
def clean_description(description: str) -> str:
        if not description:
            return ""
        # remove unicode characters
        description = description.encode('ascii', 'ignore').decode()
        
        # remove punctuation
        description = re.sub('[%s]' % re.escape(string.punctuation), ' ', description)

        # clean up the spacing
        description = re.sub('\s{2,}', " ", description)

        # remove newlines
        description = description.replace("\n", " ")

        # split on capitalized words
        #description = " ".join(re.split('(?=[A-Z])', description))

        # clean up the spacing again
        description = re.sub('\s{2,}', " ", description)

        # make all words lowercase
        description = description.lower()

        return description


# this is query to insert the data to parent uri

def querytoinsertIntoParent(app_dict: dict, temp_uri: str, temp_des:str,temp_ind:str):
    query=f'''PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    insert data{{
    <{temp_uri}> dbo:description "{temp_des}" ;
    dbo:industry {temp_ind} ;
    dbo:headquarters "{app_dict['headquarters']}";
    dbo:no_of_employees {app_dict['no_of_employees']} ;
    foaf:founded "{app_dict['operating_years']}"^^xsd:gYear ;
    foaf:current_year_revenue {app_dict['revenue_dollar']} ;
    foaf:quarterly_revenue_growth "{app_dict['quarterly_growth']}"^^xsd:float ;
    foaf:annual_revenue_growth "{app_dict['annual_growth']}"^^xsd:float ;
    dbo:naics {app_dict['NAICS']} ;
    dbo:sic {app_dict['SIC']} .
    }}'''
    query = query.replace("\n", "")
    return query

#  parent data delete query 

def querytodeleteIntoParent(temp_uri: str):
    query=f'''PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

delete {{
     <{temp_uri}> ?p ?o .
}}where {{
    <{temp_uri}> ?p ?o .
    filter (?p NOT IN(rdfs:label, dbo:source, rdf:type , fosf:custom_lead))

}}'''
    query = query.replace("\n", "")
    return query



def deleteParentData(temp_list,b,graphdb_login_res):
    # with tqdm(total=len(temp_list), desc=f'Deleting Parent Data From GraphDB...', unit='doc') as pbar:
    for x in temp_list:
        temp_uri=x['parent']
        delete_query=querytodeleteIntoParent(temp_uri)
        update_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
                        delete_query), "token": graphdb_login_res.get('token')})
        # pbar.update(1)

def InsertParentData(temp_list,b,graphdb_login_res):
    deleteParentData(temp_list,b,graphdb_login_res)
    # with tqdm(total=len(temp_list), desc=f'Inserting Parent Data Into GraphDB...', unit='doc') as pbar:
    result=[]
    error=[]
    finalResponse={'error': [], 'record': []}
    for x in temp_list:
        temp_uri=x['parent']
        temp_des=clean_description(x['description'])
        temp_ind=','.join(f"'{e}'" for e in x['industry'].split(','))
        insert_query=querytoinsertIntoParent(x,temp_uri,temp_des,temp_ind)
        response=update_sparql_query({"repositoryID": DEFAULT_GRAPHDB_REPO, "query": encodeURIComponent(
                        insert_query), "token": graphdb_login_res.get('token')})
        if response['status']==True:
            result.append('Data inserted for ' + temp_uri)
        else:
            error.append('Data not inserted for ' + temp_uri)

        
            # pbar.update(1)
    finalResponse['error']=error
    finalResponse['record']=result
    return finalResponse
    


#-----------------Call Insert new parent data with deletion of old parent data---------






    
     