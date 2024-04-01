from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai import OpenAI

def rag_pipeline(u_id: str):
    reader = SimpleDirectoryReader(f"ask-arxiv/{u_id}")
    llm = OpenAI()
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
        "What are the differences between restapi and graphql?"
    )   
    return response






# from llama_index import ServiceContext, SimpleDirectoryReader, VectorStoreIndex, OpenAIEmbedding
# from llama_index.llms import OpenAI as LLamaOpenAI


# SYSTEM_PROMPT = ''' 
#     You are an Expert in answering Research question. Your answer is to the point and you don't make things up.\
#     You will receive a query or a question from Me, along with 4 articles/research paper for that query.\
#     Make use of the relevant information for answering. Do not start you answer with 'Based on the given context' or similar phrases."
#     '''


# def rag_pipeline(u_id):
#     service_context = ServiceContext.from_defaults(
#         llm=LLamaOpenAI(
#             model='gpt-3.5-turbo',
#             temperature=0.3,
#             system_prompt=SYSTEM_PROMPT,
#         ),
#         embed_model=OpenAIEmbedding(),
#         chunk_size=500,
#     )
    
# #     documents = SimpleDirectoryReader(f"ask-arxiv/{u_id}", recursive=True).load_data()
# #     index = VectorStoreIndex.from_documents(documents)

# #     return index, service_context