from pydantic import BaseModel


class SearchTerms(BaseModel):
    search_term: str

class NlpClassification(BaseModel):
    url: str

class SparqlGPT(BaseModel):
    input: str

class NlpClassificationEntities(BaseModel):
    input: str

class NearestFriendParams(BaseModel):
    searching_person:str
    target_company:str


class PersonToPersonParams(BaseModel):
    searching_person:str
    target_person:str
    filter_type: list

class DataExtractionParams(BaseModel):
    text:str

class chatCompletion(BaseModel):
    prompt:str
    model: str

class langchainSummary(BaseModel):
    pdf_url:str

 
