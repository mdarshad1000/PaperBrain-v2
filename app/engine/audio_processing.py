import logging
from io import BytesIO
from pydub import AudioSegment

from config import PODCAST_STORAGE_PATH, MUSIC_ESSENTIALS
from app.service.openai_service import OpenAIUtils


def get_voice(speaker):
    if speaker.startswith("EM"):
        return "nova"
    elif speaker.startswith("ET"):
        return "onyx"
    elif speaker.startswith("NO"):
        return "echo"
    elif speaker.startswith("OL"):
        return "shimmer"
    elif speaker.startswith("AL"):
        return "alloy"
    elif speaker.startswith("ST"):
        return "fable"
    else:
        return None


def overlay_audio_segments(segments):
    segments.sort(key=len, reverse=True)
    base_segment = segments[0]
    for segment in segments[1:]:
        base_segment = base_segment.overlay(segment)
    return base_segment


def generate_speech(response_dict):
    client = OpenAIUtils.get_async_openai_client()

    for key, text in response_dict.items():
        voice = get_voice(key)
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


def overlay_bg_music_on_final_audio(final_audio, style: str = None):
    logging.info("Loading and adjusting background music...")
    if style == "funny":
        bg_music = AudioSegment.from_mp3(MUSIC_ESSENTIALS + "bg-music-new-2.mp3")
    else:
        bg_music = AudioSegment.from_mp3(MUSIC_ESSENTIALS + "bg-music-new-2.mp3")

    # Calculate how many times the bg_music needs to be repeated
    repeat_times = len(final_audio) // len(bg_music) + 1
    bg_music = bg_music * repeat_times

    logging.info("Overlaying background music onto the final audio...")
    bg_music = bg_music[: len(final_audio)]
    bg_music = (
        bg_music - 9 if style == "funny" else bg_music - 9
    )  # reduce volume by 9 dB
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


x = {
    "EMMA1": "Welcome to Paper Brain, where we delve into cutting-edge research papers and unravel their complexities. I'm your host, Emma Anderson, and today we're discussing a survey that's making waves in the world of computational linguistics. Joining me is Ethan Sullivan, an experienced connoisseur in the field. Ethan, it's great to have you here!",
    "ETHAN1": "Thank you, Emma. It's a pleasure to be here to discuss this fascinating survey on Large Language Models for Generative Information Extraction.",
    "EMMA2": "Absolutely! Now, let's give our listeners an overview. The paper we're talking about is titled 'Large Language Models for Generative Information Extraction: A Survey' by Derong Xu and team. In a nutshell, this survey looks at the role of LLMs in extracting structured knowledge, like entities, relations, and events, from plain texts. Ethan, could you unpack what exactly Generative Information Extraction means?",
    "ETHAN2": "Gladly, Emma. Generative Information Extraction is an approach where we use large language models to generate structured information from text. Unlike traditional methods that classify or label parts of the text, LLMs can directly output structured formats. This capability aligns closely with how humans interpret and communicate information.",
    "EMMA3": "Hmm, that definitely sounds like a game-changer. And what about the key subtasks in this area, like Named Entity Recognition and Relation Extraction?",
    "ETHAN3": "Oh, those are the bread and butter of IE. Named Entity Recognition, or NER, is about identifying entities such as names of people or organizations. Relation Extraction, on the other hand, deals with how these entities interact or relate to each other. Think of it like piecing together a social network from a text.",
    "EMMA4": "Got it, like who's tagging who in a post, metaphorically speaking. Now, I've heard these LLMs face quite the challenge with these subtasks, right?",
    "ETHAN4": "Indeed they do. For one, bridging the gap between traditional NER and what LLMs can do is a big hurdle. But new approaches, like GPT-NER, are transforming these tasks by employing strategies to self-verify and correct as they go. It's pretty nifty how these models can now self-improve!",
    "STUART1": "And if I may jump in here, Emma, I'm Stuart Montgomery, and I work closely with these models. LLMs really shine when they're fine-tuned with examples. It's as if you're honing a chef's skills to specialize in a certain cuisine, and that's when you get the best results.",
    "EMMA5": "Welcome, Stuart, and wow, that's an interesting perspective! So LLMs are like master chefs in the kitchen of language!",
    "ETHAN5": "Indeed, and speaking of specializations, let's talk about Relation Extraction with LLMs.",
    "EMMA6": "Sure, lead the way!",
    "ETHAN6": "LLMs were initially not so great at extracting relationships because their training didn’t involve much of this task. But now, methods like QA4RE and GPT-RE are framing these tasks in ways that play to the models' strengths. It's like asking someone to do a job in a way that suits them best.",
    "STUART2": "Exactly, and that's not all. With Event Extraction, for example, methods like Code4Struct and PGAD are pushing boundaries by generating context-aware prompts. It's truly innovative how they utilize programming language features to represent complex event structures.",
    "EMMA7": "Oh, that reminds me of building something intricate with code. You're using the model’s language generation to create a blueprint of the events, right?",
    "ETHAN7": "Precisely. And beyond these task-specific models, we're now looking at Universal Information Extraction, which combines all of these tasks in a more interconnected way.",
    "EMMA8": "Seems like integration is key here. Oh, but hold on—",
    "ETHANCHORUS1": "Ethan, do these techniques work well only with text?",
    "EMMACHORUS1": "Sorry, Ethan, are these techniques strictly for text?",
    "ETHAN8": "No worries, Emma. To answer that, no, they're not limited to just text. For instance, there's exciting work being done in Multimodal IE, where models are handling both text and visual info, as well as in multilingual setups!",
    "EMMA9": "Oh-huh, I see. Now, with the good comes the challenging. Evaluating these models must be quite the task.",
    "STUART3": "You're right, Emma. Evaluation isn’t straightforward. We have to consider how well the model can reason or if it's robust to different kinds of inputs. There're a lot of angles to consider.",
    "ETHAN9": "And if I may add to Stuart's point, there are common errors like 'unannotated spans' to watch out for. That’s when a model misses extracting a piece of information. It’s essential to identify and fix these gaps.",
    "EMMA10": "So it's like proofreading but for AI. Now, to cap it off, Ethan, what's on the horizon for Generative Information Extraction?",
    "ETHAN10": "The future is ripe with potential. We're talking about developing models that are even more robust and adaptable, better prompt designs, and tackling Open IE challenges. There's more work to be done, but the prospects are incredibly exciting!",
    "EMMA11": "Absolutely thrilling! Listeners, remember to check out PaperBrain to explore scientific literature like never before! Ethan, Stuart, thank you both for sharing your insights on this promising field!",
    "ETHAN11": "Thank you, Emma. It's been a pleasure!",
    "STUART4": "It was great being part of this discussion. Thanks for having me!",
}
