from dotenv import load_dotenv
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.engine.chat_utils import create_prompt_template, ask_questions
from app.service.pinecone_service import PineconeService
from config import CHAT_PROMPT_TEMPLATE

from dotenv import load_dotenv
import os

load_dotenv()

chat_router = r = APIRouter()

prompt = create_prompt_template(CHAT_PROMPT_TEMPLATE)

class ChatRequest(BaseModel):
    paper_id: str = Field(..., description='Paper ID of the research paper')
    message: str = Field(..., description='Question to ask the research paper')

def get_pinecone_service():
    api_key = os.getenv('PINECONE_API_KEY_2')
    index_name = os.getenv('PINECONE_INDEX_NAME_2')
    environment = os.getenv('PINECONE_ENVIRONMENT_2')
    return PineconeService(api_key=api_key, index_name=index_name, environment=environment)

@r.post('/explain-new')
async def explain_question(request: ChatRequest, pinecone_service=Depends(get_pinecone_service)):

    answer = ask_questions(
        question=request.message,
        paper_id=request.paper_id, 
        prompt=prompt,
        index=pinecone_service.index
    )

    return {"answer": answer}