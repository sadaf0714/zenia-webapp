# This file contains all the util methods
import io
from ariadne import format_error
from graphql import GraphQLError
from models.company import Company
import urllib.parse as urllp
from config.log_config import get_logger
from config.constant import STANDARD_COMP_FIELDS, GRAPHDB_SIMILARITY_INDEX_NAME, STANDARD_COMP_FIELDS_LINKEDIN, STANDARD_COMP_FIELDS_DBPEDIA, STANDARD_COMP_FIELDS_YAHOO, GRAPHDB_SERVICE_SHOWKG_HTTP_URL
import re
import string
import pdfplumber
import requests

my_logger = get_logger("/util")

#load schema file into typedef
def load_schema_from_path(path: str) -> str:
    with open(path, "r") as file:
        return file.read()

def my_format_error(error: GraphQLError, debug: bool = False) -> dict:
    if debug:
        # If debug is enabled, reuse Ariadne's formatting logic (not required)
        return format_error(error, debug)

    # Create formatted error data
    formatted = error.formatted
    # Replace original error message with custom one
    #formatted["message"] = "INTERNAL SERVER ERROR"
    errorResponse= {"message":""}
     
    errorResponse["message"] = formatted["message"]
    return errorResponse

def handle_similar_result(data):
    similar_company_list = []
    for obj in data:
        company = Company(obj)
        my_logger.info(vars(company))
        similar_company_list.append(company)
    return similar_company_list

def classify_text(data_string):
        
    text_classified = find_active_inactive_criteria(data_string)

    resutls = {"active":{},"inactive":{}}
    sample_content  = {
            "operating_years":["operating","business",'businesses','operating business'],
            "no_of_employees":["number of employee","number of employees",'employees','total employees'],
            "invest_funding":["investment funding","funding",'investment'],
            "quarterly_growth":["growth quarterly","in every three months",'three months','in each quarter'],
            "annual_growth":["growth yearly","growth annually",'growth annual','every annual',"every year","a year"]
        }
    if(len(text_classified) > 0):
        for key in sample_content :            
            for element in sample_content[key] :      
                for string in text_classified['active'] :
                    if element in string :
                        get_number = string.split(' ')[0];
                        resutls['active'][key] = get_number.replace("%", "")
                for string in text_classified['inactive'] :
                    if element in string :
                        get_number = string.split(' ')[0];
                        resutls['inactive'][key] = get_number.replace("%", "")
                        
    return resutls;

def find_active_inactive_criteria(data_string):
    results = {}
    active_start = data_string.find("ACTIVE") + len("ACTIVE")
    active_end = data_string.find("INACTIVE")

    # Extract the "ACTIVE" criteria
    active_criteria = data_string[active_start:active_end].strip().split('\n')

    # Find the starting and ending positions of the "INACTIVE" section
    inactive_start = data_string.find("INACTIVE") + len("INACTIVE")
    inactive_end = data_string.find("Others")

    # Extract the "INACTIVE" criteria
    inactive_criteria = data_string[inactive_start:inactive_end].strip().split('\n')

    results['active'] = active_criteria
    results['inactive'] = inactive_criteria

    return results 

def multiple_array_to_comma(json_object, key):
    # Extract names from the JSON object
    names = [obj[key] for obj in json_object]

    # Create string with names separated by commas and enclosed in single quotes
    names_string = ", ".join([f"'{name}'" for name in names])

    return names_string

def array_to_comma(json_object):
    names_string = ", ".join([f"'{name}'" for name in json_object])
    return names_string


#===============SHOW KG SPARQL QUERY BUILDER==================
def config_query(data: list):
    uris = ' '.join('<' + get_proper_url_company(encodeURIComponent(item.get("name", ""))) + '>' + ',' for item in data)
    uris = uris[0: len(uris) - 1]  # removing extra comma from uris
    query = f'''PREFIX dbp: <http://dbpedia.org/property/> 
                PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                PREFIX dbr1: <https://www.linkedin.com/company/> 
                PREFIX dbr2: <https://dbpedia.org/resource/> 
                PREFIX dbo: <http://dbpedia.org/ontology/> 
                PREFIX dbr3: <https://www.salesforce.com/company/> 
                PREFIX dbr_gkg: <https://www.zeniagraphgkg.com/company/> 
                PREFIX dbr_scrap: <https://www.zeniagraphscrap.com/company/> 
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                PREFIX pro: <http://property.org/resource/> 
                PREFIX node: <http://property.org/node/> 
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#> 
                PREFIX com: <https://company.org/resource/> 
                PREFIX dbr4: <https://www.zoominfo.com/company/> 
                CONSTRUCT {{ 
                    ?company a dbo:Organisation .
                }} 
                WHERE {{ 
                    ?company a dbo:Organisation .                         
                    FILTER (?company IN ({uris}))
                }}'''
    query = query.replace("\n", "")
    my_logger.info(query)
    return encodeURIComponent(query)

#===============SHOW KG IN CASE OF EVENT SELECTION==================
def config_query_event(data: list):
    uris = ' '.join('<' + get_proper_url_company(encodeURIComponent(item.get("name", ""))) + '>' + ',' for item in data)
    uris = uris[0: len(uris) - 1]  # removing extra comma from uris
    query = f'''PREFIX dbp: <http://dbpedia.org/property/> 
                PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                PREFIX dbr1: <https://www.linkedin.com/company/> 
                PREFIX dbr2: <https://dbpedia.org/resource/> 
                PREFIX dbo: <http://dbpedia.org/ontology/> 
                PREFIX dbr3: <https://www.salesforce.com/company/> 
                PREFIX dbr_gkg: <https://www.zeniagraphgkg.com/company/> 
                PREFIX dbr_scrap: <https://www.zeniagraphscrap.com/company/> 
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                PREFIX pro: <http://property.org/resource/> 
                PREFIX node: <http://property.org/node/> 
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#> 
                PREFIX com: <https://company.org/resource/> 
                PREFIX dbr4: <https://www.zoominfo.com/company/> 
                CONSTRUCT {{ 
                    ?company a dbo:Organisation .
                    ?company dbo:employees ?employer .
                }} 
                WHERE {{ 
                    ?company a dbo:Organisation ;
                        dbo:source ?source .
                    ?source dbo:employees ?employer .

                    FILTER (?company IN ({uris}))
                }}'''
    query = query.replace("\n", "")
    my_logger.info(query)
    return encodeURIComponent(query)

