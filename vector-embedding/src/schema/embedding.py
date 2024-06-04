from pydantic import BaseModel
from settings.enums import EmbeddingType

# base model for search term metadata


class SearchTermMetadata(BaseModel):
    search_term: list
    type: EmbeddingType
