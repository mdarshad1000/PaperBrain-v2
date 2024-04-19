
from openai import OpenAI
from pydub import AudioSegment
from dotenv import load_dotenv
from db_handling import Action
import os
import json
import logging
import sys
from rq import Queue
from redis import Redis
from io import BytesIO

load_dotenv()

logging.basicConfig(level=logging.INFO, )

db_actions = Action(
    host=os.getenv('HOST'),
    dbname=os.getenv('DATABASE'),
    user=os.getenv('USERNAME'),
    password=os.getenv('PASSWORD'),
    port=os.getenv('PORT')
)
# initialize redis and openai connection

r = Redis()
q = Queue(connection=r)
clientOAI = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


SYSTEM_PROMPT = """
    You are a podcast script writer, highly skilled in generating engaging intellectual questions and answers in an
    easy-to-understand podcast style.

    Podcasters:
        The Interviewer's name is Noah Bennett, and the expert name is Ethan Sullivan. Keep in mind that Ethan is not a
        co-author or anyone related to the paper, he is just an Expert. You may consult another Specialist Emma Anderson
        in between the podcast, or even at the starting too (rarely). When consulting her, give a very quick introduction.
        She should have a minimum 2 and maximum of 3 dialogues. Include Emma in the conversation in a very smooth and intelligent way.

    Tone:
        Maintain a conversational yet authoritative tone. Noah and Ethan should engage the audience by discussing the paper's
        content with enthusiasm and expertise. Emma should be consulted for her two cents like the specialist she is.
        Use conversational fillers like Umm, Ohhh I see.., Wow, Hmm, Oh, Mmm, Oh-huh, hold on, I mean etcetera to make the conversation more
        natural. Also include '......' to add breaks in the dialogue

    Very Important Note:
        Provide output in valid JSON format having Keys NOAH1, NOAH2, ... NOAHn for Noah's dialogue where 1, 2, ... n are the dialogue number.
        Similarly, the Keys for ETHAN should be ETHAN1, ETHAN2, ..., ETHANn where 1, 2, ... n are the dialogue number.
        Lastly, the Keys for EMMA should be EMMA1, EMMA2, ... EMMAn where 1, 2, ... n are the dialogue number.

    Make sure to have a very catchy introduction and a very cool sounding conclusion (farewell to expert and audience).
    Generate 15-17 dialouges at maximum.

    Additional Notes:
        Use a blend of technical language and layman terms to make the content accessible to a wide audience.
        Keep the discussion engaging and avoid jargon overload.
        Ensure that each section flows naturally into the next, maintaining a coherent narrative throughout the script.
    """

USER_PROMPT = """
    Based on the given context from a research paper, generate an entire podcast script having 4-5 questions.
    Keep the podcast engaging, ask follow up questions. You may use analogies sometimes to explain the concepts.
    In the introduction always include the phrase 'Welcome to Paper Brain'. Introduce  NOAH, ETHAN in the beginning, and introduce EMMA when required.
    In the conclusion always include a tweaked version of -- 'Check out PaperBrain to explore scientific literature like never before!'
    You are also provided the metadata of the Paper i.e TITLE, AUTHORS, ABSTRACT. Make use of these information
    in the introduction.

    \n\n
    CONTEXT:
    \n
    """

def generate_script(key_findings: str):
    try:
        key_findings_str = ''.join(key_findings)
        logging.info("Sending request to OpenAI...")
        completion = clientOAI.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type":"json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT + key_findings_str}
            ]
        )
    except Exception as e:
        logging.error("Failed to send request to OpenAI: %s", e)
        sys.exit(1)

    try:
        response = completion.choices[0].message.content
        response = response.strip()
        response_dict = json.loads(response)
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response from OpenAI.")
        sys.exit(1)
        
    return response_dict

def load_intro_music():
    logging.info("Loading intro music...")
    return AudioSegment.from_mp3("music_essentials/intro.mp3")

def create_directory(paper_id: str):
    directory_name = f"podcast/{paper_id}"
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
    return directory_name

def generate_speech(response_dict):
    for key, text in response_dict.items():
            voice = "nova" if "EMMA" in key else "onyx" if "ETHAN" in key else "echo"
            logging.info(f"Generating speech for {key} with voice {voice}...")
            audio_response = clientOAI.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            binary_content = audio_response.read()
            in_memory_bytes_file = BytesIO(binary_content)

            dialogue_segment = AudioSegment.from_file(in_memory_bytes_file, format="mp3")
            yield dialogue_segment

def append_audio_segments(audio_generator):
    final_audio = AudioSegment.empty()
    for audio_segment in audio_generator:
        logging.info("Appending this audio segment to the final audio...")
        final_audio += audio_segment
    return final_audio

def overlay_bg_music_on_final_audio(final_audio):
    logging.info("Loading and adjusting background music...")
    bg_music = AudioSegment.from_mp3("music_essentials/bg-music-new-2.mp3") - 10

    logging.info("Overlaying background music onto the final audio...")
    bg_music = bg_music[:len(final_audio)]
    return final_audio.overlay(bg_music - 10, position=7000)

def add_outro(final_mix):
    logging.info("Adding outro...")
    outro_music = AudioSegment.from_mp3("music_essentials/outro.mp3")
    clipped_outro = outro_music[-5500:]
    return final_mix + (clipped_outro - 15)

def export_audio(final_mix, paper_id: str):
    logging.info("Exporting the mixed audio to a new file...")
    final_mix.export(f"podcast/{paper_id}/{paper_id}.mp3", format="mp3")

def delete_pdf(paper_id: str):
    pdf_path = f'ask-arxiv/{paper_id}/{paper_id}.pdf'
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