#===============SHOW SIMILARY COMPANY KG SPARQL QUERY BUILDER BY GRAPH==================
def config_graph_query(data:list):
    uris = ' '.join('<' + get_proper_urls(item.get("source", ""), encodeURIComponent(item.get("name", ""))) + '>' + ',' for item in data)
    uris = uris[0: len(uris) - 1]  # removing extra comma from uris
    for x in data:
        temp = float(x.get("vector_score", ""))
        temp = "{:.4f}".format(round(temp, 4))
        x['vector_score'] = temp
    score_uris = ' '.join('(<' + get_proper_urls(item.get("source", ""), encodeURIComponent(item.get("name", ""))) + '>' + '<http://property.org/resource/' + item.get("vector_score", "") + '> )' for item in data)
    
    query = f'''PREFIX dbp: <http://dbpedia.org/property/> PREFIX foaf: <http://xmlns.com/foaf/0.1/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX dbr1: <https://www.linkedin.com/company/> PREFIX dbr2: <https://dbpedia.org/resource/> PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dbr3: <https://www.salesforce.com/company/> PREFIX dbr_gkg: <https://www.zeniagraphgkg.com/company/> PREFIX dbr_scrap: <https://www.zeniagraphscrap.com/company/> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> PREFIX pro: <http://property.org/resource/> PREFIX node: <http://property.org/node/> PREFIX vcard: <http://www.w3.org/2006/vcard/ns#> PREFIX com: <https://company.org/resource/> PREFIX dbr4: <https://www.zoominfo.com/company/> CONSTRUCT {{ ?company a dbo:Organisation; dbo:source ?data . ?data dbo:score ?score . }} WHERE {{ VALUES (?link ?value) {{ {score_uris} }} bind(?link as ?data) bind(?value as ?score) ?company a dbo:Organisation ; dbo:source ?data . FILTER (?data IN ({uris})) }}'''
    my_logger.info(query)
    return encodeURIComponent(query)

#===============SHOW SIMILARY COMPANY KG SPARQL QUERY BUILDER BY REDIS WITHOUT SOURCE==================
def config_graph_query_redis(data:list):
    uris = ' '.join('<' + get_proper_url_company(encodeURIComponent(item.get("name", ""))) + '>' + ',' for item in data)
    uris = uris[0: len(uris) - 1]  # removing extra comma from uris
    
    score_uris = ' '.join('(<' + get_proper_url_company(encodeURIComponent(item.get("name", ""))) + '>' + '<http://property.org/resource/' + item.get("vector_score", "") + '> )' for item in data)
     
    query = f'''PREFIX dbp: <http://dbpedia.org/property/> 
                PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                PREFIX dbr1: <https://www.linkedin.com/company/> 
                PREFIX dbr2: <https://dbpedia.org/resource/> 
                PREFIX dbo: <http://dbpedia.org/ontology/> 
                PREFIX dbr3: <https://www.salesforce.com/company/> 
                PREFIX dbr_gkg: <https://www.zeniagraphgkg.com/company/> 
                PREFIX dbr_scrap: <https://www.zeniagraphscrap.com/company/> 
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                PREFIX pro: <http://property.org/resource/> 
                PREFIX node: <http://property.org/node/> 
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#> 
                PREFIX com: <https://company.org/resource/> 
                PREFIX dbr4: <https://www.zoominfo.com/company/> 
                CONSTRUCT {{ 
                    ?company a dbo:Organisation; 
                        dbo:score ?score . 
                }} 
                WHERE {{ 
                        VALUES (?link ?value) {{ {score_uris} }} bind(?link as ?company) bind(?value as ?score) ?company a dbo:Organisation .                            
                        FILTER (?company IN ({uris})) 
                }}
            '''
    
    query = query.replace("\n", "")
    my_logger.info(query)
    return encodeURIComponent(query)


def get_proper_urls(source, name):
    d = {}
    d["salesforce"] = "https://www.salesforce.com/company/"
    d["linkedin"] = "https://www.linkedin.com/company/"
    d["dbpedia"] = "https://dbpedia.org/resource/"
    #d["gkg"] = "https://www.zeniagraphgkg.com/company/"
    d["others"] = "https://www.othersource.com/company/"
    d["zoominfo"] = "https://www.zoominfo.com/company/"
    d["yahoo_finance"] = "https://finance.yahoo.com/quote/"
    uri = d.get(source, "https://www.dummy/uri/") + name.strip()
    return uri

def get_proper_url_company(name):
    uri = 'https://company.org/resource/' + name.strip()
    return uri;

def get_proper_url_jobs_candidate(name):
    uri = 'http://example.org/candid/' + name.strip()
    return uri;

def get_proper_url_jobs(name):
    uri = 'https://www.linkedin.com/jobs/view/' + name.strip()
    return uri;

def encodeURIComponent(s): return urllp.quote(s, safe='/', encoding='utf-8', errors=None)

def removeNonEnglishWords(s): 
    s=re.sub(r'[^\x00-\x7F]+', '', s)
    return s

def cleanStringAndEncode(s):
    s= s.replace(".","").replace("/","")
    return urllp.quote(s, safe='/',encoding='utf-8', errors=None)

def decodeComponent(s): return urllp.unquote(s,encoding='utf-8' , errors=None);

