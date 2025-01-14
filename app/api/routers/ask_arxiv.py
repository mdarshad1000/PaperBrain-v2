import os
import re
import cohere
import logging

from dotenv import load_dotenv
from pydantic import BaseModel
from collections import OrderedDict
from fastapi import APIRouter, Depends

from config import ASK_SYSTEM_PROMPT
from app.service.arxiv_service import ArxivManager
from app.service.pinecone_service import PineconeService
from app.service.openai_service import OpenAIUtils
from app.engine.askarxiv_utils import process_and_rank_papers, generate_response

load_dotenv()

askarxiv_router = r = APIRouter()

logging.basicConfig(level=logging.INFO)

class AskArxivRequest(BaseModel):
    question: str

# Dependency functions
def get_arxiv_manager():
    return ArxivManager()


def get_pinecone_service():
    return PineconeService()


def get_async_openai_client():
    return OpenAIUtils.get_async_openai_client()


def get_cohere_client():
    return cohere.Client(os.getenv("COHERE_API_KEY"))

@r.post("/ask-arxiv")
async def ask_arxiv(
    question: str = None,
    arxiv_client: ArxivManager = Depends(get_arxiv_manager),
    pinecone_client: PineconeService = Depends(get_pinecone_service),
    openai_client: OpenAIUtils = Depends(get_async_openai_client),
    cohere_client: cohere.Client = Depends(get_cohere_client),
):
    print('-x-x-x-x-x-x-xx-x-x-x-x-x-x GOT A REQUEST HUEHUE -x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x')
    if question is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No question provided")

    top_K = 10
    top_N = 7

    reranked_list_of_papers = await process_and_rank_papers(
        arxiv_client=arxiv_client,
        pinecone_client=pinecone_client,
        openai_client=openai_client,
        cohere_client=cohere_client,
        query=question,
        top_K=top_K,
        top_N=top_N,
    )

    formatted_response = "\n".join(
        [
            f"<<<\ncitationId: \"{paper['id']}\"\ntitle: \"{paper['title']}\"\n\n{paper['summary']}\n>>>"
            for paper in reranked_list_of_papers
        ]
    )
    response = await generate_response(
        openai_client=openai_client,
        query=question,
        system_prompt=ASK_SYSTEM_PROMPT,
        formatted_response=formatted_response,
    )

    # Find all citations
    citations = re.findall(r"\[(\d{7}|\d+\.\d+)\]", response)

    # Create a mapping dictionary
    citation_mapping = {
        citation: f"[{index+1}]"
        for index, citation in enumerate(list(OrderedDict.fromkeys(citations)))
    }


    for original, replacement in citation_mapping.items():
        response = re.sub(rf"\[{original}\]", replacement, response)

    # Create final Citation Mapping using reranked_list_of_papers
    citation_mapping = {
        replacement: next((paper_info for paper_info in reranked_list_of_papers if paper_info["id"] == original.strip("[]")), None)
        for original, replacement in citation_mapping.items()
    }
    # logging.info('Final citation_mapping: %s', citation_mapping)
    
    no_of_paper_analysed = len(citation_mapping)

    if no_of_paper_analysed == 0:
        response = "Couldn't gather relevant answers from the papers, however this might be helpful!.\n\n" + response
    
    # Prepare the final response as a JSON object
    final_response = {
        "response": response,
        "citation_mapping": citation_mapping,
        "no_of_paper_analysed": no_of_paper_analysed
    }

    return final_response