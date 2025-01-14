import os
from dotenv import load_dotenv

load_dotenv()

class OpenAIUtils:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MODEL = 'text-embedding-ada-002'

    @staticmethod
    def get_embeddings_api():
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=OpenAIUtils.MODEL, openai_api_key=OpenAIUtils.OPENAI_API_KEY)

    @staticmethod
    def get_chat_api(model_name='gpt-4o', temperature=0.0, streaming=True, callbacks=None):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            openai_api_key=OpenAIUtils.OPENAI_API_KEY,
            model_name=model_name,
            temperature=temperature,
            streaming=streaming,
            callbacks=callbacks
        )

    @staticmethod
    def get_async_openai_client():
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=OpenAIUtils.OPENAI_API_KEY)

