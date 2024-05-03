from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQAWithSourcesChain, RetrievalQA
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from uuid import uuid4
from typing import List
import itertools
import os
import json


load_dotenv()

PROMPT_TEMPLATE = """
    You are an expert assistant for question-answering tasks. Use the following pieces of retrieved content to answer the question. 
    Use four-five sentences and keep the answer concise and to the point, unless the user asks you to be detailed.
    Be very polite and respectful. Give the answers in points whenever required. Use paragraphs and proper formatting. 
    If not required then do not take the entire context for answering. Choose only the most relevant information from the context for answering
    Question: {question} 

    Context: {context} 

    Answer:
    """

PROMPT_TEMPLATE_PODCAST = """
    You are an expert assistant for summarising and information extraction. 
    Use the following pieces of retrieved content to answer the question. 
    Be elaborate and keep the answer information rich and to the point.
    Be very polite and respectful. Give the answers in points whenever required.
    Use all the provided context for answering the questions.
    If you cannot compute the answer from the context, then do not make things up

    Question: {question} 

    Context: {context} 

    Answer:
"""

prompt_chat = PromptTemplate.from_template(template=PROMPT_TEMPLATE,)
prompt_podcast = PromptTemplate.from_template(template=PROMPT_TEMPLATE_PODCAST,)

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = 'text-embedding-ada-002'

def split_pdf_into_chunks(paper_id: str):

    # Create a splitter object
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
    )  
    print("Split function got paper id as", paper_id)

    # load the PDF
    loader = PyPDFLoader(f"ask-arxiv/{paper_id}/{paper_id}.pdf")

    # split the loaded PDF
    pages = loader.load_and_split(text_splitter=text_splitter)

    # Initialize Data structures for for data prep
    texts = [] 
    metadatas = [] 

    # Adding text chunks and preparing Metadata
    for item, page in enumerate(pages):
        texts.append(page.page_content)
        metadata = {
            'paper-id': page.metadata['source'],
            'source': page.page_content,
            'page_no':int(page.metadata['page']) + 1
        }
        record_metadata = {
            "chunk": item, "text": texts[item], **metadata
        }
        metadatas.append(record_metadata)
    
    return texts, metadatas


def chunks(iterable, batch_size=100):
    """A helper function to break an iterable into chunks of size batch_size."""
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))
        

def embed_and_upsert(paper_id: str, texts: List[str], metadatas: List[str], index) -> str:
    # Create an embedding object
    embed = OpenAIEmbeddings(
        model=MODEL,
        openai_api_key=OPENAI_API_KEY
    )
    # Create pinecone.Index with pool_threads=30 (limits to 30 simultaneous requests)
    ids = [str(uuid4()) for _ in range(len(texts))]

    # Send upsert requests in parallel
    async_results = [
        index.upsert(vectors=zip(ids_chunk, embeds_chunk, metadatas_chunk), namespace=paper_id, async_req=True)
        for ids_chunk, embeds_chunk, metadatas_chunk in zip(chunks(ids), chunks(embed.embed_documents(texts)), chunks(metadatas))
    ]
    # Wait for and retrieve responses (this raises in case of error)
    [async_result.get() for async_result in async_results]

    return "Embedded the Arxiv Paper"


def ask_questions(question: str, paper_id: int, prompt: str, index):

    text_field = "text"

    # Create an embedding object
    embeddings = OpenAIEmbeddings(
        model=MODEL,
        openai_api_key=OPENAI_API_KEY
    )

    vectorstore = PineconeVectorStore(
        index=index, embedding=embeddings, text_key=text_field, namespace=paper_id
    )

    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model_name='gpt-3.5-turbo-16k',
        temperature=0.0,
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
    )

    qa_with_sources = RetrievalQA.from_chain_type(  
        llm=llm,  
        chain_type="stuff",  
        retriever=vectorstore.as_retriever(search_kwargs={'k':4}),
        chain_type_kwargs={
            "prompt":prompt,
            "verbose":True,
        } 
    )  
    answer = qa_with_sources.run(question) 

    return answer


def check_namespace_exists(paper_id, index):
    return paper_id in index.describe_index_stats().namespaces
    

def delete_namespace(index, namespace):
    delete_response = index.delete(delete_all=True, namespace=namespace)
