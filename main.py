from fastapi import FastAPI
from dotenv import load_dotenv
from llama_index import VectorStoreIndex, SimpleDirectoryReader
from helpers import pinecone_connect, optional_filtering
from typing import Optional
from openai import OpenAI
import requests
import arxiv
import uuid
import os


# Load environment variables from .env file
load_dotenv()

# initialise fastapi app 
app = FastAPI()

# initialise openai Client
client = OpenAI()


# connect to pinecone and initialized serverless
pc, index = pinecone_connect()
    

@app.get("/")
async def home():
    return {"message": "Hello World"}


@app.post("/semantic-search/")
async def search(query: str, categories: Optional[str] = None, year: Optional[str] = None):

    # calculate query embeddings
    response = client.embeddings.create(input=query, model=os.getenv("EMBED_MODEL"))
    query_vector = response.data[0].embedding

    query_response = optional_filtering(index=index, vector=query_vector, k=20, categories=categories, year=year)
    
    papers_list = [
        {
            'Id': {query_response['matches'][i]['id']},
            'Title': {query_response['matches'][i]['metadata']['title']},
            'Abstract': {query_response['matches'][i]['metadata']['abstract']},
            'Authors': {query_response['matches'][i]['metadata']['authors']},
            'PDF Link': f"https://arxiv.org/pdf/{query_response['matches'][i]['id']}.pdf",
            'Date': f"{query_response['matches'][i]['metadata']['month']}, {int(query_response['matches'][i]['metadata']['year'])}",
            'Categories': ', '.join(query_response['matches'][i]['metadata']['categories']),
            'Similarity Score': {round(query_response['matches'][i]['score']*100)},
        }
        for i in range(len(query_response['matches']))
    ]

    return papers_list


@app.post("/ask-arxiv/")
async def ask(question: str):
    pc, index = pinecone_connect()
    # calculate query embeddings
    response = client.embeddings.create(input=question, model=os.getenv("EMBED_MODEL"))
    query_vector = response.data[0].embedding

    top_5_papers = optional_filtering(index=index, vector=query_vector, k=3)

    # unique ID for a new question
    u_id = str(uuid.uuid4()) 

    # Create a Directory for each question to download the top_5 papers
    if not os.path.exists('ask-arxiv/{u_id}'):
        os.makedirs(f'ask-arxiv/{u_id}')

    # Download the top 5 papers
    for i in range(len(top_5_papers['matches'])):
        ID = top_5_papers['matches'][i]['id']
        url = f"https://arxiv.org/pdf/{ID}.pdf"
        response = requests.get(url)

        # Check if the request was successful and download paper
        if response.status_code == 200:
            with open(f'ask-arxiv/{u_id}/{ID}.pdf', 'wb') as f:
                f.write(response.content)
    

    documents = SimpleDirectoryReader(f"ask-arxiv/{u_id}", recursive=True).load_data()
    index = VectorStoreIndex.from_documents(documents)

    query_engine = index.as_query_engine(response_mode="tree_summarize", verbose=True, similarity_top_k=5)
    response = query_engine.query(question)

    # Model Response
    answer = response.response

    # Retrieve the Paper Identifier from the Response object
    arxiv_id = [response.source_nodes[i].node.metadata["file_name"].rstrip('.pdf') for i in range(len(response.source_nodes))]
    arxiv_id = list(set(arxiv_id))

    # Search arxiv using ID for the required info and preapre citation
    search = arxiv.Search(id_list=arxiv_id)
    papers = list(search.results())
    paper_info = [
        {
            "title": paper.title,
            "authors": paper.authors,
            "pdfurl": paper.pdf_url
            # "abstract": papers[0].summary,
            # Add more fields as needed
        }
        for paper in papers
    ]

    return {
            "answer": answer,
            "citation": paper_info
            }