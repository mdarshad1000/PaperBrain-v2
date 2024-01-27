from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from helpers import pinecone_connect, pinecone_retrieval, create_paper_dict
from rag import rag_pipeline
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel
from pathlib import Path
from openai import OpenAI
import requests
import arxiv
import uuid
import os


# Load environment variables from .env file
load_dotenv()

# initialise fastapi app 
app = FastAPI()


# Enable CORS for all origins 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for Pinecone connection
def get_pinecone_index():
    pc, index = pinecone_connect()
    return index

# Dependency for OpenAI client
def get_openai_client():
    return OpenAI()

# Pydantic model for ask-arxiv request
class AskArxivRequest(BaseModel):
    question: str


@app.get("/")
async def home():
    return {"message": "Hello World"}


@app.post("/semantic-search/")
async def search(query: str, categories: Optional[str], year: Optional[str], index = Depends(get_pinecone_index), client: OpenAI = Depends(get_openai_client)):

    # calculate query embeddings
    response = client.embeddings.create(input=query, model=os.getenv("EMBED_MODEL"))
    query_vector = response.data[0].embedding

    # perform semantic search over PineconeDB
    query_response = pinecone_retrieval(index=index, vector=query_vector, k=20, categories=categories, year=year)
    
    papers_list = [create_paper_dict(match) for match in query_response['matches']]
        
    return papers_list


@app.post("/ask-arxiv/")
async def ask(request: AskArxivRequest,  index = Depends(get_pinecone_index), client: OpenAI = Depends(get_openai_client)):

    _, index = pinecone_connect()
    # calculate query embeddings
    response = client.embeddings.create(input=request.question, model=os.getenv("EMBED_MODEL"))
    query_vector = response.data[0].embedding

    top_5_papers = pinecone_retrieval(index=index, vector=query_vector, k=3)

    # unique ID for a new question
    u_id = str(uuid.uuid4()) 

    # Create a Directory for each question to download the top_5 papers
    dir_path = Path(f'ask-arxiv/{u_id}')
    dir_path.mkdir(parents=True, exist_ok=True)

    # Download the top 5 papers
    for i in range(len(top_5_papers['matches'])):
        ID = top_5_papers['matches'][i]['id']
        url = f"https://arxiv.org/pdf/{ID}.pdf"
        response = requests.get(url)

        # Check if the request was successful and download paper
        if response.status_code == 200:
            with open(dir_path / f'{ID}.pdf', 'wb') as f:
                f.write(response.content)  

    index, service_context = rag_pipeline(u_id=u_id)

    query_engine = index.as_query_engine(
        response_mode="tree_summarize", 
        verbose=True, 
        similarity_top_k=5, 
        service_context=service_context
        )
    
    response = query_engine.query(request.question)

    # Model Response
    answer = response.response

    # Retrieve the Paper ID from the Response object
    arxiv_id = [response.source_nodes[i].node.metadata["file_name"].rstrip('.pdf') for i in range(len(response.source_nodes))]
    arxiv_id = list(set(arxiv_id))

    # Search arxiv using ID for the citation info
    search = arxiv.Search(id_list=arxiv_id)
    papers = list(search.results())
    paper_info = [
        {
            "title": paper.title,
            "authors": paper.authors,
            "pdfurl": paper.pdf_url,
            "abstract": paper.summary,
        }
        for paper in papers
    ]

    return {
            "answer": answer,
            "citation": paper_info
           }