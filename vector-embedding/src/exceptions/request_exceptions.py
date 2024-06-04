from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from schema.response import Response
from settings.constants import REQUIRED_FIELDS_ERROR
import json


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    data = Response(success=False, data={}, error=exc.detail).json()
    resp = json.loads(data)
    return JSONResponse(content=resp, status_code=exc.status_code)


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    data = Response(success=False, data={}, error=REQUIRED_FIELDS_ERROR).json()
    resp = json.loads(data)
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=resp)
