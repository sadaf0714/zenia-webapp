from asyncio import exceptions
from cgitb import reset
from logging import exception
from datetime import date
import sys
from unittest import result
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
from bs4 import BeautifulSoup
import requests
import json
import numpy as np
import yfinance as yahooFinance
from config.log_config import get_logger
from config.util import split_full_name

my_logger = get_logger("/crawler_service")

def get_sic_code(companyName):
  url="https://www.sec.gov/cgi-bin/browse-edgar?company="+companyName.replace("-","%20").replace("_","%20")+"&match=starts-with&filenum=&State=&Country=&SIC=&myowner=exclude&action=getcompany"
  response =  requests.get(url,headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Host":"www.sec.gov",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.7"})

  html_content = response.content
  soup = BeautifulSoup(html_content, 'html.parser')
  sicCode=""
  if response.status_code == 200 :
    if soup.find("div", class_="companyInfo") :         # If company Name exact match
      companyInfo=soup.find("div", class_="companyInfo")
      paraInCompanyInfo=companyInfo.find("p", class_="identInfo")
      sic=paraInCompanyInfo.find("a").text
      sicCode=sic if sic.isnumeric() else ""
    elif soup.find("table", class_ = "tableFile2") :         # If company Name does not match
      table=soup.find("table", class_ = "tableFile2")
      sicCodeStatus=False
      for tr in table.find_all("tr"):
        for td in tr.find_all("td"):
          if td.find("acronym"):
            if companyName.replace("-"," ").replace("_"," ").lower() in td.text.lower():
              sicCode=td.find("a").text
              sicCodeStatus=True
              break
        if sicCodeStatus==True:
          break
  return sicCode

def get_naics_code(companySicCode):
  url="https://www.naics.com/code-search/?code="+companySicCode+"&v=2022&styp=xsic"
  response =  requests.get(url,headers = {
    "User-Agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"})

  html_content = response.content
  soup = BeautifulSoup(html_content, 'html.parser')
  naicsCode=""
  if response.status_code == 200 :
    if soup.find("td", class_="first_child"):
      naicsCode=soup.find("td", class_="first_child").text
  return naicsCode

def get_results(query: str):
    target_url = f"https://www.bing.com/search?q={query}&rdr=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"}
    response={'error': None, 'url': None}
    try:
        resp = requests.get(target_url, headers=headers)
        if resp.status_code==200:
          soup = BeautifulSoup(resp.text, 'html.parser')
          complete_data = soup.find_all("li",{"class":"b_algo"})
          url = complete_data[0].find("a").get("href")
          response['url']=url
        else:
          response['error']="company not found"
    except Exception as e:
        my_logger.info("Error occured")
        my_logger.info(query)
        response['error']=e
    return response

def get_company_url_google_linkedin(name):
    params = f"linkedin.com {name}"
    res = get_results(params)
    return res

def get_company_url_google_dbpedia(name):
    params = f"dbpedia.org company {name}"
    res = get_results(params)
    return res