def create_rdf_data(data, source, custom_fields):
    statements = "";

    industry  = encodeURIComponent(data.get('industry'));
    headquarters = encodeURIComponent(data.get('headquarters'))
    country = encodeURIComponent(data.get('country'))
    name = encodeURIComponent(data.get('name').strip().replace(" ", "_"))
    quarterly_growth = data.get('quarterly_growth')
    annual_growth = data.get('annual_growth')
    no_of_employees = data.get('no_of_employees')
    founded = data.get('founded')
    sales = data.get('sales')
    yearly_revenue_2022 = data.get('yearly_revenue_2022')
    last_quarterly_revenue = data.get('last_quarterly_revenue') 
    second_last_quarterly_revenue = data.get('second_last_quarterly_revenue')
    social_url = data.get('social_url')
    yearly_revenue_2021 = data.get('yearly_revenue_2021')
    website= data.get('website')
    company_type = data.get('type')
    assets = data.get('assets')
    profit = data.get('profit')
    article = data.get('article') if data.get('article')!="" else ""
    sic_code = data.get('SIC')
    naics_code = data.get('NAICS')
    company_size = data.get('company_size')
    timestamp = data.get('timestamp')
    manual = "Yes" if data.get('manual')=="YES" else "No"  
     
    prefix = ''
    node_label =  ''

    match source:
        case 'linkedin':
            prefix = "<https://www.linkedin.com/company/"+name+">" 
            node_label = "LinkedIn" 
        case 'dbpedia':
            prefix = "<https://dbpedia.org/resource/"+name+">" 
            node_label = "DBPedia"
        case 'zoominfo':
            prefix = "<https://www.zoominfo.com/company/"+name+">" 
            node_label = "ZoomInfo" 
        case "salesforce":
            prefix = "<https://www.salesforce.com/company/"+name+">"
            node_label = "Salesforce"
        case "gkg":
            prefix = "<https://www.zeniagraphgkg.com/company/"+name+">"
            node_label = "GKG"
        case "scrap":
            prefix = "<https://www.zeniagraphscrap.com/company/"+name+">"
            node_label = "Scrap" 
    
    custom_properties = "";
    custom_prop_subject = f'<http://property.org/resource/{name + "_" + node_label + "_Properties"}>'
    for index, (key, value) in enumerate(custom_fields.items()):
        transform_to_arr = value.split(',')
        if len(transform_to_arr) > 1:
            custom_properties += f'{custom_prop_subject} <http://xmlns.com/foaf/0.1/{encodeURIComponent(key)}> <http://property.org/resource/{encodeURIComponent(key)}> .'      
            z = 1
            for ob in transform_to_arr:
                dup_key = clean_description(key)
                dynamic_key = f'{dup_key.replace(" ","_")}_{z}'
                z = z + 1             
                custom_properties += f'<http://property.org/resource/{encodeURIComponent(key)}> <http://xmlns.com/foaf/0.1/{dynamic_key}> <http://property.org/resource/{encodeURIComponent(ob)}> .'            
                
        else:
            custom_properties += f'{custom_prop_subject} <http://xmlns.com/foaf/0.1/{encodeURIComponent(key)}> <http://property.org/resource/{encodeURIComponent(value)}> .' 
             
    statements  = f'''
            {prefix} a dbo:Company;
                dbp:name "{name}";
                {"node:industry <http://property.org/resource/"+industry+">;" if industry!="" else "" }
                {"node:headquarter <http://property.org/resource/"+headquarters+">;" if headquarters!="" else "" }
                {"node:location <http://property.org/resource/"+country+">;" if country!="" else "" }
                {"node:quarterlygrowth <http://property.org/resource/"+quarterly_growth+">;" if quarterly_growth!="" and quarterly_growth!="0" else "" } 
                {"node:annualgrowth <http://property.org/resource/"+annual_growth+">;" if annual_growth!="" and annual_growth!="0" else "" } 
                {"node:numberOfEmployees <http://property.org/resource/"+no_of_employees+">;" if no_of_employees!="" and no_of_employees!="0" else "" } 
                {'foaf:companyType "'+company_type+'";' if company_type!='' else '' }
                {"node:founded <http://property.org/resource/"+founded+">;" if founded!="" else "" }
                {'foaf:WebsiteUrl "'+website+'";' if website!='' else '' } 
                {'foaf:assets "'+assets+'";' if assets!='' else '' } 
                {"node:sales <http://property.org/resource/"+sales+">;" if sales!="" else "" }
                {'foaf:profit "'+profit+'";' if profit!='' else '' }  
                {"node:yearlyRevenue2022 <http://property.org/resource/"+yearly_revenue_2022+">;" if yearly_revenue_2022!="" else "" }
                {'foaf:yearlyRevenue2021 "'+yearly_revenue_2021+'";' if yearly_revenue_2021!='' else '' }   
                {"node:lastQuarterlyRevenue <http://property.org/resource/"+last_quarterly_revenue+">;" if last_quarterly_revenue!="" else "" }
                {'foaf:secondQuarterlyRevenue "'+second_last_quarterly_revenue+'";' if second_last_quarterly_revenue!='' else '' }  
                dbo:abstract "{article}";
                {'dbo:SIC "'+str(sic_code)+'";' if sic_code!="" and sic_code !="0"  else "" }
                {'dbo:NAICS "'+str(naics_code)+'";' if naics_code!="" and naics_code !="0"  else "" }
                {'foaf:SocialURL "'+social_url+'";' if social_url!='' else '' }   
                {'foaf:CompaniesSize "'+company_size+'";' if company_size!='' else '' }
                {'dbo:industry "'+industry+'";' if industry!='' else '' }
                {'dbo:headquarter "'+headquarters+'";' if headquarters!='' else '' }
                {'dbo:location "'+country+'";' if country!='' else ''}
                {'foaf:quarterlygrowth "'+quarterly_growth+'";'if quarterly_growth!="" and quarterly_growth!="0" else "" } 
                {'foaf:annualgrowth "'+annual_growth+'";' if annual_growth!="" and annual_growth!="0" else "" } 
                {'dbo:numberOfEmployees "'+no_of_employees+'";' if no_of_employees!="" and no_of_employees!="0" else "" }
                {'dbp:founded "'+founded+'";' if founded!="" else "" } 
                {'foaf:sales "'+sales+'";' if sales!="" else "" }
                {'foaf:yearlyRevenue2022 "'+yearly_revenue_2022+'";' if yearly_revenue_2022!="" else "" }
                {'foaf:lastQuarterlyRevenue "'+last_quarterly_revenue+'";' if last_quarterly_revenue!="" else "" }
                foaf:manual pro:{manual};
                foaf:timestamp <http://property.org/resource/{timestamp}>;
                foaf:customProperties <http://property.org/resource/{name + "_" + node_label + "_Properties"}>;
                rdfs:label "{name + "_" + node_label}" . 

            {custom_prop_subject} rdfs:label "Properties" .
            {custom_properties}
                
            {'<http://property.org/resource/'+industry+'> rdfs:label "'+industry+'" .' if industry != '' else '' }

            {'<http://property.org/resource/'+headquarters+'> rdfs:label "'+headquarters+'" .' if headquarters != '' else '' }

            {'<http://property.org/resource/'+country+'> rdfs:label "'+country+'" .' if country != '' else '' } 

            {'<http://property.org/resource/'+quarterly_growth+'> rdfs:label "'+quarterly_growth+'" .' if quarterly_growth != '' and quarterly_growth != '0' else '' }

            {'<http://property.org/resource/'+annual_growth+'> rdfs:label "'+annual_growth+'" .' if annual_growth != '' and annual_growth != '0' else '' }

            {'<http://property.org/resource/'+no_of_employees+'> rdfs:label "'+no_of_employees+'" .' if no_of_employees != '' and no_of_employees != '0' else '' }

            {'<http://property.org/resource/'+founded+'> rdfs:label "'+founded+'" .' if founded != '' else '' }

            {'<http://property.org/resource/'+sales+'> rdfs:label "'+sales+'" .' if sales != '' else '' }

            {'<http://property.org/resource/'+yearly_revenue_2022+'> rdfs:label "'+yearly_revenue_2022+'" .' if yearly_revenue_2022 != '' else '' }
            
            {'<http://property.org/resource/'+last_quarterly_revenue+'> rdfs:label "'+last_quarterly_revenue+'" .' if last_quarterly_revenue != '' else '' }

            <https://company.org/resource/{name}> a dbo:Organisation;
                dbo:source {prefix} .''';

    statements = statements.replace("\n", "")
    return statements

