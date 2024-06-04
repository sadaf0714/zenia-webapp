from fastapi import Request
from starlette.responses import JSONResponse
from schema.response import Response
import json


class AppException(Exception):
    def __init__(self, status_code: int, context: Response):
        self.exception_case = self.__class__.__name__
        self.status_code = status_code
        self.context = context

    def __str__(self):
        return (
            f"<AppException {self.exception_case} - "
            + f"status_code={self.status_code} - context={self.context}>"
        )


async def app_exception_handler(request: Request, exc: AppException):
    data = exc.context.json()
    resp = json.loads(data)
    return JSONResponse(status_code=exc.status_code, content=resp)
