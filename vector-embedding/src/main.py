import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from routes.index import router
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from settings.config import HOST, PORT
from exceptions.request_exceptions import (
    http_exception_handler,
    request_validation_exception_handler,
)

from exceptions.app_exceptions import app_exception_handler, AppException

# Load environment variables
load_dotenv()

app = FastAPI()


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, e):
    return await http_exception_handler(request, e)


@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request, e):
    return await request_validation_exception_handler(request, e)


@app.exception_handler(AppException)
async def custom_app_exception_handler(request, e):
    return await app_exception_handler(request, e)


# setting up the middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get('/')
async def index():
    return {"status":"ok"}

def start_server():
    print("Starting Server...")
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        timeout_keep_alive=1000,
        log_level="debug",
        reload=True,
    )


if __name__ == "__main__":
    start_server()
