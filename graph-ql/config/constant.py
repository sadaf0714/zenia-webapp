import os
from dotenv import load_dotenv
load_dotenv()

ENV_MODE  = os.getenv("ENV")
HOST = os.getenv("HOST")

#Micro Services Endpoint
EMBEDDING_SERVICE_URL  = os.getenv("VECTOR_SERVICE_HTTP_URL")
REDIS_SERVICE_URL = os.getenv("REDIS_SERVICE_HTTP_URL")
GRAPHDB_SERVICE = os.getenv("GRAPHDB_SERVICE_HTTP_URL")
GRAPHQL_SERVICE= os.getenv('GRAPHQL_SERVICE_HTTP_URL')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
GRAPHDB_SERVICE_SHOWKG_HTTP_URL = os.getenv('GRAPHDB_SERVICE_SHOWKG_HTTP_URL')
METAPHACTORY_URL = os.getenv('METAPHACTORY_URL')
#enable or disable linkedin company names crawling from rapidapi 0 | 1
LINKEDIN_RAPID_STATUS = 0

#EXTERNAL ENDPOINTS
EXT_GRAPHQL_SERVICE_HTTP_URL = os.getenv('EXT_GRAPHQL_SERVICE_HTTP_URL')
EXT_VECTOR_SERVICE_HTTP_URL= os.getenv('EXT_VECTOR_SERVICE_HTTP_URL')
EXT_REDIS_SERVICE_HTTP_URL= os.getenv('EXT_REDIS_SERVICE_HTTP_URL')

RECON_ENDPOINT = os.getenv('RECON_ENDPOINT')

#Other Endpoints
EMBEDDING_ENDPOINT = EMBEDDING_SERVICE_URL + '/embedding/api'
REDIS_ENDPOINT = REDIS_SERVICE_URL + '/redis/api'
GPT_REORDER_ENDPOINT = EMBEDDING_SERVICE_URL + '/embedding/api/get-similarity/'
REDIS_GET_COMPANIES = REDIS_SERVICE_URL + '/redis/api/redis-get-companies'
REDIS_GET_CLAIM = REDIS_SERVICE_URL + '/redis/api/get-claim-by-id'
VECTOR_ACTIVE_CLASSIFICATION = EMBEDDING_SERVICE_URL + '/embedding/api/get-active-classification'
CLASSIFIED_COMPANIES_REDIS = REDIS_SERVICE_URL + '/redis/api/get-classify-companies'
STORE_DATA_URL = REDIS_SERVICE_URL + '/redis/api/insert-into-redisdb'
COMPANY_DATA_URL = REDIS_SERVICE_URL + '/redis/api/redis-get-companies'
REDIS_UPDATE_DATA_URL = REDIS_SERVICE_URL + '/redis/api/update-redisdb'
REDIS_UPDATE_DATA_COMP = REDIS_SERVICE_URL + '/redis/api/update-redisdb-wd'
REDIS_GET_COMPANY_BY_ID = REDIS_SERVICE_URL + '/redis/api/getCompanyByID'
GET_SPARQL_BY_GPT = EMBEDDING_SERVICE_URL + '/embedding/api/getSparqlQueryFromGPT'
GET_SPARQL_BY_GPT_FOR_CLAIMS = EMBEDDING_SERVICE_URL + '/embedding/api/getSparqlQueryFromGPTForClaimData'
GET_CLASSIFIED_RESULT_BY_NLP = EMBEDDING_SERVICE_URL + '/embedding/api/getClassifiedDataFromInputText'
GRAPHDB_LOGIN = GRAPHDB_SERVICE + '/rest/login'
GRAPHDB_CONFIG_URL= GRAPHDB_SERVICE + '/rest/explore-graph/config'
EXTRACT_COVERAGE_AMOUNT = EMBEDDING_SERVICE_URL + '/embedding/api/getCoverageAmountFromGPTForInsuranceDocument'
GET_SUMMARY_REASONS = EMBEDDING_SERVICE_URL + '/embedding/api/getSummaryReasonForWinningPlans'

