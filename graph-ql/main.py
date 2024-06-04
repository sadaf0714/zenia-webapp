from fastapi import FastAPI, Request
import uvicorn
import os

#create logs folder if not exists
log_folder_path = "logs"
isExist = os.path.exists(log_folder_path)
if not isExist:
    os.makedirs(log_folder_path)     
    
from starlette.middleware.cors import CORSMiddleware
from ariadne import make_executable_schema, gql, load_schema_from_path
from ariadne.asgi import GraphQL
from query.index import query
from query.jobs import jobQuery
from mutation.index import mutation
from config.util import my_format_error
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi import HTTPException
from fastapi.templating import Jinja2Templates
from config.constant import HOST
#from weasyprint import HTML 
from xhtml2pdf import pisa
from io import BytesIO
from fastapi import File, UploadFile
from config.constant import EMBEDDING_SERVICE_URL
import requests

type_defs = gql(load_schema_from_path("./types/index.graphql"))
schema = make_executable_schema(type_defs, [query,jobQuery, mutation])

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_route("/graphql", GraphQL(schema=schema, error_formatter=my_format_error))
app.mount('/static',StaticFiles(directory='static'), name='static')

# Point to the directory containing your templates
templates = Jinja2Templates(directory="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request":request, "current_route":"/home"})

@app.get("/index.html", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request":request, "current_route":"/home"})

@app.get("/classification", response_class=HTMLResponse)
async def classification(request: Request):
    return templates.TemplateResponse("classification.html", {"request":request, "current_route":"/classification"})

@app.get("/show_similar_companies", response_class=HTMLResponse)
async def show_similar_companies(request: Request):
    return templates.TemplateResponse("show_similar_companies.html", {"request":request, "current_route":"/show_similar_companies"})

@app.get("/show_knowledge_graph", response_class=HTMLResponse)
async def show_knowledge_graph(request: Request):
    return templates.TemplateResponse("show_knowledge_graph.html", {"request":request, "current_route":"/show_knowledge_graph"})

@app.get("/crawl_show_kg", response_class=HTMLResponse)
async def crawl_show_kg(request: Request):
    return templates.TemplateResponse("crawl_show_kg.html", {"request":request, "current_route":"/crawl_show_kg"})

@app.get("/graph_exploration", response_class=HTMLResponse)
async def graph_exploration(request: Request):
    return templates.TemplateResponse("graph_exploration.html", {"request":request, "current_route":"/graph_exploration"})

@app.get("/jobs", response_class=HTMLResponse)
async def jobs(request: Request):
    return templates.TemplateResponse("jobs.html", {"request":request, "current_route":"/jobs"})

@app.get("/insurance_claim", response_class=HTMLResponse)
async def insurance_claim(request: Request):
    return templates.TemplateResponse("insurance_claim.html", {"request":request, "current_route":"/insurance_claim"})

@app.get("/shortest_path", response_class=HTMLResponse)
async def shortest_path(request: Request):
    return templates.TemplateResponse("shortest_path.html", {"request":request, "current_route":"/shortest_path"})

@app.get("/griffin_travels", response_class=HTMLResponse)
async def griffen_travel(request: Request):
    return templates.TemplateResponse("griffen_travel.html", {"request":request, "current_route":"/griffin_travels"})
 
@app.get("/reconcile_entities", response_class=HTMLResponse)
async def reconcile_entities(request: Request):
    return templates.TemplateResponse("reconcile_entities.html", {"request":request, "current_route":"/reconcile_entities"})

@app.post("/downloadPolicyPdf")
async def download_pdf(request: Request):
    try:
        # Parse JSON data from request body
        data = await request.json()
        inclusions = "";

        if len(data['inclusions']) > 0:
            for item in data['inclusions']:
                if item['coverageAmount'] and item['coverageAmount']!="0" and item['coverageAmount']!=0:     
                    inclusions += f''' <li style="font-size:13px">{item['coverageName']} - ${item['coverageAmount']}</li> '''
        logo = ""
        if "allianztravelinsurance.com" in data['carrier'] :
            logo = "https://www.allianztravelinsurance.com/v_1534172261343/media/companies/logos_291/Allianz_Travel.png" 
        elif "travelguard" in data['carrier'] :
            logo = "https://www.travelguard.com/content/dam/travelguard/us/images/logos/TG-r-250w-c_blue.png" 

        htmlBody = f'''
            <!DOCTYPE HTML>
            <html lang="en">
                <head>
                    <title>ZeniaGraph</title>
                    <meta charset="utf-8" />
                </head>
                <body>    
                    <div style="text-align:center"><img src="{logo}"></div>
                    <div style="margin-top:40px">
                        <table>
                            <tr>
                                <td width="16%"><h2 style="font-size:15px">Plan Name:</h2></td>
                                <td style="font-size:13px">{data['plan_name']}</td>
                            </tr>
                        </table>
                    </div>
                    <div style="margin-top:15px">
                        <table>
                            <tr>
                                <td width="19%"><h2 style="font-size:15px">Policy Document:</h2></td>
                                <td><div><a style="font-size:13px" target="_blank" href="{data['pdf_link']}">View Quote</a></div></td>
                            </tr>
                        </table>
                    </div>
                    <div style="margin-top:15px">
                        <table>
                            <tr>
                                <td><h2 style="font-size:15px">Summary:</h2></td>
                            </tr>
                            <tr>
                                <td style="font-size:13px">{data['summary']}</td>
                            </tr>
                        </table>
                    </div>
                    <div style="margin-top:15px">
                        <h2 style="font-size:15px">Inclusions:</h2>
                        <ul>
                            {inclusions}
                        </ul>
                    </div>    
                </body>
            </html>

        '''
        
        
        # Convert HTML content to PDF
        pdf_data = BytesIO()
        pisa.CreatePDF(htmlBody, dest=pdf_data, encoding='utf-8')
        
        # Send the PDF file as a response
        return Response(content=pdf_data.getvalue(), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="example.pdf"'})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/getClassifiedDataFromDocs")
async def getClassifiedDataFromDocs(file: UploadFile = File(...)):
    result = {"records":{}}
    url = EMBEDDING_SERVICE_URL +"/embedding/api/getClassifiedDataFromDocs/"
    files = {'file': file.file}
    response = requests.post(url, files=files)
    result['records'] = response.json()
    return result

def start_server():
    uvicorn.run(
        'main:app',
        port=8000,
        host=HOST,
        log_level="debug",
        reload=True,
    )

if __name__ == "__main__":
    start_server();
