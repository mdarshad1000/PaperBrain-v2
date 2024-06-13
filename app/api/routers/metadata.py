import os
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from paperswithcode import PapersWithCodeClient

from app.engine.metadata_utils import (
    get_no_of_citations,
    get_dataset_info,
    get_methods_info,
    get_repo_info,
    get_tasks_info,
)

load_dotenv()

metadata_router = r = APIRouter()

def get_client():
    return PapersWithCodeClient(token=os.getenv("PAPERS_WITH_CODE"))


@r.get("/metadata")
async def read_root(
    paper_id: str,
    client: PapersWithCodeClient = Depends(get_client)
):
    try:
        citation_count = get_no_of_citations(paper_id).strip('Cited by')
    except Exception as e:
        logging.error(e)
        pass
    repository = get_repo_info(client, paper_id)
    dataset = get_dataset_info(client, paper_id)
    method = get_methods_info(client, paper_id)
    task = get_tasks_info(client, paper_id)

    return {
        "citation_count": citation_count,
        "repository": repository,
        "dataset": dataset,
        "method": method,
        "task": task
    }