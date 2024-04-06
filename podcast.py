
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

load_dotenv()

db_actions = Action(
    host=os.getenv('HOST'),
    dbname=os.getenv('DATABASE'),
    user=os.getenv('USERNAME'),
    password=os.getenv('PASSWORD'),
    port=os.getenv('PORT')
)
r = Redis()
q = Queue(connection=r)

logging.basicConfig(level=logging.INFO)

# SYSTEM_PROMPT = """
#     You are a podcast script writer, highly skilled in generating engaging intellectual questions and answers in an 
#     easy-to-understand podcast style.

#     Podcasters: 
#         The Interviewer's name is Noah Bennett, and the expert name is Ethan Sullivan. Keep in mind that Ethan is not a
#         co-author or anyone related to the paper, he is just an Expert.

#     Tone: 
#         Maintain a conversational yet authoritative tone. Noah and Ethan should engage the audience by discussing the paper's
#         content with enthusiasm and expertise. 

#     Make sure to have a very catchy introduction and a very cool sounding conclusion (farewell to expert and audience). 
#     Provide output in valid json having Keys 1, 2, ... n, where Odd numbers are for interviewer and Even numbers are for expert.
#     Generate 15-17 dialouges at maximum.
    
#     Additional Notes:
#         Use a blend of technical language and layman terms to make the content accessible to a wide audience.
#         Keep the discussion engaging and avoid jargon overload.
#         Ensure that each section flows naturally into the next, maintaining a coherent narrative throughout the script.
# """
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

clientOAI = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


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

    # try:
    #     with open('all_files.json', 'w') as f:
    #         json.dump(response_dict, f)
    # except IOError as e:
    #     logging.error("Failed to write to file: %s", e)
    #     sys.exit(1)

    return response_dict


def load_intro_music():
    logging.info("Loading intro music...")
    return AudioSegment.from_mp3("music_essentials/intro.mp3")

def create_directory(paper_id: str):
    directory_name = f"podcast/{paper_id}"
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
    return directory_name

def generate_speech(key: str, text: str):
    voice = "nova" if "EMMA" in key else "onyx" if "ETHAN" in key else "echo"
    logging.info(f"Generating speech for {key} with voice {voice}...")
    return clientOAI.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

def save_speech_to_file(tts_response, filename: str):
    logging.info(f"Saving speech to {filename}...")
    tts_response.stream_to_file(filename)

def append_audio_segment(filename: str, final_audio):
    logging.info("Appending this audio segment to the final audio...")
    segment = AudioSegment.from_mp3(filename)
    return final_audio + segment

def load_and_adjust_bg_music():
    logging.info("Loading and adjusting background music...")
    bg_music = AudioSegment.from_mp3("music_essentials/bg_music.mp3")
    return bg_music - 30

def overlay_bg_music(final_audio, bg_music):
    logging.info("Overlaying background music onto the final audio...")
    return final_audio.overlay(bg_music, loop=True)

def add_outro(final_mix):
    logging.info("Adding outro...")
    outro_music = AudioSegment.from_mp3("music_essentials/outro.mp3")
    clipped_outro = outro_music[-5500:]
    return final_mix + (clipped_outro - 15)

def export_audio(final_mix, paper_id: str):
    logging.info("Exporting the mixed audio to a new file...")
    final_mix.export(f"podcast/{paper_id}/{paper_id}.mp3", format="mp3")

def delete_intermediate_files(intermediate_files: list):
    logging.info("Deleting intermediate files...")
    for file in intermediate_files:
        os.remove(file)

def delete_pdf(paper_id: str):
    pdf_path = f'ask-arxiv/{paper_id}.pdf'
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

def generate_audio_whisper(response_dict: dict, paper_id: str):
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

    logging.info("Audio generation completed.")
    return "DONE"