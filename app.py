# Standard library imports
import json
import logging
import os
import re
import secrets
import shutil
import uuid
from pathlib import Path
from typing import Optional

# Third party imports
import arxiv
import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from openai import OpenAI
from pydantic import BaseModel
from redis import Redis
from rq import Queue

# Local imports
from aws_utils import get_mp3_url, upload_mp3_to_s3
from chat_arxiv import (ask_questions, check_namespace_exists, embed_and_upsert, 
                        prompt_chat, prompt_podcast, split_pdf_into_chunks)
from db_handling import Action
from podcast import (add_intro_outro, append_audio_segments, create_directory, 
                     export_audio, generate_script, generate_speech, 
                     overlay_bg_music_on_final_audio)
from podcast_gemini import generate_key_insights, pdf_to_text
from utils import create_paper_dict, pinecone_connect, pinecone_connect_2, pinecone_retrieval

logging.basicConfig(level=logging.INFO)

load_dotenv()

db_actions = Action(
    host=os.getenv('HOST'),
    dbname=os.getenv('DATABASE'),
    user=os.getenv('USERNAME'),
    password=os.getenv('PASSWORD'),
    port=os.getenv('PORT')
)

r = Redis(
  host=os.getenv('REDIS_HOST'),
  port=os.getenv('REDIS_PORT'),
#   password=os.getenv('REDIS_PASSWORD')
)

q = Queue(connection=r)

