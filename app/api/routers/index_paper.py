import os
import logging
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException, status
from app.service.pinecone_service import PineconeService
from app.service.arxiv_service import ArxivManager
from app.engine.chat_utils import embed_and_upsert, prepare_data


load_dotenv()

index_paper_router = r = APIRouter()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_pinecone_service():
    return PineconeService(
        api_key=os.getenv("PINECONE_API_KEY_2"),
        index_name=os.getenv("PINECONE_INDEX_NAME_2"),
        environment=os.getenv("PINECONE_ENVIRONMENT_2"),
    )

async def process_and_index_paper(paperurl: str, pinecone_service):
    paper_id = ArxivManager.id_from_url(paperurl=paperurl)

    if pinecone_service.check_paper_exists(paper_id=paper_id):
        logging.info(f"Paper ID {paper_id} is already indexed.")
        return
        
    texts, metadatas = await prepare_data(paperurl=paperurl)
    await embed_and_upsert(texts, metadatas, pinecone_service.index)
    logging.info("Successfully Embedded and Upserted to Pinecone")


# TODO: Make Downloading & PDF Extraction part truly async
@r.post("/indexpaper", response_model=dict)
async def index_paper(paperurl: str, pinecone_service=Depends(get_pinecone_service)):

    paper_id = ArxivManager.id_from_url(paperurl=paperurl)

    if not paper_id:
        logging.warning(f"Paper ID not found in URL: {paperurl}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paper ID not found in URL"
        )

    logging.info(f"Indexing new paper ID {paper_id}")
    await process_and_index_paper(paperurl, pinecone_service)
    
    return {"paper_id": paper_id}