#Methods to get the financial data
def macro_tends(symbol,companyName, result):

  if symbol == "" or companyName == "":
    result['revenue_dollar'] = 0
    result['yearly_revenue_2021'] = 0
    result['last_quarterly_revenue']  =0
    result['second_last_quarterly_revenue'] = 0
    result['annual_growth'] = 0
    result['quarterly_growth'] = 0
  else:
    companyName=companyName.replace(" ","-").replace(",","").replace(".","").replace("(","").replace(")","")
    url="https://www.macrotrends.net/stocks/charts/"+symbol+"/"+companyName+"/revenue"
    try:
      response = requests.get(url)
    except Exception as e:
        my_logger.info(e)
    yearlyRevenue2022=0
    yearlyRevenue2021=0
    quarterlyRevenue2022=0
    quarterlyRevenue2021=0
    if response.status_code == 200 :
      html_content = response.content
      soup = BeautifulSoup(html_content, 'html.parser')
      for revenueTables in soup.find_all("div", id="style-1"):
        for table in revenueTables.find_all("div",class_ = "col-xs-6"):
          for thead in table.find_all("thead",class_ = ""):
            for tbody in table.find_all("tbody", class_ = ""):
              i=0
              j=0
              for tr in tbody.find_all("tr", class_ = ""):
                if "Annual Revenue" in thead.find("th").text.strip():
                  for td in tr.find_all("td", class_ = ""):
                    if i==1:
                      yearlyRevenue2022=td.text.strip()
                    if i==3:
                      yearlyRevenue2021=td.text.strip()
                    i+=1
                else:
                  for td in tr.find_all("td", class_ = ""):
                    if j==1:
                      quarterlyRevenue2022 = td.text.strip()
                    if j==3:
                      quarterlyRevenue2021 = td.text.strip()
                    j+=1
    result['revenue_dollar'] = int(yearlyRevenue2022.replace(',','').replace('$',''))*1000000
    result['yearly_revenue_2021'] = int(yearlyRevenue2021.replace(',','').replace('$',''))*1000000
    result['last_quarterly_revenue']  =int(quarterlyRevenue2022.replace(',','').replace('$',''))*1000000
    result['second_last_quarterly_revenue'] = int(quarterlyRevenue2021.replace(',','').replace('$',''))*1000000
    result['annual_growth'] = ((int(yearlyRevenue2022.replace(',','').replace('$','')) - int(yearlyRevenue2021.replace(',','').replace('$','')))/ int(yearlyRevenue2021.replace(',','').replace('$',''))) *100
    result['quarterly_growth'] = ((int(quarterlyRevenue2022.replace(',','').replace('$','')) - int(quarterlyRevenue2021.replace(',','').replace('$','')))/ int(quarterlyRevenue2021.replace(',','').replace('$',''))) *100
  return result

#Methods to get companyName from linkedin url
def get_company_name_linkedin(url: str):
    if (not url):
        return None
    url = url.strip()
    name = ""
    if (url.startswith('https://www.linkedin.com/company/')):
        url = url.replace("https://www.linkedin.com/company/", "")
        name = url[: url.find("/")] if (url.find("/") != -1) else url
    return name

#Method to get the data using rapidApi
def get_company_data(name):
     
    url = "https://linkedin-companies-data.p.rapidapi.com/"
    querystring = {"vanity_name": name}
    headers = {
      "X-RapidAPI-Key": "7e97d41d33msh72e73c747becc47p1cb6fejsndd85bf54e01e",
      "X-RapidAPI-Host": "linkedin-companies-data.p.rapidapi.com"
    }
    dataResponse={'error':None, 'data':None}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code==200:
          resp = response.json()
          dataResponse['data']=resp
        else:
          dataResponse['error']="Response Error"
    except Exception as e:
        my_logger.info(f"Error decoding JSON for company {name}")
        dataResponse['error'] = e

    return dataResponse

#Method to get the articleBody for a company
def get_article(name):
    url = "https://kgsearch.googleapis.com/v1/entities:search?query="+name.lower()+"&key=AIzaSyDqRLBoDkQlKFFRRiFH8rFp6PdMF5PHA9Y&limit=1&indent=True"
    response = requests.get(url)
    article=""
    if response.status_code == 200 :
      html_content = response.content.decode('utf-8')
      json_code = json.loads(html_content)
      if json_code['itemListElement']:
        try:
          for data in json_code['itemListElement']:
              article = data['result']['detailedDescription']['articleBody']
        except Exception as e:
            my_logger.info(f"{name} Error type: {type(e).__name__}{e}")
    return article

def intilize_dict(data: dict):
    for key in columns_to_include:
        data[key] = ""

#DBpedia endpoint
dbpedia_endpoint = "https://dbpedia.org/sparql"

# # pre-define columns of json result [dbpedia fields]
columns_to_include = (["foundingYear","name", "industry", "type", "symbol", "abstract", "hqLocationCity","hqLocationCountry","numberOfEmployees","website"])


#Method to get the query for a specific company
def get_query_for_company_name(com_name: str):
    return f'''
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbr: <http://dbpedia.org/resource/>
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    prefix com: <http://dbpedia.org/ontology/>
    SELECT (SAMPLE(str(?property)) as ?propertyName)  (SAMPLE(str(?value)) as
     ?valueSample) WHERE{{
        <http://dbpedia.org/resource/{com_name}> ?property ?value .
        FILTER(LANG(?value) = "" || LANG(?value) = "en" || isURI(?value))
    }}
    GROUP BY ?property
    '''
