from fastapi import APIRouter, Depends

from app.engine.chat_utils import QASessionManager, create_prompt_template
from app.service.pinecone_service import PineconeService
from config import CHAT_PROMPT_TEMPLATE

import os
from dotenv import load_dotenv

load_dotenv()

chat_router = r = APIRouter()
qa_session_manager = QASessionManager()

prompt = create_prompt_template(template_str=CHAT_PROMPT_TEMPLATE)

def get_pinecone_service():
    api_key = os.getenv('PINECONE_API_KEY_2')
    index_name = os.getenv('PINECONE_INDEX_NAME_2')
    environment = os.getenv('PINECONE_ENVIRONMENT_2')
    return PineconeService(api_key=api_key, index_name=index_name, environment=environment)

@r.post('/explain-new')
async def explain_question(paper_id: str, userid: str, message: str, pinecone_service=Depends(get_pinecone_service)):

    # Check if it's the user's first question
    flag = 'first' if qa_session_manager.is_first_question(userid, paper_id) else 'subsequent'

    answer = qa_session_manager.ask_question(
        question=message,
        flag=flag,
        userid=userid,
        paper_id=paper_id,
        prompt=prompt,
        index=pinecone_service.index
    )
    return {"answer": answer}