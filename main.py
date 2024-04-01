from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from utils import pinecone_connect, pinecone_retrieval, create_paper_dict, pinecone_connect_2
from podcast import generate_audio_whisper, generate_script
from chat_arxiv import check_namespace_exists, split_pdf_into_chunks, embed_and_upsert, ask_questions, prompt_chat, prompt_podcast
from daily_digest import fetch_papers, rank_papers
from db_handling import Actions
from aws_utils import check_podcast_exists, upload_mp3_to_s3, get_mp3_url
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI 
import requests
import arxiv
import json
import uuid
import redis
import os

load_dotenv()

# initialise fastapi app 
app = FastAPI()

# initialise redis client
redis_client = redis.Redis(
  host=os.getenv('REDIS_HOST'),
  port=os.getenv('REDIS_PORT'),
  password=os.getenv('REDIS_PASSWORD')
)


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

def get_pinecone_index_2():
    pc, index = pinecone_connect_2()
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
async def search(query: str, categories: Optional[str]=None, year: Optional[str]=None, index = Depends(get_pinecone_index), client: OpenAI = Depends(get_openai_client)):
    # calculate query embeddings
    response = client.embeddings.create(input=query, model='text-embedding-ada-002')
    query_vector = response.data[0].embedding

    # perform semantic search over PineconeDB
    query_response = pinecone_retrieval(index=index, vector=query_vector, k=20, categories=categories, year=year)
    
    papers_list = [create_paper_dict(match) for match in query_response['matches']]

    return papers_list


@app.post("/ask-arxiv/")
async def ask(request: AskArxivRequest,  index = Depends(get_pinecone_index), client: OpenAI = Depends(get_openai_client)):
    # redis_client.flushall()
    
    from ask_arxiv import rag_pipeline

    index = get_pinecone_index()
    # calculate query embeddings
    response = client.embeddings.create(input=request.question, model='text-embedding-ada-002')
    query_vector = response.data[0].embedding

    top_3_papers = pinecone_retrieval(index=index, vector=query_vector, k=3)

    # unique ID for a new question
    u_id = str(uuid.uuid4()) 

    # Create a Directory for each question to download the top_5 papers
    dir_path = Path(f'ask-arxiv/{u_id}')
    dir_path.mkdir(parents=True, exist_ok=True)

    # Download the top 5 papers
    for i in range(len(top_3_papers['matches'])):
        ID = top_3_papers['matches'][i]['id']
        url = f"https://arxiv.org/pdf/{ID}.pdf"
        response = requests.get(url)

        # Check if the request was successful and download paper
        if response.status_code == 200:
            with open(dir_path / f'{ID}.pdf', 'wb') as f:
                f.write(response.content)  

    index_rag, service_context = rag_pipeline(u_id=u_id)

    query_engine = index_rag.as_query_engine(
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
            "citation": paper_info,
           }


@app.post('/indexpaper/')
async def index_paper(paperurl: str, index = Depends(get_pinecone_index)):

    # Extract the paper ID
    paper_id = os.path.splitext(os.path.basename(paperurl))[0]

    # Check if a namespace exists in Pinecone with this paper ID
    flag = check_namespace_exists(paper_id=paper_id, index=index)

    if flag:
        print("Already indexed")
    
    else:
        print("Not Indexed, Indexing Now ->")
        response = requests.get(paperurl)

        # Check if the request was successful and download the pdf
        if response.status_code == 200:
            with open(f'ask-arxiv/{paper_id}.pdf', 'wb') as f:
                f.write(response.content) 

       # Split PDF into chunks
        texts, metadatas = split_pdf_into_chunks(paper_id=paper_id)
        print("chunked", paper_id)

        # Create embeddings and upsert to Pinecone
        embed_and_upsert(paper_id=paper_id, texts=texts,
                            metadatas=metadatas, index=index)

    return {"paper_id": paper_id} 


# Chat with arxiv paper
@app.post('/explain-new')
async def explain_question(paper_id: str, message: str, index = Depends(get_pinecone_index)):
    print(index)
    print(paper_id)
    answer = ask_questions(question=message, paper_id=paper_id, prompt=prompt_chat, index=index)

    return answer


# Chat with arxiv paper
@app.post('/podcast')
async def podcast(paperurl: str, index = Depends(get_pinecone_index_2)):
    # Extract the paper ID
    paper_id = os.path.splitext(os.path.basename(paperurl))[0]

    # Check if podcast already exists
    podcast_exists, podcast_url = check_podcast_exists(paper_id=paper_id)

    if podcast_exists:
        print("podcast exists in S3")
        return get_mp3_url(f'{paper_id}.mp3')
    
    else:
        # Check if a namespace exists in Pinecone with this paper ID
        flag = check_namespace_exists(paper_id=paper_id, index=index)
        print(flag)

        if flag:
            print("Already indexed")
        
        else:
            print("Not Indexed, Indexing Now ->")
            response = requests.get(paperurl)

            # Check if the request was successful and download the pdf
            if response.status_code == 200:
                with open(f'ask-arxiv/{paper_id}.pdf', 'wb') as f:
                    f.write(response.content) 

            # Split PDF into chunks
            texts, metadatas = split_pdf_into_chunks(paper_id=paper_id)
            print("chunked", paper_id)

            # Create embeddings and upsert to Pinecone
            embed_and_upsert(paper_id=paper_id, texts=texts,
                                metadatas=metadatas, index=index)
        
        messages = [
            "What are the main FINDINGS of this paper?",
            "What are the METHODS used in this paper?",
            "What are the main STRENGTHS of this paper?",
            "What are the main LIMITATIONS of this paper?",
            "What are the main APPLICATION of this paper?",

        ]

        key_findings = [ask_questions(question=message, paper_id=paper_id, prompt=prompt_podcast,  index=index) for message in messages]

        print(key_findings)

        try:
            paper = arxiv.Search(id_list=[paper_id]).results()

            paper_info = [
                {
                    "TITLE\n": item.title,
                    "AUTHORS\n": ", ".join(author.name for author in item.authors),
                    "ABSTRACT\n": item.summary,
                }
                for item in paper
                ]
            
            key_findings.insert(0, str(paper_info))

        except Exception:
            pass

        print("After Adding Paper Info", key_findings)

        response_dict = generate_script(key_findings=key_findings)

        print(response_dict)
        # Generate audio from OpenAI's Whisper
        generate_audio_whisper(response_dict=response_dict, paper_id=paper_id)

        # Upload podcast to AWS S3
        upload_mp3_to_s3(paper_id=paper_id)

        os.remove(f'podcast/{paper_id}/{paper_id}.mp3')

        new_podcast_url = get_mp3_url(f'{paper_id}.mp3')

        return new_podcast_url, key_findings, response_dict


@app.post("/daily-digest/")
async def daily_digest(user_id: str, date: str, client: OpenAI = Depends(get_openai_client)):
        
    cache_key = f'{user_id}:{date}'

    cached_result = redis_client.get(cache_key)

    if cached_result:
        # If the result is in the cache, return it directly
        return json.loads(cached_result)
    else:
        database = Actions()

        categories, interest = database.get_user_preference(user_id=user_id)
        
        papers_lists = []

        for category in categories:
            papers_data = fetch_papers(category=category)
            papers_lists.append(papers_data)
        
        answer = rank_papers(interest=interest, papers_list=papers_lists, client=client)
        
        response_json = json.loads(answer)

        redis_client.setex(cache_key, 24*3600, json.dumps(response_json))
        
        return response_json
    