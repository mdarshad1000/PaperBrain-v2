
from openai import OpenAI
from pydub import AudioSegment
from dotenv import load_dotenv
import os
import json

load_dotenv()

SYSTEM_PROMPT = """
    You are a podcast script writer, highly skilled in generating engaging intellectual questions and answers in an 
    easy-to-understand podcast style.

    Podcasters: 
        The Interviewer's name is Noah Bennett, and the expert name is Ethan Sullivan. Keep in mind that Ethan is not a
        co-author or anyone related to the paper, he is just an Expert.

    Tone: 
        Maintain a conversational yet authoritative tone. Noah and Ethan should engage the audience by discussing the paper's
        content with enthusiasm and expertise. 

    Make sure to have a very catchy introduction and a very cool sounding conclusion (farewell to expert and audience). 
    Provide output in valid json having Keys 1, 2, ... n, where Odd numbers are for interviewer and Even numbers are for expert.
    Generate 15-17 dialouges at maximum.
    
    Additional Notes:
        Use a blend of technical language and layman terms to make the content accessible to a wide audience.
        Keep the discussion engaging and avoid jargon overload.
        Ensure that each section flows naturally into the next, maintaining a coherent narrative throughout the script.
    """

USER_PROMPT = """
    Based on the given context from a research paper, generate an entire podcast script having 4-5 questions. 
    Keep the podcast engaging, ask follow up questions. You may use analogies sometimes to explain the concepts. 
    In the introduction always include the phrase 'Welcome to Paper Brain'.
    In the conclusion always include 'Check out PaperBrain to explore scientific literature like never before!'
    You are also provided the metadata of the Paper i.e TITLE, AUTHORS, ABSTRACT. Make use of these information
    in the introduction.
    
    \n\n
    CONTEXT:
    \n
    """

clientOAI = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def generate_script(key_findings: str):

    key_findings_str = ''.join(key_findings)
    completion = clientOAI.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type":"json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT + key_findings_str}
        ]
    )

    response = completion.choices[0].message.content
    response = response.strip()
    response_dict = json.loads(response)

    return response_dict


def generate_audio_whisper(response_dict: dict, paper_id: str):
    final_audio = AudioSegment.empty()
    intermediate_files = []

    # Load intro music and append to the beginning of the final audio
    intro_music = AudioSegment.from_mp3("music_essentials/intro.mp3")
    final_audio += intro_music

    for key in sorted(response_dict.keys(), key=int):  # Ensure keys are sorted numerically
        if int(key) % 2 == 0:
            voice = "onyx"
        else:
            voice = "echo"

        tts_response = clientOAI.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=response_dict[key]
        )
        # Generate a unique filename for each segment
        filename = f"podcast/{key}.mp3"
        tts_response.stream_to_file(filename)
        intermediate_files.append(filename)

        # Append this audio segment to the final audio
        segment = AudioSegment.from_mp3(filename)
        final_audio += segment

    # Load the background music
    bg_music = AudioSegment.from_mp3("music_essentials/bg_music.mp3")
    # Reduce the volume of the background music
    bg_music = bg_music - 30  # Adjust volume reduction as needed


    # Overlay the background music onto the final audio
    final_mix = final_audio.overlay(bg_music, loop=True)

    # Add outro
    outro_music = AudioSegment.from_mp3("music_essentials/outro.mp3")
    clipped_outro = outro_music[-5500:]
    final_mix += clipped_outro - 15 # lower the volume of outro
    
    # Export the mixed audio to a new file
    final_mix.export(f"podcast/{paper_id}.mp3", format="mp3")

    # Delete intermediate files
    for file in intermediate_files:
        os.remove(file)

    return "DONE"



x = {"2": """متی نصیحت - تحریر نمبر Deja que te cuente una historia sobre un pollito. Su nombre es Pollito Tito. Él vive en un gallinero pequeño y normal en un barrio pequeño y normal.

Pollito Tito no es alto ni bajo. No es gordo ni flaco. No es inteligente ni tonto. Es un pollito completamente normal.


"""
}

# generate_audio_whisper(x, 'urdu_story')