def config_delete_query(data):  
    source = data.get('source')
    company = encodeURIComponent(data.get('name').strip().replace(" ", "_"))
    
    prefix = ''
    prefix_url=""
    match source:
        case 'linkedin':
            node_label = "LinkedIn"
            prefix = "<https://www.linkedin.com/company/"+company+">" 
            prefix_url = "PREFIX dbr1: <https://www.linkedin.com/company/>";
        case 'dbpedia':
            prefix = "<https://dbpedia.org/resource/"+company+">" 
            node_label = "DBPedia" 
            prefix_url = "PREFIX dbr2: <https://dbpedia.org/resource/>";
        case 'zoominfo':
            prefix = "<https://www.zoominfo.com/company/"+company+">" 
            node_label = "ZoomInfo" 
            prefix_url = "PREFIX dbr4: <https://www.zoominfo.com/company/>";
        case 'salesforce':
            prefix = "<https://www.salesforce.com/company/"+company+">"
            node_label = "Salesforce"
            prefix_url = "PREFIX dbr3: <https://www.salesforce.com/company/>";
        case 'gkg':
            prefix = "<https://www.zeniagraphgkg.com/company/"+company+">"
            node_label = "GKG"
            prefix_url = "PREFIX dbr_gkg: <https://www.zeniagraphgkg.com/company/>";
        case 'scrap':
            prefix = "<https://www.zeniagraphscrap.com/company/"+company+">"
            node_label = "Scrap"
            prefix_url = "PREFIX dbr_scrap: <https://www.zeniagraphscrap.com/company/>";
             
    query =  f'''{prefix_url}
            PREFIX pro: <http://property.org/resource/> 
            DELETE {{{prefix} ?p ?o .  <http://property.org/resource/{company + "_" + node_label + "_Properties"}> ?p1 ?o1 . }}
            WHERE {{{prefix} ?p ?o .  <http://property.org/resource/{company + "_" + node_label + "_Properties"}> ?p1 ?o1 . }}''';     
    return query

def arrange_fields_output(data, source):
    custom_properties = []
    standards_fields = []
    if source=="linkedin":
        standards_fields = STANDARD_COMP_FIELDS_LINKEDIN
    elif source=="dbpedia":
        standards_fields = STANDARD_COMP_FIELDS_DBPEDIA
    elif source=="yahoo_finance":
        standards_fields = STANDARD_COMP_FIELDS_YAHOO
    else :
        standards_fields = STANDARD_COMP_FIELDS
   
    for key in data:
        if key not in standards_fields:
            custom_properties.append({"name":key, "value":data[key]}) 

    data['custom_property'] = custom_properties
    return data   

def clean_description(description: str) -> str:
        if not description:
            return ""
        # remove unicode characters
        description = description.encode('ascii', 'ignore').decode()
        description = description.encode('utf-8').decode()
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

def clean_name(name: str) -> str:
        if not name:
            return ""
        # remove unicode characters
        name = name.encode('ascii', 'ignore').decode()
        
        # remove punctuation
        name = remove_punctuation_except_hyphen(name)
          
        # clean up the spacing
        name = re.sub('\s{2,}', " ", name)

        # remove newlines
        name = name.replace("\n", " ")

        # split on capitalized words
        #name = " ".join(re.split('(?=[A-Z])', name))

        # clean up the spacing again
        name = re.sub('\s{2,}', " ", name)

        # make all words lowercase
        #name = name.lower()

        #remove side spaces
        name = name.strip()

        #add _ instead  of space
        name = name.replace(" ", "_")

        return name

def remove_punctuation_except_hyphen(input_string):
    # Get a string of all punctuation characters except hyphen
    punctuation_except_hyphen = string.punctuation.replace('-', '')
    
    # Create a translation table
    translator = str.maketrans('', '', punctuation_except_hyphen)
    
    # Use the translation table to remove punctuation except hyphen
    clean_string = input_string.translate(translator)
    
    return clean_string

def validate_fields(data):
    message = ""  
    if data.get('name') == "":
        message = "Company name is required!"
    elif data.get('source') == "":
        message = "Source is required!"
    elif data.get('description') == "":
        message = "Description field is required!"
    elif data.get('source') not in ["linkedin","dbpedia","salesforce","others","yahoo_finance"]:
        message = "Description field is required!"
 
    return message

def construct_query_gpt(query: str):
    listOfStatements= query.split("\n")
    indexOfSelectStatement=-1
    for statement in listOfStatements:
        if "SELECT" in statement or "select" in statement:
            indexOfSelectStatement=listOfStatements.index(statement)
            
    if indexOfSelectStatement != -1:
        listOfStatements[indexOfSelectStatement]="CONSTRUCT {?company a dbo:Company }"

    query = " ".join(listOfStatements)
    return encodeURIComponent(query)

#===============To parse the sparql query results==================

def parse_json_response(json_data):
    result_list = []
    for entry in json_data["results"]["bindings"]:
        result_dict={}
        for key in json_data["head"]["vars"]:
            if key in entry:
                result_dict[key]=entry[key]["value"]
            else:
                result_dict[key]=""
        if len(result_dict)>0:
            result_list.append(result_dict) 

    return result_list if len(result_list)>0 else None


def getSparqlQueryForCompanyDetails(params: dict):
    queryForCompanyDetails=f'''PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    select ?companySourceURI where {{
        ?companySourceURI a dbo:Organisation;
            rdfs:label ?companyName.
        FILTER regex(?companyName, "^{params["company_name"]}", "i")
    }}'''
    return encodeURIComponent(queryForCompanyDetails)

