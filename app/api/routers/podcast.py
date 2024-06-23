import logging
from typing import List
from fastapi import APIRouter

from app.db.db_actions import Action
from app.service.arxiv_service import ArxivManager

from app.engine.podcast_task import create_podcast
from app.service.redis_service import job_queue

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

podcast_router = r = APIRouter()

arxiv_manager = ArxivManager()
database_action = Action()


def handle_job_failure(job):
    # job_id is the same as paper_id
    job_id = job.get_id()
    logging.error(f"Job {job_id} failed")
    database_action.delete_podcast(paper_id=job_id)


@r.post("/podcast")
async def podcast(paperurl: str, userid: str, style: str, speakers: List[str], background_music: str=None):

    method = "gemini" # or "RAG" TODO: Implement better RAG using Grobid + Custom Chunking

    paper_id = arxiv_manager.id_from_url(paperurl)

    # Get title, authors, abstract
    title, authors, abstract = None, None, None
    try:
        title, authors, abstract = arxiv_manager.get_metadata(paper_id)
    except Exception as e:
        raise e
    
    podcast_style = paper_id + '-' + style
    
    paper_id = (paper_id + '-' + style + '-' + '-'.join(speakers)).replace(" ", "-")
    
    podcast_exists = database_action.check_podcast_exists(
        paper_id=paper_id
    )  # checking via Supabase -- more robust
    logging.info(f"Podcast exists: {podcast_exists}")

    if podcast_exists:
        logging.info("Podcast exists in S3 and Postgres")

        if not database_action.check_user_podcast_relation(userId=userid, podcast_id=paper_id):
            print('this get executed')
            database_action.update_UserPodcast(userId=userid, podcastId=paper_id)

        paper_info = database_action.get_podcast_info(paper_id=paper_id)

        return {"flag": 0, "data": paper_info}
    
    else:
        pending = database_action.check_pending_status(paper_id=paper_id)
        logging.info(f"Pending status: {pending}")

        if len(pending) > 0:

            if not database_action.check_user_podcast_relation(userId=userid, podcast_id=paper_id):
                database_action.update_UserPodcast(userId=userid, podcastId=paper_id)

            return {"flag": 1, "data": "Job in Queue"}
        
        else:

            job = job_queue.enqueue(
                create_podcast,
                args=[userid, paperurl, method, style, speakers, title, authors, abstract],
                job_timeout=1500,
                job_id=paper_id,  # use the job id while enqueuing
                failure_callback=handle_job_failure,
            )

            database_action.add_new_podcast(paper_id=paper_id, status="PENDING", title=title, authors=authors, abstract=abstract)
            
            similar_style_exists = database_action.check_similar_style_exists(userId=userid, podcast_style=podcast_style)
            
            if similar_style_exists:
                logging.info("Similar style exists for this paper and user.")
                database_action.update_speakers(userId=userid, intial_speakers=paper_id, final_speakers=podcast_style)
            else: 
                logging.info("Similar style does not exist")
                database_action.update_UserPodcast(userId=userid, podcastId=paper_id)
            
            logging.info(f"Enqueued new podcast creation job for paper_id: {paper_id}")

            return {"flag": 2, "data": paper_id}



