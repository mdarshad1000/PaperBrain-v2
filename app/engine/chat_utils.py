import itertools
import logging

from dotenv import load_dotenv
from uuid import uuid4
from typing import List

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from app.service.openai_service import OpenAIUtils
from app.service.arxiv_service import ArxivManager

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def create_prompt_template(template_str):
    return PromptTemplate.from_template(template=template_str)

def prepare_data(paperurl: str):
    '''
    Split PDF into Chunks
    Prepare Metadata
    '''
    paper_id = ArxivManager.id_from_url(paperurl=paperurl)
    pdf_txt = ArxivManager.get_pdf_txt(paperurl=paperurl)
    paper_metadata = ArxivManager.get_metadata(paper_id=paper_id)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=120,
    )
    pages = text_splitter.split_text(pdf_txt)
    
    # Initialize Data structures for for data prep
    texts = [] 
    metadatas = [] 

    # Adding text chunks and preparing Metadata
    for item, page in enumerate(pages):
        texts.append(page)
        metadata = {
            'paper_id': paper_id,
            'source': page,
            'page_no': item + 1,
            'title': paper_metadata[0],
            'authors': paper_metadata[1]
        }
        record_metadata = {
            "chunk_id": item, "text": texts[item], **metadata
        }
        metadatas.append(record_metadata)

    logging.info(f"Completed splitting PDF for paper_id: {paperurl}")
    return texts, metadatas


def chunker(iterable, batch_size=100):
    """
    A helper function to break an iterable into chunks of size batch_size.
    """
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))


def embed_and_upsert(texts: List[str], metadatas: List[str], index) -> str:
    '''
    Creaate Embeddings and Upsert to Pinecone
    '''
    # Create an embedding object
    embed = OpenAIUtils.get_embeddings_api()

    # Create pinecone.Index with pool_threads=30 (limits to 30 simultaneous requests)
    ids = [str(uuid4()) for _ in range(len(texts))]

    # Send upsert requests in parallel
    async_results = [
        index.upsert(vectors=zip(ids_chunk, embeds_chunk,
                     metadatas_chunk), async_req=True)
        for ids_chunk, embeds_chunk, metadatas_chunk in zip(chunker(ids), chunker(embed.embed_documents(texts)), chunker(metadatas))
    ]

    # Wait for and retrieve responses (this raises in case of error)
    [async_result.get() for async_result in async_results]

    return "Embedded the Arxiv Paper"


def ask_questions(question: str, paper_id: int, prompt: str, index):
    '''
    Retrieve Context and Generate Answers
    '''

    text_field = "text"
    # Create an embedding object
    embeddings = OpenAIUtils.get_embeddings_api()

    vectorstore = PineconeVectorStore(
        index=index, embedding=embeddings, text_key=text_field,
    )

    llm = OpenAIUtils.get_chat_api(
        model_name='gpt-3.5-turbo-16k',
        temperature=0.0,
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
    )

    qa_with_sources = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_kwargs={
                'k': 4,
                'filter': {'paper_id':{"$eq":paper_id}}
                }),
        chain_type_kwargs={
            "prompt": prompt,
            "verbose": True,
        }
    )
    answer = qa_with_sources.run(question)

    return answer

