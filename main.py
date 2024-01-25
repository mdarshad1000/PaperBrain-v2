from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from helpers import pinecone_connect, optional_filtering
from typing import Optional, List
import openai
import os

# initialise fastapi app
app = FastAPI()

# Load environment variables from .env file
load_dotenv()

# connect to pinecone and initialized serverless
pc, index = pinecone_connect()
    

@app.get("/")
async def home():
    return {"message": "Hello World"}


@app.post("/semantic-search/")
async def search(query: str, categories: Optional[str] = None, year: Optional[str] = None):

    # calculate query embeddings
    response = openai.Embedding.create(input=query, model=os.getenv("EMBED_MODEL"))
    query_vector = response.data[0]["embedding"]

    query_response = optional_filtering(index=index, vector=query_vector, categories=categories, year=year)

    papers_list = [
        {
            'Id': {query_response['matches'][i]['id']},
            'Title': {query_response['matches'][i]['metadata']['title']},
            'Abstract': {query_response['matches'][i]['metadata']['abstract']},
            'Authors': {query_response['matches'][i]['metadata']['authors']},
            'Date': f"{query_response['matches'][i]['metadata']['month']}, {int(query_response['matches'][i]['metadata']['year'])}",
            'Categories': ', '.join(query_response['matches'][i]['metadata']['categories']),
            'Similarity Score': {query_response['matches'][i]['score']},
        }
        for i in range(len(query_response['matches']))
    ]

    return papers_list