def getSparqlQueryForSimilarCompaniesByName(companyURI: str, resultsLimit: int = 10):
    querytogetSimilarCompanies=f'''PREFIX :<http://www.ontotext.com/graphdb/similarity/>
    PREFIX similarity-index:<http://www.ontotext.com/graphdb/similarity/instance/>
    PREFIX psi:<http://www.ontotext.com/graphdb/similarity/psi/>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX inst:<http://www.ontotext.com/graphdb/similarity/instance/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT (?entity AS ?documentID) ?score ?companyName ?source (GROUP_CONCAT(DISTINCT ?headquarter;separator=",") as ?headquarter) (GROUP_CONCAT(DISTINCT ?industry;separator=",") as ?industry) ?quarterly_revenue_growth ?numberOfEmployees ?founded (GROUP_CONCAT(DISTINCT ?sic;separator=",") as ?sic) (GROUP_CONCAT(DISTINCT ?naics;separator=",") as ?naics) ((YEAR(NOW()) - ?founded) as ?operating_years) ?description
    WHERE {{
        ?search a inst:{GRAPHDB_SIMILARITY_INDEX_NAME} ;
        psi:searchEntity <{companyURI}>;
        psi:searchPredicate <http://www.ontotext.com/graphdb/similarity/psi/any>;
        :searchParameters "-numsearchresults {resultsLimit}";
        psi:entityResult ?result .
        ?result :value ?entity ;
        :score ?score .
        ?entity rdfs:label ?companyName;
                    dbo:source ?entity_source.
        OPTIONAL {{ ?entity_source dbo:source ?source; dbo:headquarters ?headquarter. }}
        OPTIONAL {{ ?entity_source dbo:source ?source; dbo:industry ?industry. }}
        OPTIONAL {{ ?entity_source dbo:source ?source; dbo:no_of_employees ?numberOfEmployees. }}
        OPTIONAL {{ ?entity_source dbo:source "yahoo_finance"; foaf:quarterly_revenue_growth ?quarterly_revenue_growth. }}
        OPTIONAL {{ ?entity_source dbo:source "zoominfo"; dbo:sic ?sic. }}
        OPTIONAL {{ ?entity_source dbo:source "zoominfo"; dbo:naics ?naics. }}
        OPTIONAL {{ ?entity_source dbo:source ?source. ?entity_source foaf:founded ?founded . }}
        OPTIONAL {{ ?entity_source dbo:source ?source. ?entity_source dbo:description ?description . }}
    }}
    GROUP BY ?entity ?score ?companyName ?source ?quarterly_revenue_growth ?numberOfEmployees ?founded ?description''' 
    return encodeURIComponent(querytogetSimilarCompanies)

def getCompanyURIFromCompaniesList(companies: list):
    return ' '.join('<' + item.get("id", "") + '>' for item in companies).strip(",")


def getSparqlQueryForEmployeesInCompanies(companies: list):
    companiesURI = getCompanyURIFromCompaniesList(companies)
    queryForEmployeesInCompanies=f'''PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    
    select DISTINCT ?employer ?name ?roleLabel ?about ?social_url ?employer (GROUP_CONCAT(?occupationLabel;separator=',') as ?occupations) ?source WHERE {{ 
        VALUES ?organisation {{ {companiesURI} }}
        
        ?organisation a dbo:Organisation;
    	    dbo:source ?sources.
        ?sources dbo:employer ?employee;
            dbo:source ?source.
        ?employee rdfs:label ?name.
        BIND(?organisation AS ?employer)
    	OPTIONAL {{
        	?employee dbo:role ?role.
            ?role rdfs:label ?roleLabel.
        }}
        OPTIONAL {{
                ?employee vcard:occupation ?ocupation.
                ?ocupation rdfs:label ?occupationLabel.
        }}
    	OPTIONAL {{ ?employee vcard:social_url ?social_url.}}
    	OPTIONAL {{ ?employee dbo:description ?about. }}
        }}
        GROUP BY ?name ?roleLabel ?about ?social_url ?employer ?source'''
    return encodeURIComponent(queryForEmployeesInCompanies)

def addPersonsDataIntoCompaniesData(companiesData: list,personsData: list):
    if( len(personsData["results"]["bindings"]) == 0):
        return companiesData
    for company in companiesData:
        personsList = []
        for personDetails in personsData["results"]["bindings"]:
            if(company["id"] == personDetails["employer"]["value"]):
                first_name, last_name = split_full_name(personDetails['name']['value'])
                personsList.append({
                    "first_name":first_name,
                    "last_name":last_name,
                    "description":personDetails["about"]["value"] if(is_key_exists_in_dictionary(personDetails,"about")) else "",
                    "occupation":get_occupation(personDetails),
                    "social_url":personDetails["social_url"]["value"] if(is_key_exists_in_dictionary(personDetails,"social_url")) else "",
                    "source":personDetails["source"]["value"] if(is_key_exists_in_dictionary(personDetails,"source")) else "",
                })
        if( len(personsList) > 0):
            company["employer"] = personsList    
    return companiesData

