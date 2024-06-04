import requests
import json
import urllib.parse
from datetime import datetime
from config.util import encodeURIComponent, get_plans_construct_query_post
from config.constant import allianzTravelCoverages, coverageList, EXTRACT_COVERAGE_AMOUNT, GRAPHDB_VISUAL_GRAPH, DEFAULT_GRAPHDB_REPO, GET_SUMMARY_REASONS
from config.util import extract_text_from_pdf_url, parse_json_response, clean_description
from config.log_config import get_logger
from services import similarity_service, graphdb_service
from datetime import datetime, timedelta
import time
import asyncio
import copy 

def find_coverage_amount_by_coverage_name(coverageName, quote):
    coverageAmount = ""
    if quote.get("Features"):
        for feature in quote.get("Features"):
            if coverageName.lower() == feature['DisplayInfo']['Name'].lower():
                coverageAmount = feature['Coverage']
    
    return coverageAmount

def calculate_dob(age):
    if type(age) != int:
        age = int(age)
    current_date = datetime.now()
    dob_year = current_date.year - age
    dob = datetime(dob_year, current_date.month, current_date.day)
    dob_formatted = dob.strftime('%m-%d-%Y')
    return dob_formatted

def change_date_format(date_str):
    # Split the date string by "-"
    parts = date_str.split("-")
    
    # Rearrange the parts in mm/dd/yyyy format
    formatted_date = parts[1] + "/" + parts[2] + "/" + parts[0]
    
    return formatted_date

def get_quote_details(quote, stateResidence):
    plan = {}
    
    plan['carrier'] = "https://www.allianztravelinsurance.com"
    plan['planName'] = quote['DisplayInfo']['Name']
    plan['productId'] = quote['ProductID']
    plan['pdfUrl'] = f'''https://www.allianztravelinsurance.com/api/certificates/download/all?ProductID={plan['productId']}&State={stateResidence}'''
    plan['quote'] = quote
    plan['planCost'] = quote['Price']['Amount']
    # plan['exclusions'] = []
    #!plan['inclusions'] = []
    #!for coverage in allianzTravelCoverages:
        #!cov={}
        #!cov["coverageName"] = coverage['id']
        #!cov['coverageAmount'] = find_coverage_amount_by_coverage_name(coverage["coverageName"],quote) if coverage['coverageName'] != "" else ""
        # cov['coverageDetails'] = []
        #!plan['inclusions'].append(cov)
    return plan

