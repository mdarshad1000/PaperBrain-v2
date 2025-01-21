import itertools
import logging
import os

from dotenv import load_dotenv
from uuid import uuid4
from typing import List

from langchain.chains import RetrievalQA
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from app.service.openai_service import OpenAIUtils
from app.service.arxiv_service import ArxivManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# def create_prompt_template(template_str):
#     return PromptTemplate.from_template(template=template_str)

def create_prompt_template(template_str: str, input_variables=["text"]):
    return PromptTemplate(template=template_str, input_variables=input_variables)


async def prepare_data(paperurl: str):
    """
    Split PDF into Chunks
    Prepare Metadata
    """
    paper_id = ArxivManager.id_from_url(paperurl=paperurl)
    pdf_txt = await ArxivManager.get_pdf_txt(paperurl=paperurl)

    paper_metadata = await ArxivManager.get_metadata(paper_id=paper_id)

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
            "paper_id": paper_id,
            "source": page,
            "page_no": item + 1,
            "title": paper_metadata[0],
            "authors": paper_metadata[1],
        }
        record_metadata = {"chunk_id": item, "text": texts[item], **metadata}
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


async def embed_and_upsert(texts: List[str], metadatas: List[str], index) -> str:
    """
    Creaate Embeddings and Upsert to Pinecone
    """
    # Create an embedding object
    embed = OpenAIUtils.get_embeddings_api()

    # Create pinecone.Index with pool_threads=30 (limits to 30 simultaneous requests)
    ids = [str(uuid4()) for _ in range(len(texts))]

    # Send upsert requests in parallel
    async_results = [
        index.upsert(
            vectors=zip(ids_chunk, embeds_chunk, metadatas_chunk), async_req=True
        )
        for ids_chunk, embeds_chunk, metadatas_chunk in zip(
            chunker(ids), chunker(embed.embed_documents(texts)), chunker(metadatas)
        )
    ]

    # Wait for and retrieve responses (this raises in case of error)
    [async_result.get() for async_result in async_results]

    return "Embedded the Arxiv Paper"


async def semantic_router(question: str, routing_prompt: str, groq_client):
    """
    Routes the query to either summarization, general Q&A, or a vanilla LLM call based on query analysis.
    """

    response = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "system",
                "content": "You are a routing assistant. Determine if the query requires summarization/fetching key takeaways or General Q&A or simple LLM call.",
            },
            {"role": "user", "content": routing_prompt.format(question=question)},
        ],
        max_completion_tokens=20,
    )
    routing_decision = response.choices[0].message.content.strip()

    if "TOOL: SUMMARIZE" in routing_decision:
        return "summarize"
    elif "TOOL: VECTOR_DB" in routing_decision:
        return "vector_db"
    else:
        return "general"


async def summarize_tool(paper_text: str, map_prompt, combine_prompt, llm_client):

    map_reduce_chain = load_summarize_chain(
        llm=llm_client,
        chain_type="map_reduce",
        map_prompt=map_prompt,
        combine_prompt=combine_prompt,
        return_intermediate_steps=True,
    )
    map_reduce_outputs = map_reduce_chain({"input_documents": paper_text})
    return map_reduce_outputs



async def general_tool(question: str, async_agentic_client):
    pass


async def vector_db_tool(
    question: str,
    paper_id: int,
    prompt: str,
    pinecone_service,
    async_openai_client,
    agentic_client,
):
    """
    Do Retrieval & Generation without using LangChain
    """
    top_k = 7

    response = await async_openai_client.embeddings.create(
        input=question, model="text-embedding-ada-002"
    )

    query_vector = response.data[0].embedding
    retrieved_chunks = pinecone_service.retrieval(
        vector=query_vector, k=top_k, filter_params={"paper_id": {"$eq": paper_id}}
    )

    formatted_chunks = "\n".join(
        [
            f"<<<\nChunk: {i+1}\nText: \"{match['metadata']['text']}\"\n>>>"
            for i, match in enumerate(retrieved_chunks["matches"])
        ]
    )
    # Generate Response from OpenAI
    answer = await agentic_client.chat.completions.create(
        model="agentic-turbo",
        messages=[
            {
                "role": "system",
                "content": """You are an expert assistant for question-answering tasks. 
                    You will be provided with a Question and some paragraph (Context) from a Research Paper. 
                    Your task is to answer the question based on the given context""",
            },
            {
                "role": "user",
                "content": prompt.format(context=formatted_chunks, question=question),
            },
        ],
    )

    return answer.choices[0].message.content  # Optionally return the Source too


# OBSOLETE: Replaced with custom Retrieval + Generation logic above
# async def ask_questions(question: str, paper_id: int, prompt: str, index):
#     """
#     Retrieve Context and Generate Answers using LangChain
#     """
#     text_field = "text"
#     # Create an embedding object
#     embeddings = OpenAIUtils.get_embeddings_api()

#     vectorstore = PineconeVectorStore(
#         index=index,
#         embedding=embeddings,
#         text_key=text_field,
#     )

#     llm = OpenAIUtils.get_chat_api(
#         model_name="gpt-3.5-turbo-16k",
#         temperature=0.0,
#         streaming=True,
#         callbacks=[StreamingStdOutCallbackHandler()],
#     )

#     qa_with_sources = RetrievalQA.from_chain_type(
#         llm=llm,
#         chain_type="stuff",
#         retriever=vectorstore.as_retriever(
#             search_kwargs={"k": 4, "filter": {"paper_id": {"$eq": paper_id}}}
#         ),
#         chain_type_kwargs={
#             "prompt": prompt,
#             "verbose": True,
#         },
#     )
#     answer = qa_with_sources.run(question)
#     return answer
