from llama_index import ServiceContext, SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms import OpenAI as LlamaIndexOpenAI

SYSTEM_PROMPT=''' 
    You are an expert in answering Research question. \
    You will receive a query or a question from the user, along with 3 articles/research paper for that query.\
    Make use of the most apt and relevant information for answering."
    '''

def rag_pipeline(u_id):
    service_context = ServiceContext.from_defaults(
        llm=LlamaIndexOpenAI(
            model='gpt-3.5-turbo',
            temperature=0.5,
            system_prompt=SYSTEM_PROMPT,
        ),
        # embed_model=OpenAIEmbedding('text-embedding-3-small'),
        chunk_size=500,
    )
    
    documents = SimpleDirectoryReader(f"ask-arxiv/{u_id}", recursive=True).load_data()
    index = VectorStoreIndex.from_documents(documents)

    return index, service_context