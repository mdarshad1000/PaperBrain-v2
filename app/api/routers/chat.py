import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends

from app.engine.chat_utils import (
    create_prompt_template,
    vector_db_tool,
    # ask_questions,
)
from app.service.pinecone_service import PineconeService
from app.service.openai_service import OpenAIUtils
from config import CHAT_PROMPT_TEMPLATE, CHAT_PROMPT_TEMPLATE_MANUAL, MAP_PROPMT_TEMPLATE, COMBINE_PROMPT_TEMPLATE

load_dotenv()

chat_router = r = APIRouter()

# prompt_langchain_vector_db = create_prompt_template(CHAT_PROMPT_TEMPLATE)


def get_pinecone_service():
    api_key = os.getenv("PINECONE_API_KEY_2")
    index_name = os.getenv("PINECONE_INDEX_NAME_2")
    environment = os.getenv("PINECONE_ENVIRONMENT_2")
    return PineconeService(
        api_key=api_key, index_name=index_name, environment=environment
    )


def get_async_openai_client():
    return OpenAIUtils.get_async_openai_client()


def get_agentic_client():
    return OpenAIUtils.get_agentic_client()


# def get_groq_client():
#     return Groq(
#         api_key=os.environ.get("GROQ_API_KEY"),
    # )


@r.post("/explain-new")
async def explain_question(
    paper_id: str, message: str, pinecone_service=Depends(get_pinecone_service)
):

    answer = await vector_db_tool(
        question=message,
        paper_id=paper_id,
        prompt=CHAT_PROMPT_TEMPLATE_MANUAL,
        pinecone_service=pinecone_service,
        async_openai_client=get_async_openai_client(),
        agentic_client=get_agentic_client(),
    )
    # answer = await ask_questions(
    #     question=message, paper_id=paper_id, prompt=prompt_langchain_vector_db, index=pinecone_service.index
    # )
    return {"answer": answer}
