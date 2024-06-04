from pydantic import BaseModel


class SimilarityMetadata(BaseModel):
    similarity_data: list
    query: str