def company_data_extraction_from_dppedia(name: str):
    sparql = SPARQLWrapper(dbpedia_endpoint)
    sparql.setQuery(get_query_for_company_name(name))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # Process the results
    data = dict()
    intilize_dict(data)
    for binding in results['results']['bindings']:
        try:
            property_name = binding['propertyName']['value']
            prop_name = property_name[property_name.rfind("/")+1:]
            value = binding['valueSample']['value']
            
            idx = value.rfind("/")
            if (idx != -1):
                value = value[idx + 1:] if (len(value) > idx) else value
            data[prop_name] = value
        except Exception as e:
            my_logger.info("Error in fetching property")
    return data

#Method to get the query for contact data of a company
def get_query_for_contact(com_name: str):
    return f'''SELECT ?dbpName ?rdfslabel ?foafName (GROUP_CONCAT(DISTINCT ?dbp_occupation ;separator=",") as ?dbp_occupations ) ?info
where
{{
	?person dbo:employer <http://dbpedia.org/resource/{com_name}>.
OPTIONAL{{ ?person dbp:name ?dbpName FILTER (LANGMATCHES(LANG(?dbpName ), "en"))}}
OPTIONAL{{ ?person rdfs:label ?rdfslabel FILTER (LANGMATCHES(LANG(?rdfslabel), "en"))}}
OPTIONAL{{ ?person foaf:name ?foafName FILTER (LANGMATCHES(LANG(?foafName), "en"))}}
OPTIONAL{{ ?person dbp:occupation ?dbp_occupation }}
OPTIONAL{{ ?person dbo:abstract ?info FILTER (LANGMATCHES(LANG(?info), "en"))}}
}}GROUP BY ?dbpName ?rdfslabel ?foafName ?info'''


def get_contact_from_dppedia(name: str):
    sparql = SPARQLWrapper(dbpedia_endpoint)
    sparql.setQuery(get_query_for_contact(name))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # Process the results
    data = []
    try:
        for bindings in results['results']['bindings']:
            res={}
            for key, value in bindings.items():
                res[key] = value['value']
            # print(res)
            data.append(res)
    except Exception as e:
        my_logger.info("Error in fetching property")
    return data

def get_company_name_dbpedia(url: str):
    url = url.strip()
    name = ""
    if (url.startswith('https://dbpedia.org/page/')):
        url = url.replace("https://dbpedia.org/page/", "")
        name = url[: url.find("/")] if (url.find("/") != -1) else url
    elif (url.startswith('https://dbpedia.org/resource/')):
        url = url.replace("https://dbpedia.org/resource/", "")
        name = url[: url.find("/")] if (url.find("/") != -1) else url
    return name

#Method to get the data from DBpedia
def get_dbpedia_company_data(name):
    response={'error':None, 'data':dict()}
    d=dict()
    try:
        if name != "" and name != None:
          d = company_data_extraction_from_dppedia(name)
          #my_logger.info(d)
          d['description']=d['abstract']
          del d['abstract']
          d['founded']=int(d['foundingYear']) if d['foundingYear'] != "" and d['foundingYear'] != None else ""
          d['operating_years']=date.today().year-int(d['foundingYear']) if d['foundingYear'] != "" and d['foundingYear'] != None else ""
          del d['foundingYear']
          d['headquarters']=d['hqLocationCity']
          del d['hqLocationCity']
          d['country']=d['hqLocationCountry']
          del d['hqLocationCountry']
          d['source']="dbpedia"
          d['no_of_employees']=int(d["numberOfEmployees"]) if d["numberOfEmployees"] != "" and d["numberOfEmployees"] != None else ""
          del d["numberOfEmployees"]
          d['company_type']= d["type"] if d["type"] != "" and d["type"] != None else ""
          del d["type"]
          d['parent_name'] = d['name']
          d['name'] = d['rdf-schema#label']
          #d['name'] = d['isPrimaryTopicOf']

          contactList=get_contact_from_dppedia(name)
          d['employer'] = []
          #collects contact information
          records = []
          if len(contactList) > 0:
                for item in contactList:
                    name = ""
                    if item.get("dbpName"):
                        name = item.get("dbpName")
                    elif item.get("foafName"):
                        name = item.get("foafName")
                    elif item.get("rdfslabel"):
                        name = item.get("rdfslabel")
                    first_name, last_name = split_full_name(name)
                
                    records.append({
                        "first_name": first_name,
                        "last_name": last_name,
                        "occupation": item['dbp_occupations'] if "dbp_occupations" in item else  "",
                        "social_url": item['social_url'] if "social_url" in item else "",
                        "description": item['info'] if "info" in item else "",
                        "source":"dbpedia"
                    })
          d['employer']  = records
          response['data'] = d
        else:
          response['error']="Company not found on dbpedia"
    except Exception as e:
        my_logger.info(f"Error in {name}")
        response['error']=e
    return response