def getSparqlConstructQueryForAttributesWithCompaniesList(company_list: list, attributes_list: list):
    attribute_predicate_mapping = {
        "dbp:name ?name;": ["name"],
        "node:industry ?industry;": ["industry","industries"],
        "node:headquarters ?headquarters;": ["headquarter","headquarters"],
        "node:location ?location;": ["location"],
        "foaf:founded ?founded;": ["founded"],
        "node:total_assets ?total_assets;": ["assets","total assets","totalassets"],
        "node:sales ?sales;": ["sales"],
        "node:gross_profit ?gross_profit;": ["gross profit","grossProfit","profit"],
        "rdfs:label ?label;": ["label"],
        "node:market_cap ?market_cap": ["marketCap","market cap"],
        "dbo:description ?description;": ["description","descriptions"],
        "node:sic ?SIC;": ["sic"],
        "node:naics ?naics;": ["naics"],
        "node:exchange ?exchange;": ["exchange"],
        "node:ticker-symbol ?ticker_symbol;": ["ticker-symbol","ticker symbol","sym","symbols"],
        "node:operating_years ?operating_years;": ["operating year","operatingyear","operating years","operatingyears"], 
        "foaf:Specialities ?Specialities;": ["specialities"],
        "node:quarterly_revenue_growth ?quarterly_revenue_growth;": ["quaterlygrowth", "quaterly growth", "quaterly revenue growth"],
        "node:annualgrowth ?annualgrowth;": ["annualgrowth", "annual growth"],
        "node:no_of_employees ?no_of_employees;": ["numberofemployees", "number of employees", "noofemployees", "no of employees"],
        "dbo:company_type ?company_type;": ["companytype", "company type", "type"],
        "node:website ?website;": ["website url", "websiteurl", "website"],
        "node:current_year_revenue ?current_year_revenue;": ["current year revenue","currentYearRevenue","yearlyrevenue2022", "yearly revenue 2022", "revenue"],
        "node:previous_year_revenue ?previous_year_revenue;": ["previous year revenue","previousYearRevenue","yearlyrevenue2021", "yearly revenue 2021"],
        "node:last_quarterly_revenue ?last_quarterly_revenue;": ["last quarterly revenue", "lastquarterlyrevenue", "last quarterly"],
        "node:second_last_quarterly_revenue ?second_last_quarterly_revenue;": ["second quarterly revenue", "secondquarterlyrevenue", "second quarterly"],
        "node:social_url ?social_url;": ["socialurl", "social url"],
        "node:wiki_url ?wiki_url;": ["wiki url", "wikiurl", "wikipedia url"],
        "foaf:profile_url ?profile_url;": ["profile_url","profile url","profile"],
        "foaf:SocialFollowers ?SocialFollowers;": ["socialfollowers", "social followers"],
        "foaf:CompaniesSize ?CompaniesSize;": ["companiessize", "companies size"],
        "foaf:custom_properties ?custom_properties;": ["custom properties","customproperties"],
        "foaf:long_business_summary ?long_business_summary;":["long business summary","business summary"]
    }
    variableNames = ""
    whereStatements = ""
    constructStatements = ""

    for keys, valueList in attribute_predicate_mapping.items():
        for attr in attributes_list: 
            if attr.lower() in valueList:
                constructStatements = constructStatements+keys+"\n"
                whereStatements = whereStatements+"OPTIONAL { ?source "+keys[:-1]+".}\n"
                break
            
    sample_query=f"""
        PREFIX  com: <https://company.org/resource/>
        PREFIX  owl: <http://www.w3.org/2002/07/owl#> 
        PREFIX  xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX  rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX  dbr2: <https://dbpedia.org/resource/>
        PREFIX  path: <http://www.ontotext.com/path#>
        PREFIX  dbr3: <https://www.salesforce.com/company/>
        PREFIX  dbr_scrap: <https://www.zeniagraphscrap.com/company/>
        PREFIX  dbr1: <https://www.linkedin.com/company/>
        PREFIX  yahoo: <https://finance.yahoo.com/quote/>
        PREFIX  foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX  dbr_gkg: <https://www.zeniagraphgkg.com/company/>
        PREFIX  vcard: <http://www.w3.org/2006/vcard/ns#>
        PREFIX  pro: <http://property.org/resource/>
        PREFIX  dbr4: <https://www.zoominfo.com/company/>
        PREFIX  dbo: <http://dbpedia.org/ontology/>
        PREFIX  node: <http://property.org/node/>
        PREFIX  dbp: <http://dbpedia.org/property/>
        PREFIX  rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX  finance: <http://property.org/finance/>


        CONSTRUCT {{
            ?org a dbo:Organisation;
                dbo:source ?source.
            ?source foaf:parent_name ?parent_name;
                    {constructStatements[:-2]}.
        }}
        where
        {{
            ?org a dbo:Organisation;
                dbo:source ?source.
            ?source foaf:parent_name ?parent_name.
                    {whereStatements[:-1]}
            FILTER regex(?parent_name, "{"|".join(f'{com.get("company_name")}' for com in company_list)}", "i")
        }}"""
    return encodeURIComponent(sample_query)

def getSparqlSelectQueryForAttributesWithCompaniesList(company_list: list, attributes_list: list):
    attribute_predicate_mapping = {
        "dbp:name ?name;": ["name"],
        "dbo:industry ?industry_;": ["industry","industries"],
        "dbo:headquarters ?headquarters;": ["headquarter","headquarters"],
        "node:location ?location;": ["location"],
        "foaf:founded ?founded;": ["founded"],
        "foaf:total_assets ?total_assets;": ["assets","total assets","totalassets"],
        "node:sales ?sales;": ["sales"],
        "foaf:gross_profit ?gross_profit;": ["gross profit","grossProfit","profit"],
        "rdfs:label ?label;": ["label"],
        "foaf:market_cap ?market_cap": ["marketCap","market cap"],
        "dbo:description ?description;": ["description","descriptions"],
        "dbo:sic ?sic_;": ["sic"],
        "dbo:naics ?naics_;": ["naics"],
        "node:exchange ?exchange;": ["exchange"],
        "foaf:ticker-symbol ?ticker_symbol;": ["ticker-symbol","ticker symbol","sym","symbols"],
        "node:operating_years ?operating_years;": ["operating year","operatingyear","operating years","operatingyears"], 
        "foaf:Specialities ?Specialities_;": ["specialities"],
        "foaf:quarterly_revenue_growth ?quarterly_revenue_growth;": ["quaterlygrowth", "quaterly growth", "quaterly revenue growth"],
        "node:annualgrowth ?annualgrowth;": ["annualgrowth", "annual growth"],
        "dbo:no_of_employees ?no_of_employees;": ["numberofemployees", "number of employees", "noofemployees", "no of employees"],
        "dbo:company_type ?company_type;": ["companytype", "company type", "type"],
        "foaf:website ?website;": ["website url", "websiteurl", "website"],
        "foaf:current_year_revenue ?current_year_revenue;": ["current year revenue","currentYearRevenue","yearlyrevenue2022", "yearly revenue 2022", "revenue"],
        "foaf:previous_year_revenue ?previous_year_revenue;": ["previous year revenue","previousYearRevenue","yearlyrevenue2021", "yearly revenue 2021"],
        "foaf:last_quarterly_revenue ?last_quarterly_revenue;": ["last quarterly revenue", "lastquarterlyrevenue", "last quarterly"],
        "foaf:second_last_quarterly_revenue ?second_last_quarterly_revenue;": ["second quarterly revenue", "secondquarterlyrevenue", "second quarterly"],
        "foaf:social_url ?social_url;": ["socialurl", "social url"],
        "node:wiki_url ?wiki_url;": ["wiki url", "wikiurl", "wikipedia url"],
        "foaf:profile_url ?profile_url;": ["profile_url","profile url","profile"],
        "foaf:SocialFollowers ?SocialFollowers;": ["socialfollowers", "social followers"],
        "foaf:CompaniesSize ?CompaniesSize;": ["companiessize", "companies size"],
        "foaf:custom_properties ?custom_properties;": ["custom properties","customproperties"],
        "foaf:long_business_summary ?long_business_summary;":["long business summary","business summary"]
    }
    variableNames = []
    whereStatements = ""
    constructStatements = ""

    for keys, valueList in attribute_predicate_mapping.items():
        for attr in attributes_list: 
            if attr.lower() in valueList:
                constructStatements = constructStatements+keys+"\n"
                whereStatements = whereStatements+"OPTIONAL { ?company "+keys[:-1]+".}\n"
                variableNames.append(" ?" + keys.split("?")[1][:-1])
                break

    groupBy = "GROUP By ?company"

    for variable in variableNames:
        if variable not in [' ?Specialities_',' ?industry_',' ?sic_',' ?naics_']:
            groupBy = groupBy + variable

    for multiValueVar in [' ?Specialities_',' ?industry_',' ?sic_',' ?naics_']:
        if multiValueVar in variableNames:
            index=variableNames.index(multiValueVar)
            variableNames[index] = " (GROUP_CONCAT(DISTINCT"+multiValueVar+"; separator=\", \") AS "+multiValueVar[:-1]+")"
    
    

            
    sample_query=f"""
        PREFIX  com: <https://company.org/resource/>
        PREFIX  owl: <http://www.w3.org/2002/07/owl#> 
        PREFIX  xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX  rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX  dbr2: <https://dbpedia.org/resource/>
        PREFIX  path: <http://www.ontotext.com/path#>
        PREFIX  dbr3: <https://www.salesforce.com/company/>
        PREFIX  dbr_scrap: <https://www.zeniagraphscrap.com/company/>
        PREFIX  dbr1: <https://www.linkedin.com/company/>
        PREFIX  yahoo: <https://finance.yahoo.com/quote/>
        PREFIX  foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX  dbr_gkg: <https://www.zeniagraphgkg.com/company/>
        PREFIX  vcard: <http://www.w3.org/2006/vcard/ns#>
        PREFIX  pro: <http://property.org/resource/>
        PREFIX  dbr4: <https://www.zoominfo.com/company/>
        PREFIX  dbo: <http://dbpedia.org/ontology/>
        PREFIX  node: <http://property.org/node/>
        PREFIX  dbp: <http://dbpedia.org/property/>
        PREFIX  rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX  finance: <http://property.org/finance/>


        SELECT ?company_name ?source {"".join(f'{var}' for var in variableNames)} 
        where
        {{
            ?company foaf:parent_name ?company_name;
                    dbo:source ?source.
                    {whereStatements[:-1]}
            FILTER regex(?company_name, "{"|".join(f'{com.get("company_name")}' for com in company_list)}", "i")
        }}
        {groupBy} ?company_name ?source"""
    return sample_query

