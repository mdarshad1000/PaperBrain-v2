import os
from typing import Optional
from pydantic import Field, BaseModel
from fastapi import APIRouter, Depends

from app.service.openai_service import OpenAIUtils
from app.service.pinecone_service import PineconeService

semantic_router = r = APIRouter()

def get_async_openai_client():
    return OpenAIUtils.get_async_openai_client()

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="The search query text")
    categories: Optional[str] = Field(None, description="Optional categories to filter the search")
    year: Optional[str] = Field(None, description="Optional year to filter the search")

def create_paper_dict(match):
    """
    Creates a dictionary for a single match.
    """
    return {
        'id': match['id'],
        'title': match['metadata']['title'],
        'summary': match['metadata']['abstract'],
        'authors': {match['metadata']['authors']},
        'pdf_url': f"https://arxiv.org/pdf/{match['id']}.pdf",
        'date': f"{match['metadata']['month']}, {int(match['metadata']['year'])}",
        'categories': match['metadata']['categories'],
        'similarity_score': round(match['score']*100),
    }

def get_pinecone_service():
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME')
    environment = os.getenv('PINECONE_ENVIRONMENT')
    return PineconeService(api_key=api_key, index_name=index_name, environment=environment)

@r.post("/semantic_search")
async def semantic_search(
    request: SemanticSearchRequest,
    pinecone_service=Depends(get_pinecone_service),
    async_openai_client=Depends(get_async_openai_client)
    ):

    # calculate query embeddings
    response = await async_openai_client.embeddings.create(
        input=request.query, model='text-embedding-ada-002')
    query_vector = response.data[0].embedding


    # perform semantic search over PineconeDB
    query_response = pinecone_service.retrieval(
        vector=query_vector, k=20, categories=request.categories, year=request.year)
    
    papers_list = [create_paper_dict(match)
                   for match in query_response['matches']]

    return papers_list