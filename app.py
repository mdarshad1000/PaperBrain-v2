from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from utils import pinecone_connect, pinecone_retrieval, create_paper_dict, pinecone_connect_2
from podcast import (generate_script, load_intro_music, create_directory, generate_speech, save_speech_to_file, append_audio_segment, 
                     load_and_adjust_bg_music, overlay_bg_music, add_outro, export_audio, delete_intermediate_files, delete_pdf)
from chat_arxiv import check_namespace_exists, split_pdf_into_chunks, embed_and_upsert, ask_questions, prompt_chat, prompt_podcast
# from daily_digest import fetch_papers, rank_papers
from aws_utils import get_mp3_url, upload_mp3_to_s3, check_podcast_exists
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
from db_handling import Action
from rq import Queue
from redis import Redis
import logging
import requests
import arxiv
import uuid
import os
import shutil
import json
import requests

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
  password=os.getenv('REDIS_PASSWORD')
)

q = Queue(connection=r)

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
    # Initialize Pinecone index and OpenAI client here
    _, index = pinecone_connect_2()
    # Extract the paper ID
    paper_id = os.path.splitext(os.path.basename(paperurl))[0]

    # Check if a namespace exists in Pinecone with this pape ID
    flag = check_namespace_exists(paper_id=paper_id, index=index)
    logging.info(flag)

    if flag:
        logging.info("Already indexed")

    else:
        logging.info("Not Indexed, Indexing Now ->")
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

    response_dict = generate_script(key_findings=key_findings)
    response_dict_json = json.dumps(response_dict) 

    # Generate audio from OpenAI's Whisper
    final_audio = load_intro_music()
    intermediate_files = []

    directory_name = create_directory(paper_id)
    
    for key in response_dict.keys():
        tts_response = generate_speech(key, response_dict[key])
        filename = f"{directory_name}/{key}.mp3"
        save_speech_to_file(tts_response, filename)
        intermediate_files.append(filename)
        final_audio = append_audio_segment(filename, final_audio)

    bg_music = load_and_adjust_bg_music()
    final_mix = overlay_bg_music(final_audio, bg_music)
    final_mix = add_outro(final_mix)
    export_audio(final_mix, paper_id)
    delete_intermediate_files(intermediate_files)
    delete_pdf(paper_id)

    # Upload podcast to AWS S3
    upload_mp3_to_s3(paper_id=paper_id)

    os.remove(f'podcast/{paper_id}/{paper_id}.mp3')

    new_podcast_url = get_mp3_url(f'{paper_id}.mp3')['url']

    db_actions.update_podcast_status(paper_id=paper_id, status='SUCCESS')
    logging.info("Podcast status updated to SUCCESS.")

    title = paper_info[0]['TITLE']
    authors = paper_info[0]['AUTHORS']
    abstract = paper_info[0]['ABSTRACT']

    db_actions.update_podcast_information(paper_id=paper_id, title=title, authors=authors, abstract=abstract, transcript=response_dict_json, s3_url=new_podcast_url)
    logging.info("Podcast information updated.")

    return "DONE"


@app.get("/")
async def home():
    return {"message": "Hello World"}


@app.post("/semantic-search")
async def search(query: str, categories: Optional[str]=None, year: Optional[str]=None, index = Depends(get_pinecone_index), client: OpenAI = Depends(get_openai_client)):
    # calculate query embeddings
    response = client.embeddings.create(input=query, model='text-embedding-ada-002')
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
    response = client.embeddings.create(input=request.question, model='text-embedding-ada-002')
    query_vector = response.data[0].embedding

    top_3_papers = pinecone_retrieval(index=index, vector=query_vector, k=3)

    # unique ID for a new question
    u_id = str(uuid.uuid4())

    # Create a Directory for each question to download the top_3 papers
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
async def index_paper(paperurl: str, index = Depends(get_pinecone_index)):
    print("Received request data:", paperurl)
    
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
            with open(f'ask-arxiv/{paper_id}/{paper_id}.pdf', 'wb') as f:
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

    return {"answer":answer}


@app.post('/podcast')
async def podcast(paperurl: str):
    paper_id = os.path.splitext(os.path.basename(paperurl))[0]
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
                create_podcast,
                args=[paperurl],
                # result_ttl=1234,
                job_timeout=1000,
                job_id=paper_id # use the job id while enqueuing
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