def getAllianzTravelPlan(params):
    plans =  {}

    Insureds = []
    if params.get("travellers"):
        for item in params.get("travellers"):
            Insureds.append({
                "Age": item['age'],
                "Primary": True,
                "MailingAddress": {
                    "Address1": "",
                    "Address2": "",
                    "City": "",
                    "CountryCode": "USA",
                    "PostalCode": "",
                    "StateCode": params['stateResidence']
                }
            })

    payload = {
        "Destination": {},
        "StartDate":params['startDate'],
        "EndDate":params['endDate'],
        "StateOfResidence":params['stateResidence'],
        "TripCost":{
            "Amount":params['totalTripCost'],
            "Type":"USD"
        },
        "Type":"International",
        "Insureds": Insureds
    }
    headers = {
        "Content-Type": "application/json",
        "Origin":"https://www.allianztravelinsurance.com",
        'Referer':"https://www.allianztravelinsurance.com/compare-plans",
        'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    response  =  requests.put('https://www.allianztravelinsurance.com/api/quotes/request', verify=False, data = json.dumps(payload), headers= headers)
    if response.status_code == 200 :
        response = response.json()
        if len(response['Quote']) > 0:
            quote = response['Quote'][0]
            plans = get_quote_details(quote, params['stateResidence'])
            plans['carrierName'] = "AllianzTravel"
    return plans

def getTravelGuardplanCost(params):
    planCost = ""
    url = "https://www.travelguard.com/content/forms/af/travelguard/us/en/buy/jcr:content/guideContainer.af.dermis"

    travelers = []
    travelerIdentifier=0
    if params.get("travellers"):
        for item in params.get("travellers"):
            travelerIdentifier+=1
            travelerDOB = calculate_dob(item['age'])
            travelers.append({
                    "travelerIdentifier": travelerIdentifier,
                    "prefix": "wer",
                    "firstName": "",
                    "middleName": "",
                    "lastName": "",
                    "suffix": "",
                    "dateOfBirth": travelerDOB,
                    "passengerType": "Adult",
                    "addresses": [
                        {
                            "type": "Residency",
                            "isoStateOrProvince": params['stateResidence'],
                            "street1": "",
                            "city": "",
                            "stateOrProvinceName": params['stateResidence'],
                            "postalCode": "",
                            "isoCountry": "US"
                        }
                    ],
                    "contactDetails": [
                        {
                            "type": "Email",
                            "value": ""
                        }
                    ],
                    "travelerTripPrice": {
                        "isoCurrencyCode": "USD",
                        "value": params['totalTripCost']
                    }
                    })

    input = f'''{{
            "QuoteRequest":{{
                "schemaVersion":2.3,
                "partnerId":"DIGDRCT",
                "language":"en",
                "partnerSystemId":"MULTI",
                "partnerPOS":"US",
                "quoteRequest":{{
                    "trips":[
                        {{
                        "tripIdentifier":"1",
                        "tripType":"OW",
                        "initialDepositDate":"2024-03-12",
                        "finalPaymentDate":"",
                        "totalTripPrice":[
                            {{
                                "isoCurrencyCode":"USD",
                                "value":"{params['totalTripCost']}"
                            }}
                        ],
                        "referenceNumbers":[
                            {{
                                "type":"BookingItemID",
                                "value":""
                            }}
                        ],
                        "bookingItems":[
                            {{
                                "order":1,
                                "startDateTime":"{change_date_format(params['startDate'])}",
                                "endDateTime":"{change_date_format(params['endDate'])}",
                                "supplier":{{
                                    "type":"Airplane"
                                }},
                                "bookingItemPrice":[
                                    {{
                                    "isoCurrencyCode":"USD",
                                    "value":"{params['totalTripCost']}"
                                    }}
                                ],
                                "referenceNumbers":[
                                    {{
                                    "type":"a",
                                    "value":""
                                    }}
                                ],
                                "locations":[
                                    {{
                                    "type":"Destination",
                                    "locationValue":[
                                        {{
                                            "type":"ISOCountry",
                                            "value":"{params['primaryDestination']}",
                                            "primaryFlag":"true"
                                        }}
                                    ]
                                    }}
                                ]
                            }}
                        ]
                        }}
                    ],
                    "travelers":{travelers},
                    "productDetails":[
                        {{
                        "productCode":"{params['productId']}",
                        "productName":"{params['planName']}",
                        "planCode":"{params['planCode']}",
                        "amounts":null,
                        "benefitDetails":[
                            
                        ],
                        "referenceNumbers":null,
                        "tripIdentifiers":[
                            {{
                                "tripIdentifier":"1"
                            }}
                        ],
                        "travelerIdentifiers":[
                            {{
                                "travelerIdentifier":"1",
                                "insuredType":"PrimaryInsured"
                            }}
                        ]
                        }},
                        ],
                    "submissionType":"Travelguard.com",
                    "fulfillmentOption":"Online"
                }}
            }}
            }}'''
    payload = {'functionToExecute': 'invokeFDMOperation',
    'formDataModelId': '/content/dam/formsanddocuments-fdm/tg-common/purchase-path',
    'input': input,
    'operationName': 'POST /policy/quote/v2_15579936244501',
    'guideNodePath': '/content/forms/af/travelguard/us/en/quote/getAQuotePanel/jcr:content/guideContainer/rootPanel/items/guidebutton'}

    response = requests.request("POST", url, data=payload, verify=False)

    if response.status_code == 200 :
        response =  json.loads(response.text)
        planCost = response['quoteResponse']['quoteResponses'][0]['purchaseRequest']['productDetails'][0]['amounts'][0]['amountValues'][0]['value']

    return convert_cost(planCost)


def getTravelGuardPlan(params):
    plans =  {}
    #first request to get product Ids
    url = "https://www.travelguard.com/content/forms/af/travelguard/us/en/buy/jcr:content/guideContainer.af.dermis"

    payload = {
        'functionToExecute': 'invokeFDMOperation',
        'formDataModelId': '/content/dam/formsanddocuments-fdm/tg-common/purchase-path',
        'input': f'''{{"arc":"332996","isoCountryCode":"US","stateCode":"{params['stateResidence']}","Content-Type":"application/json"}}''',
        'operationName': 'GET /product/list/v1/{arc}/{isoCountryCode}/{stateCode}_15556700573950',
        'guideNodePath': '/content/forms/af/travelguard/us/en/buy/jcr:content/guideContainer/rootPanel/items/panel/items/wrapperPanel_Residency/items/panel_368452407/items/guidebutton_11549439'
    }
    headers = {
        #"Content-Type": "application/json",
        "Origin":"https://www.travelguard.com",
        'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    response = requests.request("POST", url, data=payload, verify=False, headers=headers)
    if response.status_code == 200 :
        response =  json.loads(response.text)
        if len(response['products']) > 0:
            quote = response['products'][0]
            plans['carrier'] = "https://www.travelguard.com/"
            plans['planName'] = quote['name']
            plans['productId'] = quote['productId']
            plans['pdfUrl'] = f'''https://webservices.travelguard.com/Product/FileRetrieval.aspx?CountryCode=US&FileType=PROD_PLAN_DOC&ProductCode={quote['productId']}&StateCode={params['stateResidence']}&PlanCode={quote['planCode']}'''
            plans['quote'] = quote
            params['planName'] = plans['planName']
            params['productId'] = plans['productId']
            params['planCode'] = quote['planCode']
            plans['planCost'] = getTravelGuardplanCost(params)
            plans['carrierName'] = "TravelGuard"
    return plans

def get_count(plan):
    count = len(plan.get("inclusion")) - len(plan.get("exclusion"))
    # print("inc - exc: ",count)

    for inclusion in plan.get("inclusion"):
        count += len(inclusion.get("coverageDetails"))/10
    
    # print("total count:", count,end="\n\n")
    return count*10

def getBestPlan(data):
    
    plan1weighted = get_count(data[0])
    if data[0].get("cost"):
        plan1weighted += int(data[0].get("cost")) if type(data[0].get("cost")) != int else data[0].get("cost")

    plan2weighted = get_count(data[1])
    if data[1].get("cost"):
        plan2weighted += int(data[1].get("cost")) if type(data[1].get("cost")) != int else data[1].get("cost")

    return max(plan1weighted,plan2weighted)

def convert_cost(cost):
    return float(cost.replace("$","").replace(",",""))

def get_plan_names(insurancePlans):

    app_dict = {}
    for plan in insurancePlans:
            app_dict[plan['planName']] = 0
    return app_dict

def format_inclusions(inclusions):
    resp = []
    for coverage_name, coverage_amount in inclusions.items():
        resp.append({
            "coverageName": coverage_name,
            "coverageAmount": coverage_amount
        })
    return resp

def get_extracted_coverage_amount_from_GPT(extracted_text):
    result = {"error": None, "data": None}
    my_logger = get_logger("/get-coverage-amount")
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(f'{EXTRACT_COVERAGE_AMOUNT}', data = json.dumps({"text":extracted_text}), headers = headers)
        if response.status_code == 200:
            response = response.json()
            if response['error'] == None:
                result['data'] = response['result']
            else:
                result['error'] = response['error']
        elif response.status_code == 404 :
            result['error'] = response.get('error')             
        else:
            result['error'] = 'coverage amount not found'
    except Exception as e:
        my_logger.error(e)
        result['error'] = e
    return result

def getBestPlan2(insurancePlans):
    result = {"error":None, "best_plan":None}
    
    insuranceNameAndcpc = get_plan_names(insurancePlans) #Creating a key value dict {"planName":"coveragePerCost"}
    for coverage in coverageList:

        for plan in insurancePlans:
            coverage_cost = None
            plan_cost = None
            plan_commission = plan.get("commission")
            for inclusion in plan['inclusions']:
                if inclusion['coverageName'] == coverage:
                    coverage_cost = convert_cost(inclusion['coverageAmount']) if inclusion['coverageAmount'] != "" else 0
                    plan_cost = convert_cost(plan['planCost']) if type(plan['planCost']) != int and type(plan['planCost']) != float else plan['planCost']
                    break

            if coverage_cost is not None and plan_cost is not None:
                coverage_per_cost = (coverage_cost / plan_cost) * plan_commission
                insuranceNameAndcpc[plan['planName']] += coverage_per_cost
        # print(insuranceNameAndcpc,end="\n\n\n---------------------\n\n\n")
        
        # Checking if all values are not the same
        if len(set(insuranceNameAndcpc.values())) == len(insuranceNameAndcpc):
            
            # Finding the plan name associated with the maximum value
            bestPlanName = max(insuranceNameAndcpc, key=insuranceNameAndcpc.get)
            result['best_plan'] = getCompleteDetail(bestPlanName,insurancePlans)
            return result


    #Checking at the last all the coveragesPerCosts are same or not
    if len(set(insuranceNameAndcpc.values())) != len(insuranceNameAndcpc):
        result['error'] = "All coverages amount is same"             
        return result
    
    
    return result


def insertDataIntoGraphDBRest(params):
    response = {}
    my_logger = get_logger("/insertDataIntoGraphDB")
    loginResponse = graphdb_service.login()
    if "token" in loginResponse:
        rdf_data = f'''
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix gr: <http://www.griffin.org/> .
            @prefix pro: <http://property.org/resource/> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        '''
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        input_info = params['input_info']
        requestUri = f'''http://www.griffin.org/{encodeURIComponent(formatted_time)}/{urllib.parse.urlencode(params['input_info'])}'''
        for item in params['plans']:            
            item['request_uri']  = requestUri
            productId = item['productId']

            if item['planCost']:
                rdf_data += f'''
                        <{requestUri}>
                        gr:hasPlanCost "{item['planCost']}"^^xsd:double ;
                        gr:planCost <http://property.org/resource/{requestUri}/{productId}/{item['planCost']}> .
                        <http://property.org/resource/{requestUri}/{productId}/{item['planCost']}> a gr:Cost ;
                        rdfs:label "{item['planCost']}" ;
                        gr:includesPlan <http://www.griffin.org/{productId}/QuoteCost> .
                        gr:{productId} gr:requestCost <http://www.griffin.org/{productId}/QuoteCost> .
                        <http://www.griffin.org/{productId}/QuoteCost> a gr:QuoteCost ;
                        rdfs:label "Prices" .

                '''

            rdf_data += f'''
                    # Individual Quotes
                    gr:{productId} rdf:type gr:Quote ;
                        rdfs:label "{item['planName']}" ;
                        gr:productId "{productId}" .
                    '''
            # Carrier Sites
            rdf_data += f'''<{item['carrier']}> rdf:type gr:CarrierSite ;
                gr:quote gr:{productId} .'''
            
            # Traveller Requests
            rdf_data += f'''<{requestUri}> rdf:type gr:TravellerRequest ;
                rdfs:label "request-{datetime.now()}" ;
                gr:request <http://www.griffin.org/{productId}/requests> ;
                gr:startDate "{input_info['startDate']}"^^xsd:date ;
                gr:endDate "{input_info['endDate']}"^^xsd:date ;
                gr:destinationCountry "{input_info['primaryDestination']}" ;
                gr:stateOfResidence "{input_info['stateResidence']}" ;
                gr:totalTripCost "{input_info['totalTripCost']}"^^xsd:integer .
            '''
            rdf_data += f'''<{requestUri}> gr:travelers <{requestUri}-travelers> .
                <{requestUri}-travelers> rdfs:label "Travelers" . '''
                                 
            #use loop
            for traveler_item in input_info['travellers']:
                rdf_data +=   f'''
                        <{requestUri}-travelers> gr:traveler <{requestUri}-{traveler_item['name']}-{traveler_item['age']}> .
                        <{requestUri}-{traveler_item['name']}-{traveler_item['age']}> a gr:Traveler;
                                    rdfs:label "{traveler_item['name']}" ;
                                    gr:age  "{traveler_item['age']}"^^xsd:integer  . 
                '''
            
            #rdf_data += f'''<{requestUri}> gr:status <http://property.org/resource/{requestUri}/in-progress> .'''

            rdf_data += f'''<http://www.griffin.org/{productId}/requests> gr:getQuote gr:{productId} .'''    

            # Agent
            rdf_data += f'''<http://{input_info['agentEmail']}> rdf:type gr:Agent ;
                rdfs:label "{input_info['agentName']}" ;
                gr:email "{input_info['agentEmail']}";
                gr:name "{input_info['agentName']}".
                <http://{input_info['agentEmail']}>  gr:request <{requestUri}> .
            '''
            
        graphDBResponse = graphdb_service.add_rdf_statement({'repositoryID':DEFAULT_GRAPHDB_REPO,'rdfData':rdf_data,'token':loginResponse['token']})
        my_logger.info('pre graphdb query ')
        my_logger.info(graphDBResponse)
        if 'success' in graphDBResponse:
            response['success'] = True
        if 'error' in graphDBResponse:
            response['error'] = True
            
        response['plans'] = params['plans']
    return response


def insertDataIntoGraphDB(params):
    response = {}
    my_logger = get_logger("/insertDataIntoGraphDB")
    loginResponse = graphdb_service.login()
    if "token" in loginResponse:
        rdf_data = f'''
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix gr: <http://www.griffin.org/> .
            @prefix pro: <http://property.org/resource/> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        '''
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        input_info = params['input_info']
        requestUri = f'''http://www.griffin.org/{encodeURIComponent(formatted_time)}/{urllib.parse.urlencode(params['input_info'])}'''
        for item in params['plans']:            
            item['request_uri']  = requestUri
            productId = item['productId']
            formatted_exclusions = ""

            if len(item['exclusions']) > 0:    
                formatted_exclusions = ','.join(['"' + clean_description(x) + '"' for x in item['exclusions']])
            
            if item['planCost']:
                rdf_data += f'''
                        <{requestUri}>
                        gr:hasPlanCost "{item['planCost']}"^^xsd:double ;
                        gr:planCost <http://property.org/resource/{requestUri}/{productId}/{item['planCost']}> .
                        <http://property.org/resource/{requestUri}/{productId}/{item['planCost']}> a gr:Cost ;
                        rdfs:label "{item['planCost']}" ;
                        gr:includesPlan <http://www.griffin.org/{productId}/QuoteCost> .
                        gr:{productId} gr:requestCost <http://www.griffin.org/{productId}/QuoteCost> .
                        <http://www.griffin.org/{productId}/QuoteCost> a gr:QuoteCost ;
                        rdfs:label "Prices" .

                '''

            rdf_data += f'''<http://property.org/resource/{requestUri}/in-progress> rdfs:label "Done" .'''
            
            if len(item['inclusions']) > 0:    
                rdf_data += f''' gr:{productId} gr:includes <http://www.griffin.org/{productId}/inclusions> .'''

                rdf_data += f''' gr:{productId} gr:inclusionsStatus "Yes" .'''
            
            if formatted_exclusions:    
                rdf_data += f''' 
                            gr:{productId} gr:excludes <http://www.griffin.org/{productId}/exclusions> .
                            <http://www.griffin.org/{productId}/exclusions> a gr:Exclusions ;  
                                rdfs:label "Exclusions" ;
                                gr:exclusionsDetails {formatted_exclusions} .
                '''

            # Inclusions
            allInclusionsUri = []
            if len(item['inclusions']) > 0:
                for incItem in item['inclusions']:
                    formatted_details = ""
                    if "coverageDetails" in incItem:
                        if len(incItem['coverageDetails']) > 0:
                            incItem['coverageDetails'] = list(filter(lambda x: x != "", incItem['coverageDetails']))
                            formatted_details = ','.join(['"' + clean_description(x) + '"' for x in incItem['coverageDetails']])

                    allInclusionsUri.append(f'''<http://www.griffin.org/{productId}/{encodeURIComponent(incItem['coverageName'])}>''')
                    rdf_data += f'''
                        <http://www.griffin.org/{productId}/{encodeURIComponent(incItem['coverageName'])}> rdf:type gr:Inclusion ;
                            rdfs:label "{incItem['coverageName']}" ;
                            gr:name "{incItem['coverageName']}" .'''
                    
                    if formatted_details:
                        rdf_data += f'''<http://www.griffin.org/{productId}/{encodeURIComponent(incItem['coverageName'])}>
                                        gr:inclusionDetails {formatted_details} . 
                                    '''
                    
                    if incItem['coverageAmount'] and incItem['coverageAmount']!="0" and incItem['coverageAmount']!=0:     
                        rdf_data += f'''<{requestUri}> gr:coverage  <http://property.org/resource/{requestUri}/{encodeURIComponent(incItem['coverageName'])}/{incItem['coverageAmount']}> .
                            <http://property.org/resource/{requestUri}/{encodeURIComponent(incItem['coverageName'])}/{incItem['coverageAmount']}> a gr:Cost ;
                            rdfs:label "{incItem['coverageAmount']}" ;
                            gr:includesCoverage <http://www.griffin.org/{productId}/{encodeURIComponent(incItem['coverageName'])}> .
                        '''
            if allInclusionsUri:
                formatted_inclusions = ','.join([x for x in allInclusionsUri])
                rdf_data += f'''
                    <http://www.griffin.org/{productId}/inclusions> a gr:Inclusions; 
                        rdfs:label "Inclusions" ;
                        gr:inclusion {formatted_inclusions} .
                        
                '''
        graphDBResponse = graphdb_service.add_rdf_statement({'repositoryID':DEFAULT_GRAPHDB_REPO,'rdfData':rdf_data,'token':loginResponse['token']})
        my_logger.info(graphDBResponse)
        if 'success' in graphDBResponse:
            response['success'] = True
        if 'error' in graphDBResponse:
            response['error'] = True
        response['plans'] = params['plans']
    return response
            
def extractCoverageAmountUsingGpt(travelGuardPlanPDFUrl):
    
    resp = extract_text_from_pdf_url(travelGuardPlanPDFUrl,10)

    if resp['error'] == None:
        extractedTextFromPDF = resp['extracted_data']
    
    coverageAmount = get_extracted_coverage_amount_from_GPT(extractedTextFromPDF)
    if coverageAmount['error'] == None:
        inclusionsWithAmount = format_inclusions(coverageAmount['data'])
    else:
        inclusionsWithAmount = [
                    {
                        "coverageName": "Trip Cancellation coverage",
                        "coverageAmount": ""
                    },
                    {
                        "coverageName": "Trip Interruption",
                        "coverageAmount": ""
                    },
                    {
                        "coverageName": "Medical Evacuation",
                        "coverageAmount": ""
                    },
                    {
                        "coverageName": "Emergency Medical",
                        "coverageAmount": ""
                    },
                    {
                        "coverageName": "Baggage Loss",
                        "coverageAmount": ""
                    },
                    {
                        "coverageName": "Flight Accident",
                        "coverageAmount": ""
                    },
                    {
                        "coverageName": "Accidental Death",
                        "coverageAmount": ""
                    }
                ]
    return inclusionsWithAmount

def get_inclusion_exclusion(url,firstChunkSize,otherChunkSize):
    my_logger = get_logger("/get_inclusion_exclusion")
    response={'error':None, 'inclusion': None , 'exclusions' :None}
    coverage=["Trip Cancellation coverage", "Trip Interruption", "Medical Evacuation", "Emergency Medical", "Baggage Loss", "Flight Accident", "Accidental Death"]
    inclusion=[]
    final_inclusion=[]
    exclusion=[]
    failedError=[]
    if url is not None:
       try:
            pdfContent = extract_text_from_pdf_url(url)
            pdfContent = pdfContent['extracted_data']
            my_logger.info(pdfContent)
       except:
           error = 'extract_text_from_pdf_url function failed' 
           failedError.append(error)
           response['error'] = failedError 
           return  response    
    else:
       error='No url found for the Pdf'
       failedError.append(error)
       response['error'] = failedError 
       return  response
    
    try:
        chunks = split_into_custom_chunks(pdfContent,firstChunkSize, otherChunkSize)
    except :
        failedError.append('chunks method failed')  
        response['error']=failedError
        return response  


    if len(chunks)>0:
        # going for inclusions
        for cov in coverage:
            try:
                beforeCall=datetime.now()
                #inResult = similarity_service.get_chat_completion(get_gpt_prompt_Single(cov,chunks[1]),"gpt-3.5-turbo-16k")
                inResult = similarity_service.get_chat_completion_mistral(get_gpt_prompt_Single(cov,chunks[1]),"mistralai/Mistral-7B-Instruct-v0.2")
                afterCall=datetime.now()
                time_difference = beforeCall - afterCall

                # Getting the difference in seconds (including fractions of a second)
                difference_in_seconds = time_difference.total_seconds()
                if difference_in_seconds > 20:
                    time.sleep(0)
                else:    
                    time.sleep(20-difference_in_seconds)  
                inclusion.append(inResult)
            except:
                my_logger.info('PRINT INCLUSIONS')
                my_logger.info('Failed somehow')
                  
        # # going for exclusion
        try:
            #exResult = similarity_service.get_chat_completion(get_gpt_prompt_Single_ex(chunks[1]),"gpt-3.5-turbo-16k")
            exResult = similarity_service.get_chat_completion_mistral(get_gpt_prompt_Single_ex(chunks[1]),"mistralai/Mistral-7B-Instruct-v0.2")
            exclusion.append(exResult)
        except:
            my_logger.info('PRINT EXCLUSIONS')
            my_logger.info('Failed somehow')
            
        if len(inclusion) > 0:
            for data in inclusion:
                try:
                    my_logger.info('A11111111111111111')
                    my_logger.info(data)
                    if data['data']!=None:
                        json_data = json.loads(data['data'])
                        final_inclusion.append(json_data)
                except:
                    my_logger.info('PRINT DATA')
                    my_logger.info('Failed somehow')

            if len(final_inclusion)>0:
                response['inclusion']=final_inclusion
            else:
                failedError.append('No inclusions found or some error occured')

        


        if len(exclusion)>0:
            # print(exclusion)
            try:
                if exclusion[0]['data']!=None:
                    # print(exclusion[0]['data'])
                    json_data = json.loads(exclusion[0]['data'])
                    response['exclusions']=json_data[0]['Exclusions']
            except:
                my_logger.info('Failed somehow')
                failedError.append('No exclusion found or some error occured')

        response['error']=failedError
                   
    else:
        error='No chunks created'
        failedError.append(error)
        response['error']=failedError
    
    return response

def split_into_custom_chunks(text, first_chunk_size, other_chunk_size):
    # Check if the text is shorter or equal to the first chunk size
    # print(text)
    if len(text) <= first_chunk_size:
        return [text]
    
    # Create the first chunk
    chunks = [text[:first_chunk_size]]
    
    # Start from the end of the first chunk and create subsequent chunks of 'other_chunk_size' characters each
    for i in range(first_chunk_size, len(text), other_chunk_size):
        chunks.append(text[i:i + other_chunk_size])
    
    return chunks

def get_gpt_prompt_Single_ex(sample_data):
    gpt_prompt = f"""1.You are given sample_data delimited with triple backticks  
    2.I am also providing you the desired task to do on the data.
    3.Follow the instruction given below to answer correctly.


    Task : '''Retrive the details of exclusions or not covered details from given data'''
    
    sample_data : '''{sample_data}'''
    
    Please generate the following information in the specified output format only:

    [
      {{
        "Exclusions": [
          "Detail1",
          "Detail2",
          ...
        ]
      }}
    ]


    Instructions:
    Take your time and analyse the prompt carefylly.
    Please dont give the response before you complete the task.
    Dont miss the data as i need complete original data from the text.
    I am providing the pdf file text which includes the different-different coverage details and excluded details about the
      policy plan.
    I want the exclusion details from the input in bullet points and each bullet points should contain the one information
      about the exclusion.
    Put the data as much original as possible.
    """
    return gpt_prompt

def get_gpt_prompt_Single(task, sample_data):
    gpt_prompt = f"""1.You are given sample_data delimited with triple backticks  
    2.I am also providing you the desired task to do on the data.
    3.Follow the instruction given below to answer correctly.


    Task : '''Retrive the details of {task} inclusions or coverage details from given data'''
    
    sample_data : '''{sample_data}'''
    
    Please generate the following information in the specified format:

    [
      {{
        "coverageName": "CoverageName",
        "coverageDetails": [
          "Detail1",
          "Detail2",
          ...
        ]
      }},
      {{
        "coverageName": "CoverageName",
        "coverageDetails": [
          "Detail1",
          "Detail2",
          ...
        ]
      }},
      {{
        "coverageName": "CoverageName",
        "coverageDetails": [
          "Detail1",
          "Detail2",
          ...
        ]
      }}
    ]
  

    Instructions:
    Take your time and analyse the prompt carefylly.
    Please dont give the response before you complete the task.
    Dont miss the data as i need complete original data from the sample text for that perticular coverage.
    I am providing the pdf file text which includes the different-different coverage details about the
      policy plan.
    I want the coverge details of that perticular coverage which is mentioned in the task in bullet points and each bullet points should contain the one information 
      about the perticular coverage.
    Dont rephrase or summarise the content of the input 
    Put the data as much original as possible.
    If no details are provided for that perticular coverage just put NA 

    The pdfs might contain many coverages so create the record for the coverage which is mentioned in the task  only.  
    """
    return gpt_prompt

def getCompleteDetail(bestPlanName, insurancePlans):
    for plan in insurancePlans:
        if bestPlanName == plan.get("planName"):
            return plan

#async function
async def data_extraction(params):
    my_logger = get_logger("/extraction_Async")

    for item in params['plans']:
        item['inclusions'] = []
        item['exclusions'] = []
        if item['carrier'] == "https://www.allianztravelinsurance.com":
            quote = item['quote']
            for coverage in allianzTravelCoverages:
                cov={}
                cov["coverageName"] = coverage['id']
                #Extracting coverage amount using openai (gpt-3.5-turbo)
                cov['coverageAmount'] = find_coverage_amount_by_coverage_name(coverage["coverageName"],quote).replace("$","") if coverage['coverageName'] != "" else ""
                # cov['coverageDetails'] = []
                item['inclusions'].append(cov)
        if "https://www.travelguard.com" in item['carrier']:
            travelGuardPlanPDFUrl = item["pdfUrl"]
            item['inclusions'] = extractCoverageAmountUsingGpt(travelGuardPlanPDFUrl)

    for item in params['plans']:
        #gaurav code start here
        checkIsInclusionsExists = getInclusionsStatus(item)
        my_logger.info(checkIsInclusionsExists)
        if checkIsInclusionsExists['status'] == "No":
            get_detail_inclusions = get_inclusion_exclusion(item["pdfUrl"],10000,35000)
            #get_detail_inclusions = {'error': [], 'inclusion': [[{'coverageName': 'Trip Cancellation Coverage', 'coverageDetails': ['Refund of non-refundable trip payments, deposits, cancellation fees, and costs to rebook transportation', 'Reimbursement for additional accommodation fees if traveling companion cancels', 'Reimbursement for transportation expenses to continue trip or return home', 'Reimbursement for additional accommodation and transportation expenses if trip is interrupted', 'Coverage for trip cancellation due to illness, injury, or medical condition', "Coverage for trip cancellation due to family member's illness, injury, or medical condition", 'Coverage for trip cancellation due to quarantine', 'Coverage for trip cancellation due to traffic accident', 'Coverage for trip cancellation due to uninhabitable primary residence', 'Coverage for trip cancellation due to legal proceeding', 'Coverage for trip cancellation due to reassignment or change in leave status of U.S. Armed Forces member', 'Coverage for trip cancellation due to travel carrier delay or cancellation', 'Coverage for trip cancellation due to termination or layoff by current employer', 'Coverage for trip cancellation due to inability to receive required vaccination', 'Coverage for trip cancellation due to mandatory evacuation', "Coverage for trip cancellation due to birth of family member's child", 'Coverage for trip cancellation due to stolen travel documents', 'Coverage for trip cancellation due to uninhabitable destination', 'Coverage for trip cancellation due to separation or divorce', 'Coverage for trip cancellation due to inability to be accommodated by family or friends', 'Coverage for trip cancellation due to vehicle breakdown', 'Coverage for trip cancellation due to change in school schedule', 'Coverage for trip cancellation due to tour or event cancellation']}], [{'coverageName': 'Trip Interruption Coverage', 'coverageDetails': ['Refund Cash, credit, or a voucher for future travel that you are eligible to receive from a travel supplier, or any credit, recovery, or reimbursement you are eligible to receive from your employer, another insurance company, a credit card issuer, or any other entity.', 'Rental car An automobile or other vehicle designed for use on public roads that you have rented from a rental car company for the period of time shown in a rental car agreement for use on your trip.', 'Rental car agreement The contract issued to you by the rental car company that describes all of the terms and conditions of renting a rental car, including your responsibilities and the responsibilities of the rental car company.', 'Rental car company A commercial company licensed (where applicable) and whose primary business is renting automobiles. A rental car company does not include car or ride share companies (examples include Uber, Zipcar, and Turo), automobile dealerships, mechanics, or body shops.', 'Return date The date on which you are originally scheduled to end your travel, as shown on your travel itinerary.', 'Severe weather Hazardous weather conditions including but not limited to windstorms, hurricanes, tornados, fog, hailstorms, rainstorms, snow storms, or ice storms.', 'Traffic accident An unexpected and unintended traffic-related event, other than mechanical breakdown, that causes injury, property damage, or both.', 'Travel carrier A company licensed to commercially transport passengers between cities for a fee by land, air, or water. It does not include: 1. Rental vehicle companies; 2. Private or non-commercial transportation carriers; 3. Chartered transportation, except for group transportation chartered by your tour operator; or 4. Local public transportation.', 'Travel supplier A travel agent, tour operator, airline, cruise line, hotel, railway company, or other travel service provider.', 'Traveling companion A person or service animal (as defined by the Americans with Disabilities Act) traveling with you or traveling to accompany you on your trip. A group or tour leader is not considered a traveling companion unless you are sharing the same room with the group or tour leader.', 'Trip Your travel to, within, and/or from a location at least 100 miles from your primary residence, which is originally scheduled to begin on your departure date and end on your return date. It cannot include travel with the intent to receive health care or medical treatment of any kind, moving, or commuting to and from work, and it cannot last longer than 366 days.', 'Uninhabitable A natural disaster, fire, flood, burglary, or vandalism has caused enough damage (including extended loss of power, gas, or water) to make a reasonable person find their home or destination inaccessible or unfit for use.']}], [{'coverageName': 'Medical Evacuation', 'coverageDetails': ['Mandatory involuntary confinement by order or other official directive of a government, public or regulatory authority, or the captain of a commercial vessel on which you are booked to travel during your trip, which is intended to stop the spread of a contagious disease to which you or a traveling companion has been exposed.', 'Refund Cash, credit, or a voucher for future travel that you are eligible to receive from a travel supplier, or any credit, recovery, or reimbursement you are eligible to receive from your employer, another insurance company, a credit card issuer, or any other entity.', 'Rental car An automobile or other vehicle designed for use on public roads that you have rented from a rental car company for the period of time shown in a rental car agreement for use on your trip.', 'Rental car agreement The contract issued to you by the rental car company that describes all of the terms and conditions of renting a rental car, including your responsibilities and the responsibilities of the rental car company.', 'Rental car company A commercial company licensed (where applicable) and whose primary business is renting automobiles. A rental car company does not include car or ride share companies (examples include Uber, Zipcar, and Turo), automobile dealerships, mechanics, or body shops.', 'Return date The date on which you are originally scheduled to end your travel, as shown on your travel itinerary.', 'Severe weather Hazardous weather conditions including but not limited to windstorms, hurricanes, tornados, fog, hailstorms, rainstorms, snow storms, or ice storms.', 'Terrorist event An act, including but not limited to the use of force or violence, of any person or group(s) of persons, whether acting alone or on behalf of or in connection with any organization(s), which constitutes terrorism as recognized by the government authority or under the laws of the United States, and is committed for political, religious, ethnic, ideological, or similar purposes, including but not limited to the intention to influence any government and/or to put the public, or any section of the public, in fear. It does not include general civil disorder or unrest, protest, rioting, political risk, or acts of war.', 'Traffic accident An unexpected and unintended traffic-related event, other than mechanical breakdown, that causes injury, property damage, or both.', 'Travel carrier A company licensed to commercially transport passengers between cities for a fee by land, air, or water. It does not include: 1. Rental vehicle companies; 2. Private or non-commercial transportation carriers; 3. Chartered transportation, except for group transportation chartered by your tour operator; or 4. Local public transportation.', 'Travel supplier A travel agent, tour operator, airline, cruise line, hotel, railway company, or other travel service provider.', 'Traveling companion A person or service animal (as defined by the Americans with Disabilities Act) traveling with you or traveling to accompany you on your trip. A group or tour leader is not considered a traveling companion unless you are sharing the same room with the group or tour leader.', 'Trip Your travel to, within, and/or from a location at least 100 miles from your primary residence, which is originally scheduled to begin on your departure date and end on your return date. It cannot include travel with the intent to receive health care or medical treatment of any kind, moving, or commuting to and from work, and it cannot last longer than 366 days.', 'Uninhabitable A natural disaster, fire, flood, burglary, or vandalism has caused enough damage (including extended loss of power, gas, or water) to make a reasonable person find their home or destination inaccessible or unfit for use.']}], [{'coverageName': 'Emergency Medical/Dental Coverage', 'coverageDetails': ['Coverage for medical expenses incurred due to illness or injury during the trip', 'Coverage for dental expenses incurred due to emergency dental treatment during the trip']}], [{'coverageName': 'Baggage Loss', 'coverageDetails': ['Refund Cash, credit, or a voucher for future travel that you are eligible to receive from a travel supplier, or any credit, recovery, or reimbursement you are eligible to receive from your employer, another insurance company, a credit card issuer, or any other entity.']}], [{'coverageName': 'Flight Accident', 'coverageDetails': ['Coverage for losses resulting from a flight accident', 'Includes coverage for injuries, property damage, or both caused by an unexpected and unintended traffic-related event during the flight', 'Does not cover mechanical breakdowns', 'Coverage effective from the day after the policy is purchased and the full premium is paid', 'Coverage ends on the earliest of the Coverage End Date listed in the Coverage Summary, cancellation of the policy, cancellation of the trip, end of the trip, arrival at a medical facility for further care, 180th day of the trip without return travel arrangements, 366th day of the trip, or 1,096th day after the policy purchase date', 'Coverage can be extended if the return travel is delayed due to a reason covered under the policy', 'Plan price is nonrefundable after the policy ends', 'Policy applies for a specific trip and cannot be renewed']}], [{'coverageName': 'Accidental Death', 'coverageDetails': ['An unexpected and unintended traffic-related event, other than mechanical breakdown, that causes injury, property damage, or both.']}]], 'exclusions': ['Any loss, condition, or event that was known, foreseeable, intended, or expected when your policy was purchased.', 'A pre-existing medical condition, except as waived under the Pre-Existing Medical Condition Exclusion Waiver.', 'Normal pregnancy or childbirth, except when and to the extent that normal pregnancy or childbirth is expressly referenced in and covered under Trip Cancellation Coverage or Trip Interruption Coverage.', 'Fertility treatment or elective abortion.', 'The use or abuse of alcohol or drugs, or any related physical symptoms. This does not apply to drugs prescribed by a doctor and used as prescribed.', 'An act committed with the intent to cause loss.', 'Operating or working as a crew member (including as a trainee or learner/student) aboard any aircraft or commercial vehicle or commercial watercraft.', 'Participating in or training for any professional sporting competition.', 'Participating in or training for any amateur sporting competition while on your trip. This does not include participating in informal recreational sporting competitions, such as tournaments organized by hotels, resorts, or cruise lines to entertain their guests.', 'Participating in an extreme, high-risk sport or activity, such as skydiving, BASE jumping, hang gliding, or parachuting.', 'A criminal act resulting in a conviction, except when you, a traveling companion, or a family member is the victim of such act.', 'An epidemic or pandemic, except when and to the extent that an epidemic or pandemic is expressly referenced in and covered under Trip Cancellation Coverage, Trip Interruption Coverage, Travel Delay Coverage, or Emergency Medical/Dental Coverage.', 'A natural disaster, except when and to the extent that a natural disaster is expressly referenced in and covered under Trip Cancellation Coverage, Trip Interruption Coverage, or Travel Delay Coverage.', 'Air, water, or other pollution, or the threat of a pollutant release, including thermal, biological, and chemical pollution or contamination.', 'Nuclear reaction, radiation, or radioactive contamination.', 'War (declared or undeclared) or acts of war.', 'Military duty, except when and to the extent that military duty is expressly referenced in and covered under Trip Cancellation Coverage or Trip Interruption Coverage.', 'Political risk.', 'Cyber risk.', 'Civil disorder or unrest, except when and to the extent that civil disorder or unrest is expressly referenced in and covered under Trip Interruption Coverage or Travel Delay Coverage.', 'A terrorist event, except when and to the extent that a terrorist event is expressly referenced in and covered under Trip Cancellation Coverage, Trip Interruption Coverage, or Travel Delay Coverage.', 'An act, travel alert/bulletin, or prohibition by any government or public authority, except when and to the extent that an act, travel alert/bulletin, or prohibition by a government or public authority is expressly referenced in and covered under Trip Cancellation Coverage or Trip Interruption Coverage.', 'Any travel supplier’s complete cessation of operations due to financial condition, with or without filing for bankruptcy, except when and to the extent that a traveler supplier’s complete cessation of operations due to financial condition is expressly referenced in and covered under Trip Cancellation Coverage or Trip Interruption Coverage.', 'A travel supplier’s restriction on any baggage, including on medical supplies or equipment.', 'Ordinary wear and tear or defective materials or workmanship.', 'An act of gross negligence by you or a traveling companion.', 'Travel against the orders or advice of any government or other public authority.']}
            if get_detail_inclusions['inclusion'] != None:
                for incItem in get_detail_inclusions['inclusion']:
                    for mainItem in item['inclusions']:
                        string_1 = mainItem['coverageName'].lower()
                        string_2 = incItem[0]['coverageName'].lower()
                        if string_1 in string_2:
                            if len(incItem[0]['coverageDetails']) > 15:
                                mainItem['coverageDetails'] = incItem[0]['coverageDetails']
                    
            if get_detail_inclusions['exclusions'] != None:
                item['exclusions'] = get_detail_inclusions['exclusions']

    #update plan request with inclusions and exclusions data in graph db
    graphdbResponse = insertDataIntoGraphDB({'plans':params['plans'], "input_info": params['input_info']})
    my_logger.info('GraphDB Response')
    my_logger.info(graphdbResponse)


def getSparqlQueryForInclusionsFromPlanName(productId):
    query = f"""
            PREFIX gr: <http://www.griffin.org/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT (CONCAT('[', GROUP_CONCAT(?json; separator=",") ,']') AS ?inclusions)
            WHERE {{
                
                {{
                    SELECT ?quote ?coverageName (GROUP_CONCAT(?coverageDetails; separator='","') AS ?details)
                    WHERE {{
                        ?quote a gr:Quote;
                            gr:productId ?productId.

                        optional{{ 
                            ?quote gr:includes [gr:inclusion ?coverageIRI].
                        	?coverageIRI rdfs:label ?coverageName.
                			optional{{ 
                    			?coverageIRI gr:inclusionDetails ?coverageDetails.}}
                        }}
                    filter(?productId = "{productId}")
                    }} GROUP BY ?quote ?coverageName
                }}
                BIND(
                    CONCAT(
                        '{{ "coverageName": "', ?coverageName, '", ',
                        '"coverageDetails": ["', ?details, '"] }}'
                    ) AS ?json
                )
                
            }} GROUP BY ?quote
            """
    return query

def getSparqlQueryForExclusionsFromPlanName(productId):
    query = f""" 
        PREFIX gr: <http://www.griffin.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?exclusion 
        where
        {{
            ?quote a gr:Quote;
                gr:productId ?productId.
            filter(?productId = "{productId}")
            ?quote gr:excludes [gr:exclusionsDetails ?exclusion]

        }}
    """
    
    return query

def mergeInclusions(inclusionDetails, item):
    allInclusions = []
    for inclusion in item['inclusions']:
        for inclusionDetail in inclusionDetails:
            if inclusionDetail['coverageName'] == inclusion['coverageName']:
                inclusionDict={}
                inclusionDict['coverageName'] = inclusion['coverageName']
                inclusionDict["coverageAmount"] = inclusion['coverageAmount']
                inclusionDict['coverageDetails'] = inclusionDetail['coverageDetails']
                allInclusions.append(inclusionDict)
                break
    item['inclusions'] = allInclusions
    return item

def getInclusionExclusionSummaryForAllPlansFromGraphDB(plans):
    result = {"error":None, "best_plan":None, "plans": None}

    for  item in plans:
        #get all the extracted inclusions from graphDB
        queryToGetAllInclusions = getSparqlQueryForInclusionsFromPlanName(item['productId'])
        
        loginResponse  = graphdb_service.login()
        paramsForInclusions = {
            'query': encodeURIComponent(queryToGetAllInclusions),
            'token': loginResponse.get('token'),
            'repositoryID': DEFAULT_GRAPHDB_REPO
        }
        resp=graphdb_service.execute_sparql_query(paramsForInclusions)
        if resp['error'] == None:
            parsedJSON = parse_json_response(resp['result'])
            if parsedJSON:
                inclusionDetails = json.loads(parsedJSON[0]['inclusions'])
                item = mergeInclusions(inclusionDetails, item)
        else:
            result['error']=resp['error']

        #get all the extracted exclusions from graphDB
        queryToGetAllExclusions = getSparqlQueryForExclusionsFromPlanName(item['productId'])
        paramsForExclusions = {
            'query': encodeURIComponent(queryToGetAllExclusions),
            'token': loginResponse.get('token'),
            'repositoryID': DEFAULT_GRAPHDB_REPO
        }
        
        resp = graphdb_service.execute_sparql_query(paramsForExclusions)
        if resp['error'] == None:
            parsedJSON = parse_json_response(resp['result'])
            if parsedJSON:
                exclusions = [exc['exclusion'] for exc in parsedJSON]
                item['exclusions'] = exclusions
            else:
                item['exclusions'] = []

        else:
            result['error']=resp['error']

        #get summary from graphDB using planID
        queryToGetSummary = getSparqlQueryForSummaryFromPlanName(item['productId'])
        paramsForSummary = {
            'query': encodeURIComponent(queryToGetSummary),
            'token': loginResponse.get('token'),
            'repositoryID': DEFAULT_GRAPHDB_REPO
        }
        
        resp=graphdb_service.execute_sparql_query(paramsForSummary)
        if resp['error'] == None:
            parsedJSON=parse_json_response(resp['result'])
            summary = parsedJSON[0]['summary']
            item['summary'] = summary
        else:
            result['error']=resp['error']
    
    result['plans'] = plans

    return result

def getTheReasonForBestPlan(bestPlan, plans):
    result = {"error":None, "bestPlan":bestPlan}

    bestPlanName = bestPlan['planName']

    promptToGetTheReason = getPromptForReasonBehindTheBestAlgo(bestPlanName, plans)
    #gptResults = similarity_service.get_chat_completion(promptToGetTheReason,"gpt-3.5-turbo")
    gptResults = similarity_service.get_chat_completion_mistral(promptToGetTheReason,"mistralai/Mistral-7B-Instruct-v0.2")
    
    if gptResults['error'] == None:
        result['bestPlan']['reason'] =  json.loads(gptResults['data'])['reasons']
    else:
        result['error']=gptResults['error']
        result['bestPlan']['reason'] = []
    
    return result

async def getLangChainSummarization(plan):
    my_logger = get_logger("/getLangChainSummarization")
    summary = similarity_service.getLangChainSummarization(plan['pdfUrl']);
    loginResponse = graphdb_service.login()
    rdf_data = f'''
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix gr: <http://www.griffin.org/> .
            @prefix pro: <http://property.org/resource/> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
             
        '''
    rdf_data += f'''
                    # Individual Quotes
                    gr:{plan['productId']} gr:summary <http://www.griffin.org/{plan['productId']}/summary> .
                    <http://www.griffin.org/{plan['productId']}/summary> gr:summary "{clean_description(summary)}" ;
                    rdfs:label "Summary" .
                '''
    # my_logger.info(rdf_data)
    graphDBResponse = graphdb_service.add_rdf_statement({'repositoryID':DEFAULT_GRAPHDB_REPO,'rdfData':rdf_data,'token':loginResponse['token']})
    # my_logger.info(graphDBResponse) 
    
def getSummaryStatus(plans):
    result = {}
    loginResponse = graphdb_service.login()
    formatted_ids = ""
    for item in plans:
        formatted_ids += f''' ("{item['productId']}") '''
         

    query = f'''
        PREFIX gr: <http://www.griffin.org/>

        SELECT ?productId (IF(?summaryExists, "Yes", "No") AS ?summaryStatus)
        WHERE {{
            VALUES (?productId) {{ {formatted_ids} }}
            {{
                SELECT ?productId (COUNT(?summary) AS ?summaryExists)
                WHERE {{
                    ?s a gr:Quote ;
                        gr:productId ?productId .
                    OPTIONAL {{
                        ?s gr:summary [ gr:summary ?summary ] .
                    }}
                }}
                GROUP BY ?productId
            }}
        }}


    '''
    queryResponse = graphdb_service.execute_sparql_query({"repositoryID":DEFAULT_GRAPHDB_REPO,'token':loginResponse['token'],'query':query})    
    if len(queryResponse['result']['results']['bindings']) > 0:
        for item in queryResponse['result']['results']['bindings']:
            if item['summaryStatus']['value'] == "Yes":
                result[item['productId']['value']] = item['summaryStatus']['value']   
    
    return result

def getSparqlQueryForSummaryFromPlanName(productId):
    query = f""" 
        PREFIX gr: <http://www.griffin.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        select ?summary where {{
            ?s a gr:Quote ;
            gr:productId ?productId .
            ?s gr:summary [gr:summary ?summary] .
            filter(?productId = "{productId}")
        }} LIMIT 1
    """
    return query


def getInclusionsStatus(plan):
    result = {"status":"No"}
    loginResponse = graphdb_service.login()
    formatted_ids = f''' ("{plan['productId']}") '''
    
    query = f'''
        PREFIX gr: <http://www.griffin.org/>

        SELECT ?productId (IF(?inclusionStatusExists, "Yes", "No") AS ?status)
        WHERE {{
            VALUES (?productId) {{ {formatted_ids} }}
            {{
                SELECT ?productId (COUNT(?inclusionstatus) AS ?inclusionStatusExists)
                WHERE {{
                    ?s a gr:Quote ;
                        gr:productId ?productId .
                    OPTIONAL {{
                        ?s gr:inclusionsStatus ?inclusionstatus .
                    }}
                }}
                GROUP BY ?productId
            }}
        }}

    '''
    queryResponse = graphdb_service.execute_sparql_query({"repositoryID":DEFAULT_GRAPHDB_REPO,'token':loginResponse['token'],'query':query})    
    if len(queryResponse['result']['results']['bindings']) > 0:
        for item in queryResponse['result']['results']['bindings']:
            result['status'] = item['status']['value']
               
    return result

def getPromptForReasonBehindTheBestAlgo(bestPlanName, plans):

    plansItems = copy.copy(plans)
    for item in plansItems:
        del item['quote']
    
    query = f'''You are given insurance plans which includes list of inclusions, planCost, commission and serviceProvider.
                You are also given a bestPlanName among these plans.
            Task: Your task is to send me summerized points why the given bestPlan is best plan from the given plans
            plans: {plansItems}
            bestPlanName: {bestPlanName}
            how we selected the bestPlanName:
            Coverages in their order: ["Trip Cancellation coverage", "Trip Interruption", "Medical Evacuation", "Emergency Medical", "Baggage Loss", "Flight Accident", "Accidental Death"]
            
            Our formula: (coverageAmount/costPlan) * commission



            Instructions:
            - Take your time to read the given data and analyze the prompt carefully.
            - Please dont give the response before you complete the task.
            - I need you to send me the summerized points why the given bestPlan document is best among the plans.
            - Please ensure that you don't have to tell about the formula in output.
            - please don't include 'how we selected the bestPlanName' formula which is under this string.
            - please follow return format for output strictly.


            return format:
            {{
                "reasons":["reason1", "reason2", "reason3",.......]
            }}


             
            '''
    return query


def queryToUpdateCountForWinnings(plan_uri):
    return f'''PREFIX gr: <http://www.griffin.org/>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

                delete{{
                    ?quote gr:numberOfWinnings ?numberOfWinnings.
                }}
                insert {{
                    ?quote gr:numberOfWinnings ?newNumberOfWinnings.
                        }}


                where {{
                    ?quote a gr:Quote;
                        gr:numberOfWinnings ?numberOfWinnings.
                    
                    filter(?quote=<{plan_uri}>)
                    
                    BIND((xsd:integer(?numberOfWinnings) + 1) AS ?newNumberOfWinnings)
                    }}'''

def markWinningQuote(request_uri:str, plan_uri:str, plan_name:str, bestPlanReason:list):

    loginResponse = graphdb_service.login()
    my_logger = get_logger("/markWinningQuote")
    response ={}
    if "token" in loginResponse:
        rdf_data = f''' 
                <{request_uri}> gr:winningQuote "{plan_uri}" ;
                    gr:winningQuoteName "{plan_name}" .
        '''
        if bestPlanReason:
            for reason in bestPlanReason:
                rdf_data += f''' 
                <{request_uri}> gr:winningQuoteReason "{reason}".
        '''
        graphDBResponse = graphdb_service.add_rdf_statement({'repositoryID':DEFAULT_GRAPHDB_REPO,'rdfData':rdf_data,'token':loginResponse['token']})
        
        graphDBResponse2 = graphdb_service.update_rdf_statement({"repositoryID":DEFAULT_GRAPHDB_REPO,'rdfData':queryToUpdateCountForWinnings(plan_uri),'token':loginResponse.get('token')})
        my_logger.info("count response: ")
        my_logger.info(graphDBResponse2)
        
        if 'success' in graphDBResponse:
            response['success'] = True
        if 'error' in graphDBResponse:
            response['error'] = True
    return response


def get_summary_reasons_for_winning_reason_from_gpt(winningPlanReasons):
    result = {"error": None, "summaryReasons": None}
    my_logger = get_logger("/get-summary-reason")
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(f'{GET_SUMMARY_REASONS}', data = json.dumps({"reasons":winningPlanReasons}), headers = headers)
        if response.status_code == 200:
            response = response.json()
            if response['error'] == None:
                result['summaryReasons'] = response['summaryReason']
            else:
                result['error'] = response['error']
        elif response.status_code == 404 :
            result['error'] = response.get('error')             
        else:
            result['error'] = 'Summary reason not found'
    except Exception as e:
        my_logger.error(e)
        result['error'] = e
    return result

def queryToGetWinningPlanReasons(plan_uri):
    return f"""
            PREFIX gr: <http://www.griffin.org/>
            SELECT (CONCAT("[", GROUP_CONCAT(CONCAT('"', ?reason, '"'); separator=", "), "]") as ?reasons)
            WHERE {{
                ?s a gr:TravellerRequest;
                gr:winningQuote ?quote;
                gr:winningQuoteReason ?reason .
                FILTER(?quote = "{plan_uri}")
            }}
            GROUP BY ?s"""

def queryToCheckSUmmaryReasonStatus(plan_uri):
    return f"""PREFIX gr: <http://www.griffin.org/>
            ASK where {{
                ?s gr:summaryOfReasons ?summaryOfReasons .
                filter(?s = <{plan_uri}>)
            }}"""

def queryToUpdateaSummaryReasons(plan_uri, summaryOfReasons):
    summaryOfReasonTriple = ""
    for item in summaryOfReasons:
        summaryOfReasonTriple += f''' "{item}",'''
    
    summaryOfReasonTriple = summaryOfReasonTriple[:-1]
    
    return f'''PREFIX gr: <http://www.griffin.org/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            delete{{
                ?quote gr:summaryOfReasons ?summaryOfReasons.
            }}
            insert {{
                ?quote gr:summaryOfReasons {summaryOfReasonTriple} .
                    }}

            where {{
                ?quote a gr:Quote;
                    gr:summaryOfReasons ?summaryOfReasons.
                
                filter(?quote=<{plan_uri}>)
                }}
            '''

async def updateSummaryReason(plan_uri):
    my_logger = get_logger("/update-Summary-reason")
    #To get all winning plan reasons for a plan_uri
    queryForPlanReasons = queryToGetWinningPlanReasons(plan_uri)
    loginResponse  = graphdb_service.login()
    paramsForReasons = {
        'query': encodeURIComponent(queryForPlanReasons),
        'token': loginResponse.get('token'),
        'repositoryID': DEFAULT_GRAPHDB_REPO
    }
    resp=graphdb_service.execute_sparql_query(paramsForReasons)

    if resp['error'] == None:
        parsedJSON=parse_json_response(resp['result'])
        winningPlanReasons = [json.loads(reason['reasons']) for reason in parsedJSON]
        #To get summary reasons for all winning plan reasons using openai
        summaryReasonResponse = get_summary_reasons_for_winning_reason_from_gpt(winningPlanReasons)

        if summaryReasonResponse["summaryReasons"] != None:

            #To check the summary reason are already in graphDB or not
            queryToCheckStatusOfSummaryReasons = queryToCheckSUmmaryReasonStatus(plan_uri)
            paramsForSummaryReasonsStatus = {
                'query': encodeURIComponent(queryToCheckStatusOfSummaryReasons),
                'token': loginResponse.get('token'),
                'repositoryID': DEFAULT_GRAPHDB_REPO
            }
            summaryReasonStatusResponse=graphdb_service.execute_sparql_query(paramsForSummaryReasonsStatus)
            
            if summaryReasonStatusResponse['error'] == None:
                summaryReasonStatus = summaryReasonStatusResponse['result']['boolean']

                if summaryReasonStatus == False:
                    #If there is not existing summary reason on graphDB [for first time summary reason ingestion]
                    summaryReasonTriples = ""
                    for summaryReason in summaryReasonResponse["summaryReasons"]:
                        summaryReasonTriples += f'''<{plan_uri}> gr:summaryOfReasons "{summaryReason}".'''
                    
                    queryToIngestSummaryReasonForFirstTime = f'''PREFIX gr: <http://www.griffin.org/>
                                                            INSERT DATA{{
                                                            {summaryReasonTriples}
                                                            }}'''
                    
                    res = graphdb_service.update_rdf_statement({"repositoryID":DEFAULT_GRAPHDB_REPO,'rdfData':queryToIngestSummaryReasonForFirstTime,'token':loginResponse.get('token')})
                    my_logger.info("Summary of reasons (first time): ")
                    my_logger.info(res)
                else:
                    #If there is existing summary reason on graphDB [to update the summary reason on graphDB]
                    queryToUpdateExistingSummaryReasons = queryToUpdateaSummaryReasons(plan_uri, summaryReasonResponse["summaryReasons"])
                    
                    res = graphdb_service.update_rdf_statement({"repositoryID":DEFAULT_GRAPHDB_REPO,'rdfData':queryToUpdateExistingSummaryReasons,'token':loginResponse.get('token')})
                    my_logger.info("Summary of reasons (update): ")
                    my_logger.info(res)
            else:
                my_logger.info(summaryReasonStatusResponse['error'])
        else:
            my_logger.info(summaryReasonResponse['error'])
    else:
        my_logger.info(resp['error'])

def getInclusionExclusion(plans):
    #implement surjeet work here
    for item in plans:
        item['inclusions'] = []
        item['exclusions'] = []
        item['allAvailableInclusions'] = []
        if item['carrier'] == "https://www.allianztravelinsurance.com":
            quote = item['quote']
            for coverage in allianzTravelCoverages:
                cov={}
                cov["coverageName"] = coverage['id']
                #Extracting coverage amount using openai (gpt-3.5-turbo)
                cov['coverageAmount'] = find_coverage_amount_by_coverage_name(coverage["coverageName"],quote).replace("$","") if coverage['coverageName'] != "" else ""
                # cov['coverageDetails'] = []
                item['inclusions'].append(cov)
                if cov['coverageAmount'] != "" and cov['coverageAmount'] != None and cov['coverageAmount'] != "0":
                    item['allAvailableInclusions'].append(cov['coverageName'])
        if "https://www.travelguard.com" in item['carrier']:
            travelGuardPlanPDFUrl = item["pdfUrl"]
            item['inclusions'] = extractCoverageAmountUsingGpt(travelGuardPlanPDFUrl)

            for inc in item['inclusions']:
                if inc['coverageAmount'] != "" and inc['coverageAmount'] != None and inc['coverageAmount'] != "0":
                    item['allAvailableInclusions'].append(inc['coverageName'])

    return plans