def split_full_name(full_name):
    """
    Split full name into first and last name based on white spaces.
    Being first_name the first word and last_name the rest of the string.
    """
    n = full_name.find(" ")
    if n < 0:
        return full_name, ""
    return full_name[:n].strip(), full_name[n:].strip()

def is_key_exists_in_dictionary(dictionary: dict, key_value: str):
    return True if (key_value in dictionary) else False 


#===============SHOW SIMILARY COMPANY KG SPARQL QUERY BUILDER for GRAPH==================
def config_graph_query_for_graph_similarity(data:list):
    uris = ", ".join('<' +item.get("id").strip() + '>' for item in data)
    for x in data:
        temp = float(x.get("vector_score", ""))
        temp = "{:.4f}".format(round(temp, 4))
        x['vector_score'] = temp
    score_uris = " ".join('(<' +item.get("id").strip() + '> ' + '<http://property.org/resource/' + item.get("vector_score", "") + '> )' for item in data)
    
    query = f'''PREFIX dbp: <http://dbpedia.org/property/> 
    PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    PREFIX dbr1: <https://www.linkedin.com/company/> 
    PREFIX dbr2: <https://dbpedia.org/resource/> 
    PREFIX dbo: <http://dbpedia.org/ontology/> 
    PREFIX dbr3: <https://www.salesforce.com/company/> 
    PREFIX dbr_gkg: <https://www.zeniagraphgkg.com/company/> 
    PREFIX dbr_scrap: <https://www.zeniagraphscrap.com/company/> 
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
    PREFIX pro: <http://property.org/resource/> 
    PREFIX node: <http://property.org/node/> 
    PREFIX vcard: <http://www.w3.org/2006/vcard/ns#> 
    PREFIX com: <https://company.org/resource/> 
    PREFIX dbr4: <https://www.zoominfo.com/company/> 
    CONSTRUCT {{ ?company rdf:type dbo:Organisation. ?company dbo:score ?score. }}
    WHERE {{ VALUES (?link ?value) {{ {score_uris} }} 
    bind(?link as ?company) 
    bind(?value as ?score) 
    ?company a dbo:Organisation. FILTER (?company IN ({uris})) }}'''
    return encodeURIComponent(query)
 
def get_occupation(data: dict):
    occupations = ""
    if(is_key_exists_in_dictionary(data,"occupations") and bool(data["occupations"]["value"].strip())):
        occupations =  data["occupations"]["value"]
    elif(is_key_exists_in_dictionary(data,"roleLabel") and bool(data["roleLabel"]["value"].strip())):
        occupations =  data["roleLabel"]["value"]
    return occupations

def get_field_source_order(field: str):
    source_orders = {
        "industry": ["dbpedia","linkedin","zoominfo"],
        "headquarter": ["linkedin","dbpedia", "zoominfo"],
        "numberOfEmployees": ["linkedin","zoominfo", "dbpedia"],
        "description": ["dbpedia","linkedin"],
        "founded": ["zoominfo","linkedin", "dbpedia"],
        "operating_years": ["zoominfo","linkedin", "dbpedia"],
        "naics": ["zoominfo"],
        "sic": ["zoominfo"],
        "quarterly_revenue_growth": ["yahoo_finance"],
    }
    return source_orders[field]

def get_value_from_graph_similarity_data(params: dict, companies: dict):
    value = None
    for source in get_field_source_order(params["field"]):
        for company in companies:
            if(company["companyName"]["value"] == params["company"] and company["source"]["value"] == source and is_key_exists_in_dictionary(company,params["field"]) and bool(company[params["field"]]["value"].strip())):
                value = company[params["field"]]["value"].strip()
                break
        if(value):
            break
    return value

def is_item_in_second_array(first_array, second_array):
    for item in first_array:
        if item in second_array:
            return True
    return False

def personalize_company_name(input_string):
    # Remove special characters using regex
    cleaned_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)

    # Remove spaces and convert to lowercase
    cleaned_string = cleaned_string.replace(' ', '').lower()

    return cleaned_string + '_linkedin'

def clean_string(input_string):
    # Remove special characters using regex
    cleaned_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)

    # Remove spaces and convert to lowercase
    cleaned_string = cleaned_string.replace(' ', '').lower()

    return cleaned_string

def clean_string_v2(input_string):
    # Remove special characters using regex
    cleaned_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)

    return cleaned_string