GRIFFIN_POC_REPO = "GRIFFIN-POC"
 
GRAPHDB_VISUAL_GRAPH =  GRAPHDB_SERVICE_SHOWKG_HTTP_URL + '/graphs-visualizations?query='
GRAPHDB_USERNAME = os.getenv("GRAPHDB_USERNAME")
GRAPHDB_PASSWORD = os.getenv("GRAPHDB_PASSWORD")
GRAPHDB_SIMILARITY_INDEX_NAME =  "common-graph-similarity"
DEFAULT_GRAPHDB_REPO = "MASTER-REPO-V2"

GET_REDIS_JOB = REDIS_SERVICE_URL + '/redis/api/get-job-by-title'
GET_REDIS_CANDIDATE = REDIS_SERVICE_URL + '/redis/api/get-candidate-by-name'

RAPID_LINKEDIN_API = "https://linkedin-public-search.p.rapidapi.com/companysearch"

HR_USECASE_JOB_REPO = "MASTER-REPO-V2"

ASSURANT_POC_REPO = "CLAIM-POLICY-USECASE"

ASSURANT_SIMILARITY_INDEX_NAME="assurant_similarity_index"

RECONCILIATION_ENDPOINT= "http://localhost:9900"

STANDARD_COMP_FIELDS = [
    "name",
    "parent_name",
    "source", 
    "SIC",
    "NAICS",
    "headquarters",
    "operating_years",
    "no_of_employees",
    "industry", 
    "description",
    "revenue_dollar", 
    "annual_growth",
    "quarterly_growth", 
    "vector_score",
    "status",
    "manual",
    "huggingface_embedding",
    "timestamp",
    "employer"
]

#standard fields for linkedin source
STANDARD_COMP_FIELDS_LINKEDIN = [
    "name",
    "source",
    "industry",
    "headquarters", 
    "no_of_employees",
    "social_url",
    "manual", 
    "founded",
    "company_type", 
    "description",
    "specialities",
    "timestamp",
    "employer",
    "parent_name",
]

#standard fields for dbpedia source
STANDARD_COMP_FIELDS_DBPEDIA = [
    "name",
    "source",
    "industry",
    "headquarters", 
    "no_of_employees",
    "profile_url",
    "manual", 
    "founded",
    "company_type", 
    "description",
    "timestamp",
    "employer",
    "parent_name"
]

#standard fields for yahoo finance source
STANDARD_COMP_FIELDS_YAHOO = [
    "industry",
    "source",
    "name",
    "no_of_employees",
    "manual",
    "parent_name",
    "quarterly_revenue_growth",
    "total_assets",
    "gross_profit",
    "website",
    "market_cap",
    "last_quarterly_revenue",
    "second_last_quarterly_revenue",
    "description",
    "current_year_revenue",
    "previous_year_revenue",
    "ticker_symbol",
    "annual_revenue_growth",
    "timestamp",
    "employer",
    "exchange"
]

coverageList = ["Trip Cancellation coverage", "Trip Interruption", "Medical Evacuation", "Emergency Medical", "Baggage Loss", "Flight Accident", "Accidental Death"]

allianzTravelCoverages = [
    {
        "id": "Trip Cancellation coverage",
        "coverageName": "Trip Cancellation"
    },
    {
        "id": "Trip Interruption",
        "coverageName": "Trip Interruption"
    },
    {
        "id": "Medical Evacuation",
        "coverageName": ""
    },
    {
        "id": "Emergency Medical",
        "coverageName": "Emergency Medical"
    },
    {
        "id": "Baggage Loss",
        "coverageName": "Baggage Loss/Damage"
    },
    {
        "id": "Flight Accident",
        "coverageName": ""
    },
    {
        "id": "Accidental Death",
        "coverageName": ""
    }
]