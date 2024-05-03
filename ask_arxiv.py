from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai import OpenAI

def rag_pipeline(u_id: str, question: str):
    reader = SimpleDirectoryReader(f"ask-arxiv/{u_id}")
    llm = OpenAI(temperature=0,)
    data = reader.load_data()
    index = VectorStoreIndex.from_documents(data)
    chat_engine = index.as_chat_engine(chat_mode="best", llm=llm, verbose=True)

    chat_engine = index.as_chat_engine(
        chat_mode="context",
        system_prompt=("""
                    You are an Expert in answering Research question. Your answer is to the point and you don't make things up.\
                    You will receive a query or a question from Me, along with 4 articles/research paper for that query.\
                    Make use of the relevant information for answering. Do not start you answer with 'Based on the given context' or similar phrases.
                """
        ),
    )
    response = chat_engine.chat(
        f"{question}"
    )
    return response