# initialise fastapi app
app = FastAPI(
    title="PaperBrain",
    docs_url=None
    )

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, os.getenv('FASTAPI_USERNAME'))
    correct_password = secrets.compare_digest(credentials.password, os.getenv('FASTAPI_PASSWORD'))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(username: str = Depends(get_current_username)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


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

def create_podcast(paperurl: str):
    '''
    Creates Podcast using RAG from Pinecone + Script Generation from GPT-4 + TTS w Whisper
    '''

    # Initialize Pinecone index and OpenAI client here
    _, index = pinecone_connect_2()

    # Extract the paper IDs
    paper_id = os.path.splitext(os.path.basename(paperurl))[0]

    # Check if a namespace exists in Pinecone with this pape ID
    flag = check_namespace_exists(paper_id=paper_id, index=index)
    logging.info(flag)

    if flag:
        logging.info("Paper found in Pinecone:  Already Indexed")

    else:
        logging.info("Paper not Indexed: Indexing Now ->")
        response = requests.get(paperurl)


        if response.status_code == 200:
            folder_path = f'ask-arxiv/{paper_id}'
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            with open(f'{folder_path}/{paper_id}.pdf', 'wb') as f:
                f.write(response.content)

        # Split PDF into chunks
        texts, metadatas = split_pdf_into_chunks(paper_id=paper_id)
        logging.info("chunked %s", paper_id)

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

    key_findings = [ask_questions(question=message, paper_id=paper_id, prompt=prompt_podcast, index=index) for message in messages]

    logging.info(key_findings)

    try:
        paper = arxiv.Search(id_list=[paper_id]).results()

        paper_info = [
                {
                    "TITLE": item.title,
                    "AUTHORS": ", ".join(author.name for author in item.authors),
                    "ABSTRACT": item.summary,
                }
            for item in paper
            ]

        key_findings.insert(0, str(paper_info))
    except Exception:
        pass

    logging.info("After Adding Paper Info %s", key_findings)

    # Information to generate podcast script
    response_dict = generate_script(key_findings=key_findings)

    # generate JSON to insert in Database
    response_dict_json = json.dumps(response_dict) 

    # Create directory for the podcast
    create_directory(paper_id)

    # Generate speech
    speech_segments = list(generate_speech(response_dict))

    # Append audio segments
    final_audio = append_audio_segments(speech_segments)

    # Overlay background music on final audio
    final_audio = overlay_bg_music_on_final_audio(final_audio)

    # Add outro
    final_audio_w_outro = add_intro_outro(final_audio)

    # Export audio
    export_audio(final_audio_w_outro, paper_id)

    # Upload podcast to AWS S3
    upload_mp3_to_s3(paper_id=paper_id)

    # Delete PDF and Podcast
    shutil.rmtree(f'ask-arxiv/{paper_id}')
    shutil.rmtree(f'podcast/{paper_id}')

    new_podcast_url = get_mp3_url(f'{paper_id}.mp3')['url']

    title = paper_info[0]['TITLE']
    authors = paper_info[0]['AUTHORS']
    abstract = paper_info[0]['ABSTRACT']

    db_actions.update_podcast_information(paper_id=paper_id, title=title, authors=authors, abstract=abstract, transcript=response_dict_json, s3_url=new_podcast_url, status='SUCCESS')
    logging.info("Podcast information updated.")

    return "DONE"


def create_podcast_gemini(paperurl: str):
    '''
    Creates Podcast using Info Extractions using Gemini Pro + Script Generation from GPT-4 + TTS w Whisper
    '''
    # Extract the paper IDs
    pattern = r"/pdf/(\d+\.\d+)"
    match = re.search(pattern, paperurl)
    if match:
        # Extract the paper ID from the matched group
        paper_id = match.group(1)
        print(paper_id, "This is Paper_ID")
    else:
        return None
    
    response = requests.get(paperurl)

    if response.status_code == 200:
        folder_path = f'ask-arxiv/{paper_id}'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        with open(f'{folder_path}/{paper_id}.pdf', 'wb') as f:
            f.write(response.content)

    try:
        paper = arxiv.Search(id_list=[paper_id]).results()

        paper_info = [
                {
                    "TITLE": item.title,
                    "AUTHORS": ", ".join(author.name for author in item.authors),
                    "ABSTRACT": item.summary,
                }
            for item in paper
            ]

    except Exception:
        pass
    
    title = paper_info[0]['TITLE']
    authors = paper_info[0]['AUTHORS']
    abstract = paper_info[0]['ABSTRACT']

    # convert pdf to text
    research_paper_text = pdf_to_text(f'{folder_path}/{paper_id}.pdf')

    # generate key insights
    key_insights = generate_key_insights(research_paper_text=research_paper_text)
    
    response_dict = generate_script(title=title, abstract=abstract, authors=authors, key_findings=key_insights)

    # generate JSON to insert in Database
    response_dict_json = json.dumps(response_dict) 

    # Create directory for the podcast
    create_directory(paper_id)

    # Generate speech
    speech_segments = list(generate_speech(response_dict))

    # Append audio segments
    final_audio = append_audio_segments(speech_segments)

    # Overlay background music on final audio
    final_audio_with_bg = overlay_bg_music_on_final_audio(final_audio)
    # Add outro and intro
    final_audio_w_outro_intro = add_intro_outro(final_audio_with_bg)

    # Export audio
    export_audio(final_audio_w_outro_intro, paper_id)

    # Upload podcast to AWS S3
    upload_mp3_to_s3(paper_id=paper_id)

    # Delete PDF and Podcast
    shutil.rmtree(f'ask-arxiv/{paper_id}')
    shutil.rmtree(f'podcast/{paper_id}')

    new_podcast_url = get_mp3_url(f'{paper_id}.mp3')['url']

    db_actions.update_podcast_information(paper_id=paper_id, title=title, authors=authors, abstract=abstract, transcript=response_dict_json, keyinsights=key_insights, s3_url=new_podcast_url, status='SUCCESS')
    logging.info("Podcast information updated.")

    return "DONE"


@app.get("/")
async def home():
    return {"message": "Hello World"}


@app.post("/semantic-search")
async def search(query: str, categories: Optional[str]=None, year: Optional[str]=None, index = Depends(get_pinecone_index), client: OpenAI = Depends(get_openai_client)):
    # calculate query embeddings
    response = client.embeddings.create(input=query, model='text-embedding-3-small')
    query_vector = response.data[0].embedding

    # perform semantic search over PineconeDB
    query_response = pinecone_retrieval(index=index, vector=query_vector, k=20, categories=categories, year=year)

    papers_list = [create_paper_dict(match) for match in query_response['matches']]

    return papers_list


@app.post("/ask-arxiv")
async def ask(request: AskArxivRequest,  index = Depends(get_pinecone_index), client: OpenAI = Depends(get_openai_client)):
    # redis_client.flushall()
    from ask_arxiv import rag_pipeline

    index = get_pinecone_index()
    # calculate query embeddings
    response = client.embeddings.create(input=request.question, model='text-embedding-3-small')
    query_vector = response.data[0].embedding

    top_4_papers = pinecone_retrieval(index=index, vector=query_vector, k=4)
    # unique ID for a new question
    u_id = str(uuid.uuid4())

    # Create a Directory for each question to download the top_3 papers
    dir_path = Path(f'ask-arxiv/{u_id}')
    dir_path.mkdir(parents=True, exist_ok=True)

    # Download the top 5 papers
    for i in range(len(top_4_papers['matches'])):
        ID = top_4_papers['matches'][i]['id']
        url = f"https://arxiv.org/pdf/{ID}.pdf"
        response = requests.get(url)

        # Check if the request was successful and download paper
        if response.status_code == 200:
            with open(dir_path / f'{ID}.pdf', 'wb') as f:
                f.write(response.content)

    response = rag_pipeline(u_id=u_id, question=request.question)

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
            "authors": paper.authors,
            "pdfurl": paper.pdf_url,
            "abstract": paper.summary,
        }
        for paper in papers
    ]

    shutil.rmtree(f'ask-arxiv/{u_id}')

    return {
            "answer": response.response,
            "citation": paper_info,
           }


