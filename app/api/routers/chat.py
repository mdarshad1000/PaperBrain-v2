from dotenv import load_dotenv
from fastapi import APIRouter, Depends

from app.engine.chat_utils import create_prompt_template, ask_questions
from app.service.pinecone_service import PineconeService
from config import CHAT_PROMPT_TEMPLATE

from dotenv import load_dotenv
import os

load_dotenv()

chat_router = r = APIRouter()

prompt = create_prompt_template(CHAT_PROMPT_TEMPLATE)

def get_pinecone_service():
    api_key = os.getenv('PINECONE_API_KEY_2')
    index_name = os.getenv('PINECONE_INDEX_NAME_2')
    environment = os.getenv('PINECONE_ENVIRONMENT_2')
    return PineconeService(api_key=api_key, index_name=index_name, environment=environment)

@r.post('/explain-new')  # Changed from post to get
async def explain_question(paper_id: str, message: str, pinecone_service=Depends(get_pinecone_service)):

    answer = ask_questions(
        question=message,  # Changed from request.message to message
        paper_id=paper_id,  # Changed from request.paper_id to paper_id
        prompt=prompt,
        index=pinecone_service.index
    )
    return {"answer": answer}