#Method to get the linkedin data
def get_linkedin_company_data(name):
    desire_columns = ['company_name','industry', 'headquarters', 'type', 'founded','employees_num','about_us','country_code','website','company_size','social_url']
    response={'error':None, 'data':None}

    if name != "" and name != None:
      dataResp = get_company_data(name)
      if dataResp['error'] == None:
        try:
            d = dataResp['data']
            #my_logger.info(d)
            # for col in desire_columns:
            #     d[col] = ""
            #     if (isinstance(dataResp['data'].get(col), str)):
            #         d[col] = dataResp['data'].get(col, "")
            #     elif (isinstance(dataResp['data'].get(col), int)):
            #         d[col] = dataResp['data'].get(col, 0)
            #     elif (isinstance(dataResp['data'].get(col), list)):
            #         d[col] = ', '.join([(a.get("company_name", "")
            #                             if isinstance(a, dict)
            #                             else str(a)) for a in dataResp['data'].get(col)])
            d['description']=d['about_us']
            del d['about_us']
            d['founded']=int(d['founded']) if d['founded'] != "" and d['founded'] != None else ""
            d['operating_years']=date.today().year-int(d['founded']) if d['founded'] != "" and d['founded'] != None else ""
            d['name']= d['company_name']
            del d['company_name']
            d['no_of_employees']=int(d['employees_num']) if d['employees_num'] != "" and d['employees_num'] != None else ""
            del d['employees_num']
            d['source']="linkedin"
            d['country']=d['country_code']
            del d['country_code']
            d['website']=d['website'].split("\n")[0] if d['website'] != "" and d['website'] != None else ""
            #d['sic']= ""
            d['parent_name']= ""
            #d['naics']= ""
            if "specialties" in d:
              d['specialities'] = ','.join(d['specialties'])
              del d['specialties']
            if "type" in d:
              d['company_type'] = d['type']
              del d['type']
            if "founded" in d:
              if d['founded'] is not None:  
                d['founded'] = d['founded']
                del d['founded']
            
            d['employer'] = []
            #collects contact information
            records = [];
            if len(d['employees']) > 0:
              for item in d['employees']:
                first_name, last_name = split_full_name(item['full_name'])
                
                records.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "occupation": item['position'] if "position" in item else  "",
                    "social_url": item['social_url'] if "social_url" in item else "",
                    "description": item['description'] if "description" in item else "",
                    "source":"linkedin"
                }) 
            d['employer']  = records;
            response['data'] = d
        except Exception as e:
            my_logger.info(f"Error in {name}")
            response['error']=e
      else:
        response['error']=dataResp['error']
    else:
      response['error']="Company not found"
    return response

def remove_nested_objects(result):
  res=dict()
  for key, value in result.items():
    if key =="employer":
       res[key] = value
    elif isinstance(value, dict):
      pass
    elif isinstance(value, list):
      if any(isinstance(item, dict) for item in value):
        pass
      elif all(isinstance(item,str) for item in value):
        res[key]=', '.join(value)
    else:
      res[key]=value
  return res

