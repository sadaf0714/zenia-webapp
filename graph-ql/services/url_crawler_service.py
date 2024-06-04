from logging import exception
from urllib import response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import tldextract
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
from config.log_config import get_logger
from config.constant import ENV_MODE
import platform

my_logger = get_logger("/crawler_service")

def get_company_name_from_url(url):
  response={'error':None,'companyName':None}
  try:
    extracted = tldextract.extract(url)
    domain = extracted.domain
    response['companyName']= domain
  except Exception as e:
    response['error']=e
    my_logger.error(f"Error occured {e}")
  
  return response


def google_knowledge_panel(companyName):
  
  response={'error':None, 'data':None}
  dir_path = os.path.abspath('./')
   
  try:
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    #options.binary_location = dir_path + '/chrome-win64/chrome.exe'
    #driver = webdriver.Chrome(executable_path=f'''{dir_path}/drivers/{platform.system()}/chromedriver''', options=options)

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get(f"https://www.google.com/search?q={companyName}&hl=en")

    # Get the text of the web response
    response_text = driver.page_source
    #my_logger.info(response_text)
    #ubuntu - TQc1id
    #other  - VjDLd
    isClassFound = False
    os_name = platform.system()
    if os_name =="Windows":
      isClassFound = 'VjDLd'
    else:
      isClassFound  = 'TQc1id'
     
    if isClassFound:
      my_logger.info("class found")
      panelDiv = driver.find_element(By.CLASS_NAME, isClassFound)
      response['data']=panelDiv.text
      if response['data'] != "" and response['data'] != None:
        my_logger.info("data found")
        response['data']=get_data_from_knowledge_panel(response['data'],companyName)
    else:
      response['error']="Data not found"
  except Exception as e:
    response['error']=e
    my_logger.error(f"Error occured {e}")
  return response

def filter_noOfEmployees(no_of_employees:str):
  no_of_employees = no_of_employees.replace(",","") 
  no_of_employees = no_of_employees.replace("+","") 
  if "(" in no_of_employees:
    no_of_employees = no_of_employees.split("(")[0]
  return no_of_employees


def get_data_from_knowledge_panel(data,companyName):
  required_fields=['President', 'CFO', 'Customer service chat', 'Stock price', 'Founder', 'Net income', 'Founders', 'CMO', 'Headquarters', 'Technical support', 'Customer service', 'Chairperson', 'Number of employees', 'CEO', 'Revenue', 'Products', 'Founded', 'Owner', 'N number', 'CIO', 'Subsidiaries', 'Description', 'COO']
  result=dict()
  if "Description" in data:
    result['Description']=data[data.find("Description")+12:data.find("Wikipedia\n")].strip()

  for s in data.split("\n"):
    if ":" in s and s.split(":")[0] in required_fields:
      result[s.split(":")[0]]=s.split(":")[1].strip()
  
  result['name'] = companyName
  result['source'] = "others"
  if 'Headquarters' in result:
    result['headquarters']=result['Headquarters']
    del result['Headquarters']
  if 'Founded' in result:
    year=0
    if result['Founded'] != "" and result['Founded'] != None:
      foundingYear=re.search(r"\d{4}",result['Founded'])
      if foundingYear:
        year=foundingYear.group()
    result['founded']=int(year) if year.isnumeric() else 0
    del result['Founded']
  if 'Number of employees' in result:
    result['no_of_employees']=filter_noOfEmployees(result['Number of employees'])
    del result['Number of employees']
  if 'Description' in result:
    result['article']=result['Description']
    del result['Description']
  return result
  
# def url_content(url):
#   response={'error':None, 'content':None}
#   try:
#     res=requests.get(url)
#     if res.status_code == 200:
#       html_content = res.content
#       soup = BeautifulSoup(html_content, 'html.parser')
#       response['content']=soup.text
#     else:
#       response['error']='Response code error'
#   except exception as e:
#     response['error']=e
#     my_logger.info(f"Error occured {e}")
#   return response

def get_data_from_url(input):
    response={'error':None, 'data':None}
    domainResponse=get_company_name_from_url(input)

    if domainResponse['companyName'] != "" and domainResponse['companyName'] != None :
        googleKnowledgeResponse=google_knowledge_panel(domainResponse['companyName'])
        my_logger.info(googleKnowledgeResponse)
        if googleKnowledgeResponse['data'] != "" and googleKnowledgeResponse['data'] !=None :
            response['data'] = googleKnowledgeResponse['data']
        else:
            response['error']=googleKnowledgeResponse['error']
    
    return response