import logging
from io import BytesIO
from pydub import AudioSegment

from config import PODCAST_STORAGE_PATH, MUSIC_ESSENTIALS
from app.service.openai_service import OpenAIUtils


def generate_speech(response_dict):
    client = OpenAIUtils.get_openai_client()
    for key, text in response_dict.items():
        voice = "nova" if key.startswith("EM") else "onyx" if key.startswith("ET") else "echo" if key.startswith("NO") else "shimmer" if key.startswith("OL") else "alloy" if key.startswith("AL") else "fable"
        logging.info(f"Generating speech for {key} with voice {voice}...")
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        binary_content = audio_response.read()
        in_memory_bytes_file = BytesIO(binary_content)

        dialogue_segment = AudioSegment.from_file(in_memory_bytes_file)
        yield dialogue_segment


def append_audio_segments(audio_generator):
    audio_segments = []
    for audio_segment in audio_generator:
        logging.info("Appending this audio segment to the final audio...")
        audio_segments.append(audio_segment)
    final_audio = sum(audio_segments)
    return final_audio


def overlay_bg_music_on_final_audio(final_audio, style: str=None):
    logging.info("Loading and adjusting background music...")
    if style == "funny":
        bg_music = AudioSegment.from_mp3(MUSIC_ESSENTIALS + "bg-music-new-2.mp3")
    else:
        bg_music = AudioSegment.from_mp3(MUSIC_ESSENTIALS + "bg-music-new-2.mp3")
    
    # Calculate how many times the bg_music needs to be repeated
    repeat_times = len(final_audio) // len(bg_music) + 1
    bg_music = bg_music * repeat_times

    logging.info("Overlaying background music onto the final audio...")
    bg_music = bg_music[:len(final_audio)]
    bg_music = bg_music - 9 if style == "funny" else bg_music - 9  # reduce volume by 6 dB
    final_audio = final_audio.overlay(bg_music)
    return final_audio


def add_intro_outro(final_mix):
    logging.info("Adding intro...")
    outro = AudioSegment.from_mp3(MUSIC_ESSENTIALS + "outro-soft.mp3")

    intro = AudioSegment.from_mp3(MUSIC_ESSENTIALS + "intro.mp3")
    return intro + final_mix + outro


def export_audio(final_mix, paper_id: str):
    logging.info("Exporting the mixed audio to a new file...")
    final_mix.export(f"{PODCAST_STORAGE_PATH}/{paper_id}/{paper_id}.mp3", format="mp3")
    logging.info("Finished exporting the mixed audio.")