#===============SHOW CANDIDATES USER BY SHOWKG==================
def config_graph_query_candidates(data:list):
    uris = ' '.join('<' + get_proper_url_jobs_candidate(encodeURIComponent(item.get("label", ""))) + '>' + ',' for item in data)
    uris = uris[0: len(uris) - 1]  # removing extra comma from uris
    
    score_uris = ' '.join('(<' + get_proper_url_jobs_candidate(encodeURIComponent(item.get("label", ""))) + '>' + '<http://property.org/resource/' + item.get("vector_score", "") + '> )' for item in data)
     
    query = f'''PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                PREFIX dbo: <http://dbpedia.org/ontology/> 
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                PREFIX pro: <http://property.org/resource/> 
                PREFIX node: <http://property.org/node/> 
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#> 
                PREFIX com: <https://company.org/resource/> 
                CONSTRUCT {{ 
                    ?person a vcard:Individual; 
                        dbo:score ?score . 
                }} 
                WHERE {{ 
                        VALUES (?link ?value) {{ {score_uris} }} bind(?link as ?person) bind(?value as ?score) ?person a vcard:Individual .                            
                        FILTER (?person IN ({uris})) 
                }}
            '''
    
    query = query.replace("\n", "")
    my_logger.info(query)
    return encodeURIComponent(query)

#===============SHOW JOBS USER BY SHOWKG==================
def config_graph_query_jobs(data:list):
    uris = ' '.join('<' + item.get("graph_uri", "") + '>' + ',' for item in data)
    uris = uris[0: len(uris) - 1]  # removing extra comma from uris
    
    score_uris = ' '.join('(<' + item.get("graph_uri", "") + '>' + '<http://property.org/resource/' + item.get("vector_score", "") + '> )' for item in data)
     
    query = f'''PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                PREFIX dbo: <http://dbpedia.org/ontology/> 
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                PREFIX pro: <http://property.org/resource/> 
                PREFIX node: <http://property.org/node/> 
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#> 
                PREFIX saro: <http://w3id.org/saro#>
                CONSTRUCT {{ 
                    ?job a saro:Job ;
                        dbo:score ?score . 
                }} 
                WHERE {{ 
                        VALUES (?link ?value) {{ {score_uris} }} bind(?link as ?job) bind(?value as ?score) ?job a saro:Job .                            
                        FILTER (?job IN ({uris})) 
                }}
            '''
    
    query = query.replace("\n", "")
    my_logger.info(query)
    return encodeURIComponent(query)

def config_graph_query_for_claim_similarity(data:list):
    uris = ", ".join('<' +item.get("entity").strip() + '>' for item in data)
    for x in data:
        temp = float(x.get("vector_score", ""))
        temp = "{:.4f}".format(round(temp, 4))
        x['vector_score'] = temp
    score_uris = " ".join('(<' +item.get("entity").strip() + '> ' + '<http://property.org/resource/' + item.get("vector_score", "") + '> )' for item in data)
    
    query = f'''
    PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
    PREFIX vcard: <http://www.w3.org/2006/vcard/ns#> 
    PREFIX : <http://example.org/insurance#>
    
    CONSTRUCT {{ 
        ?claim a ?p . 
        ?p rdfs:subClassOf :Claim .
        ?claim :score ?score . 
    }}
    WHERE {{ 
        VALUES (?link ?value) {{ {score_uris} }} 
        bind(?link as ?claim) 
        bind(?value as ?score) 
        ?claim a ?p .
        ?p rdfs:subClassOf :Claim . 
        FILTER (?claim IN ({uris})) 
    }}'''
    
    return encodeURIComponent(query)

def extract_text_from_pdf_url(url: str, num_pages: int = None):
    resp = {'error':None, 'extracted_data': None}
    try:
        response = requests.get(url, verify=False)

        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            text = ""

            if num_pages is None:
                pages = pdf.pages
            else:
                pages = pdf.pages[:num_pages]

            for page in pages:
                text += page.extract_text()
        resp['extracted_data'] = text

    except Exception as e:
        resp['error'] = e
    
    return resp

def get_plans_construct_query(params):
    urls  = []
    for item in params:
        urls.append(f'''<http://www.griffin.org/{item['productId']}>''')
    formatted_urls = ", ".join(urls)
   
    query = f'''
        PREFIX node: <http://property.org/node/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX gr: <http://www.griffin.org/> 

        CONSTRUCT {{
            ?agent gr:request ?request . 
            ?request gr:getQuote ?quote .
    
            ?quote gr:cost ?planCost .
            ?agent a gr:Agent .

            ?request gr:travelers ?travelers .
        }}
        WHERE {{
            ?agent a gr:Agent;
                   gr:request ?request .
            ?request a gr:TravellerRequest;
                gr:request [gr:getQuote ?quote] .
                ?request gr:travelers ?travelers .
                ?request gr:planCost ?planCost .
                ?planCost gr:includesPlan ?PlanNode .
            ?quote a gr:Quote ;
                rdfs:label ?planName ;
                gr:requestCost ?PlanNode .
            filter(?request=<{item['request_uri']}>) 
            filter(?quote in({formatted_urls}))    
        }}
    '''
    print(query)
    query = query.replace("\n", "")
    return encodeURIComponent(query)

def get_plans_construct_query_post(params):
    urls  = []
    for item in params:
        urls.append(f'''<http://www.griffin.org/{item['productId']}>''')
    formatted_urls = ", ".join(urls)

    query = f'''
        PREFIX node: <http://property.org/node/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX gr: <http://www.griffin.org/> 

        CONSTRUCT {{
            ?agent gr:request ?request . 
            ?request gr:getQuote ?quote .
    
            ?quote gr:cost ?planCost .
            ?agent a gr:Agent .

            ?request gr:travelers ?travelers .
            
            ?winningIRI a gr:winningQuote  .
            
        }}
        WHERE {{
            ?agent a gr:Agent;
                   gr:request ?request .
            ?request a gr:TravellerRequest;
                gr:request [gr:getQuote ?quote] .
                ?request gr:travelers ?travelers .
                ?request gr:planCost ?planCost .
                ?planCost gr:includesPlan ?PlanNode .
            ?quote a gr:Quote ;
                rdfs:label ?planName ;
                gr:requestCost ?PlanNode .
            OPTIONAL {{
                ?request gr:winningQuote ?winningQuote .
                BIND(IRI(?winningQuote) AS ?winningIRI)
            }} .
            
            filter(?request=<{item['request_uri']}>) 
            filter(?quote in({formatted_urls}))    
        }}
    '''
    my_logger.info(query)
     
    query = query.replace("\n", "")
    return encodeURIComponent(query)