@app.post('/indexpaper')
async def index_paper(paperurl: str, index = Depends(get_pinecone_index_2)):
    print("Received request data:", paperurl)
    
    # Extract the paper IDs
    pattern = r"/pdf/(\d+\.\d+)"
    match = re.search(pattern, paperurl)
    if match:
        # Extract the paper ID from the matched group
        paper_id = match.group(1)
        print(paper_id, "This is Paper_ID")
    else:
        return None

    # Check if a namespace exists in Pinecone with this paper ID
    flag = check_namespace_exists(paper_id=paper_id, index=index)

    if flag:
        print("Already indexed")

    else:
        print("Not Indexed, Indexing Now ->")
        response = requests.get(paperurl)

        # Check if the request was successful and download the pdf
        if response.status_code == 200:
            os.makedirs(f'ask-arxiv/{paper_id}', exist_ok=True)  # This will create the directory if it does not exist
            with open(f'ask-arxiv/{paper_id}/{paper_id}.pdf', 'wb') as f:
                f.write(response.content)

       # Split PDF into chunks
        texts, metadatas = split_pdf_into_chunks(paper_id=paper_id)
        print("chunked", paper_id)

        # Create embeddings and upsert to Pinecone
        embed_and_upsert(paper_id=paper_id, texts=texts,
                            metadatas=metadatas, index=index)
        
        shutil.rmtree(f'ask-arxiv/{paper_id}')

    return {"paper_id": paper_id}


# Chat with arxiv paper
@app.post('/explain-new')
async def explain_question(paper_id: str, message: str, index = Depends(get_pinecone_index_2)):
    print(index)
    print(paper_id)
    answer = ask_questions(question=message, paper_id=paper_id, prompt=prompt_chat, index=index)

    return {"answer":answer}

def handle_job_failure(job):
    # job_id is the same as paper_id in your case
    job_id = job.get_id()
    print(job_id)
    db_actions.delete_podcast(paper_id=job_id)


@app.post('/podcast')
async def podcast(paperurl: str):
    # Extract the paper IDs
    pattern = r"/pdf/(\d+\.\d+)"
    match = re.search(pattern, paperurl)
    if match:
        # Extract the paper ID from the matched group
        paper_id = match.group(1)
        print(paper_id, "This is Paper_ID")
    else:
        return None
    # podcast_exists, _ = check_podcast_exists(paper_id=paper_id) # checking via s3, prone to error
    podcast_exists = db_actions.check_podcast_exists(paper_id=paper_id) # cheking via Supabase -- more robust
    print(podcast_exists)
    if podcast_exists:
        print("podcast exisits in s3")
        paper_info = db_actions.get_podcast_info(paper_id=paper_id)

        return {
            "flag": True,
            "data":paper_info
            }
    else:
        pending = db_actions.check_pending_status(paper_id=paper_id)
        print(pending)
        if len(pending) > 0:
            return {"message":"Job in Queue"}

        else:
            job = q.enqueue(
                # create_podcast, 
                create_podcast_gemini,
                args=[paperurl],
                # result_ttl=1234,
                job_timeout=1000,
                job_id=paper_id, # use the job id while enqueuing
                failure_callback=handle_job_failure,
            )

            db_actions.add_new_podcast(paper_id=paper_id, status='PENDING')

            return { 
                "flag": False,
                "job_id":paper_id
            }


# @app.post("/daily-digest/")
# async def daily_digest(user_id: str, date: str, client: OpenAI = Depends(get_openai_client)):

#     cache_key = f'{user_id}:{date}'

#     cached_result = redis_client.get(cache_key)

#     if cached_result:
#         # If the result is in the cache, return it directly
#         return json.loads(cached_result)
#     else:
#         database = Actions()

#         categories, interest = database.get_user_preference(user_id=user_id)

#         papers_lists = []

#         for category in categories:
#             papers_data = fetch_papers(category=category)
#             papers_lists.append(papers_data)

#         answer = rank_papers(interest=interest, papers_list=papers_lists, client=client)

#         response_json = json.loads(answer)

#         redis_client.setex(cache_key, 24*3600, json.dumps(response_json))

#         return response_json

