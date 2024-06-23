import os
import json
import shutil
import logging
from typing import List

from app.engine.podcast_utils import (
    generate_key_insights,
    generate_podcast_script,
    get_podcast_thumbnail
    )
from app.engine.audio_processing import (
    generate_speech,
    append_audio_segments,
    overlay_bg_music_on_final_audio,
    add_intro_outro,
    export_audio
    )
from app.engine.chat_utils import (
    prepare_data,
    ask_questions,
    embed_and_upsert,
    create_prompt_template,
)

from config import (PODCAST_PROMPT_TEMPLATE, PODCAST_STORAGE_PATH)
from app.service.arxiv_service import ArxivManager
from app.service.pinecone_service import PineconeService
from app.service.aws_service import S3Manager
from app.db.db_actions import Action

prompt = create_prompt_template(PODCAST_PROMPT_TEMPLATE)


s3_manager = S3Manager()
arxiv_manager = ArxivManager()
database_action = Action()
pinecone_service = PineconeService(
    api_key = os.getenv('PINECONE_API_KEY_2'),
    index_name = os.getenv('PINECONE_INDEX_NAME_2'),
    environment = os.getenv('PINECONE_ENVIRONMENT_2')
)


async def create_podcast(userid: str, paperurl: str, method: str, style: str, speakers: List[str], title: str=None, authors: str=None, abstract: str=None):
    '''
    Creates Podcast using specified method + Script Generation from GPT-4 + TTS w Whisper
    '''
    if len(speakers) == 1:
        # TODO: Implement single speaker
        solo_speaker = speakers[0]
    else:
        speaker_one = speakers[0].upper()
        speaker_two = speakers[1].upper()
        speaker_three = speakers[2].upper()

    paper_id = arxiv_manager.id_from_url(paperurl)
    thumbnail_style = paper_id + '-' + style
    paper_id = (paper_id + '-' + style + '-' + '-'.join(speakers)).replace(" ", "-")


    if method == 'gemini':
        # convert pdf to text
        research_paper_text = arxiv_manager.get_pdf_txt(paperurl)
        key_insights = database_action.get_key_insights(paper_id=paper_id.split("-")[0])

        if key_insights is None:
            logging.info("Generating Key insights as previously not found for paper_id: %s", paper_id)
            # generate key insights
            key_insights = generate_key_insights(research_paper_text=research_paper_text)

    elif method == 'rag':
        # Check if a namespace exists in Pinecone with this paper ID
        flag = pinecone_service.check_paper_exists(paper_id=paper_id)
        logging.info(f"Bool if paper already indexed {flag}")

        if not flag:
            logging.info("Paper not Indexed: Indexing Now ->")
            # Split PDF into chunks
            texts, metadatas = prepare_data(paperurl=paperurl)
            logging.info("chunked %s", paper_id)
            # Create embeddings and upsert to Pinecone
            embed_and_upsert(texts=texts, metadatas=metadatas, index=pinecone_service.index)

        messages = [
            "What are the main FINDINGS of this paper?",
            "What are the METHODS used in this paper?",
            "What are the main STRENGTHS of this paper?",
            "What are the main LIMITATIONS of this paper?",
            "What are the main APPLICATION of this paper?",
        ]
        key_insights = [ask_questions(question=message, paper_id=paper_id, prompt=prompt, index=pinecone_service.index) for message in messages]
        logging.info("Relevant info retrieved and Key Findings computed")
    else:
        raise ValueError("Invalid method specified")

    # Generate the Podcast Script
    response_dict = generate_podcast_script(
        title=title,
        abstract=abstract,
        authors=authors,
        key_findings=key_insights,
        style=style,
        speaker_one=speaker_one,
        speaker_two=speaker_two,
        speaker_three=speaker_three,
    )

    # generate JSON to insert in Database
    response_dict_json = json.dumps(response_dict) 

    # Create directory for the podcast
    podcast_dir = f'{PODCAST_STORAGE_PATH}/{paper_id}'

    if not os.path.exists(podcast_dir):
        os.makedirs(podcast_dir)

    # Generate speech
    speech_segments = list(generate_speech(response_dict))

    # Append audio segments
    final_audio = append_audio_segments(speech_segments)

    # Overlay background music on final audio
    final_audio_with_bg = overlay_bg_music_on_final_audio(final_audio, style=style)
    
    # Add outro and intro
    final_audio_w_outro_intro = add_intro_outro(final_audio_with_bg)

    # Export audio
    export_audio(final_audio_w_outro_intro, paper_id)

    # Get Paper Thumbnail
    image_bytes = get_podcast_thumbnail(paperurl=paperurl, style=style)

    # Upload thumbnail to AWS S3
    s3_manager.upload_thumbnail_to_s3(paper_id=thumbnail_style, image_bytes=image_bytes)

    # Upload podcast to AWS S3
    s3_manager.upload_mp3_to_s3(paper_id=paper_id)

    # Delete Podcast directory
    shutil.rmtree(podcast_dir)

    new_podcast_url = s3_manager.get_url(f'{paper_id}.mp3')['url']
    
    thumbnail_url = s3_manager.get_url(f'{thumbnail_style}.png')['url']

    database_action.update_podcast_information(
            paper_id=paper_id, 
            transcript=response_dict_json,
            keyinsights=key_insights if method == 'gemini' else 'None',
            s3_url=new_podcast_url,
            thumbnail=thumbnail_url,
            status='SUCCESS'
    )

    logging.info("Podcast information updated.")

    return "DONE"