def fetch_company_data(input: dict):
    res = {}
    if input['source'] == 'linkedin':
      res = get_linkedin_company_data(input['name'])
    elif input['source'] == 'dbpedia':
      res = get_dbpedia_company_data(input['name'])
    elif input['source'] == 'yahoo_finance':
      res = get_financial_data(input['name'])
      #print(res)
    if res['data'] != "" and res['data'] != None:
      res['data'] = remove_nested_objects(res['data'])
    # print(res)
    return res


def get_financial_data(symbol):
  results={'error':None, 'data':{}}
   
  try:
    finance_data = yahooFinance.Ticker(symbol)
     
    data = {}
    data['name']=(finance_data.get_info()).get('longName')
    data['source']="yahoo_finance"
    data['ticker_symbol']=(finance_data.get_info()).get('symbol')
    data['no_of_employees']=(finance_data.get_info()).get(' ')
    data['exchange']=(finance_data.get_info()).get('exchange')

    if 'GrossProfit'  in (finance_data.get_incomestmt()).index:
      data['gross_profit']=(finance_data.get_incomestmt()).loc['GrossProfit'][0]
    else:
      data['gross_profit']=''

    if 'TotalAssets' in (finance_data.get_balance_sheet()).index:
      data['total_assets']=(finance_data.get_balance_sheet()).loc['TotalAssets'][0]
    else:
      data['total_assets']=''

    data['industry']=(finance_data.get_info()).get('industry')
    data['website']=(finance_data.get_info()).get('website')
    #data['country']=(finance_data.get_info()).get('country')
    #data['sector']=(finance_data.get_info()).get('sector')
    #data['state']=(finance_data.get_info()).get('state')
    #data['city']=(finance_data.get_info()).get('city')

    data['market_cap']=(finance_data.get_info()).get('marketCap')
    yearly_revenue_2023=''
    yearly_revenue_2022=''
    yearly_revenue_2021=''
    income_stmt_df=finance_data.get_incomestmt()
    for x in list(income_stmt_df.columns.values):
      if x.astype('datetime64[Y]')==np.datetime64('2023'):
        yearly_revenue_2023=(finance_data.get_incomestmt()).loc['TotalRevenue'][x.astype('datetime64[D]')]
      elif x.astype('datetime64[Y]')==np.datetime64('2022'):
        yearly_revenue_2022=(finance_data.get_incomestmt()).loc['TotalRevenue'][x.astype('datetime64[D]')]
      elif x.astype('datetime64[Y]')==np.datetime64('2021'):
        yearly_revenue_2021=(finance_data.get_incomestmt()).loc['TotalRevenue'][x.astype('datetime64[D]')]
    data['current_year_revenue']=yearly_revenue_2023
    data['previous_year_revenue']=yearly_revenue_2022
    
    if yearly_revenue_2023 == '':
      data['current_year_revenue']=yearly_revenue_2022
      data['previous_year_revenue']=yearly_revenue_2021

    if finance_data.quarterly_income_stmt.empty:
        data['last_quarterly_revenue']=''
        data['second_last_quarterly_revenue']=''
    else:
      data['last_quarterly_revenue']=((finance_data.quarterly_income_stmt).loc['Total Revenue'])[0]
      data['second_last_quarterly_revenue']=((finance_data.quarterly_income_stmt).loc['Total Revenue'])[1]
    data['quarterly_revenue_growth']=finance_data.get_info().get('revenueGrowth')
    data['description']=(finance_data.get_info()).get('longBusinessSummary')
    
    data['employer'] = []
    #collects contact information
    records = []
    if finance_data.get_info().get('companyOfficers'):
      if len(finance_data.get_info().get('companyOfficers')) > 0:
            for item in finance_data.get_info().get('companyOfficers'):
                
                first_name, last_name = split_full_name(item['name'])
                records.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "occupation": item['title'] if "title" in item else  "",
                    "social_url": item['social_url'] if "social_url" in item else "",
                    "description": item['info'] if "info" in item else "",
                    "source":"yahoo_finance"
                })

    data['employer']  = records
    results['data'] = data
  except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        results['error']=f"The symbol '{symbol}' was not found on Yahoo Finance."
    else:
        results['error']=f"An HTTP error occurred: {e}"
  except Exception as e:
    results['error']=e
  return results