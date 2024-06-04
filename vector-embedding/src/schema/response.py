from pydantic import BaseModel


class Response(BaseModel):
    success: bool
    data: dict
    error: str
