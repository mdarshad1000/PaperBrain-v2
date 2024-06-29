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
    client = OpenAIUtils.get_openai_client()
    overlapping_segments = {}  # Move this line outside the for loop

    for key, text in response_dict.items():
        if "sync" in key.lower():
            # Handle chorus part
            speaker, dialogue_number = key.split("sync")
            if dialogue_number not in overlapping_segments.keys():
                overlapping_segments[dialogue_number] = [(speaker, text)]
            else:
                overlapping_segments[dialogue_number].append((speaker, text))
        else:
            # Handle normal part
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

    # Generate chorus audio after collecting all speakers and their texts
    for dialogue_number, speakers_texts in overlapping_segments.items():
        chorus_segments = []
        for speaker, text in speakers_texts:
            voice = get_voice(speaker)
            logging.info(
                f"Generating speech for {speaker} with voice {voice}..."
            )
            audio_response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,  # Use the correct text for each speaker
            )
            binary_content = audio_response.read()
            in_memory_bytes_file = BytesIO(binary_content)
            dialogue_segment = AudioSegment.from_file(in_memory_bytes_file)
            chorus_segments.append(dialogue_segment)

        # Overlay the audio segments to create the chorus effect
        chorus_segment = overlay_audio_segments(chorus_segments)
        yield chorus_segment


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
    )  # reduce volume by 6 dB
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
    "EMMA1": "Welcome to Paper Brain, your go-to space for delving into the maze of scientific literature. I'm your host, Emma Anderson, and today, we're diving into the expansive realm of informational alchemy - transforming raw text into structured know-how using the latest wizardry in AI. We're looking at a paper titled 'Large Language Models for Generative Information Extraction: A Survey' by an ensemble of researchers led by Derong Xu and colleagues. In a realm where knowledge extraction is key, they've surveyed the cutting-edge advancements in this field.",
    "ETHAN1": "Thanks for having me, Emma. It's thrilling to see how Large Language Models, or LLMs, have been revolutionizing the way we approach information extraction. This study is a treasure trove, exploring everything from named entity recognition to the most nuanced aspects of event extraction.",
    "EMMA2": "And speaking of thrilling, we've got a specialist joining us to add layers to our conversation—Stuart Montgomery, a veteran in the domain of artificial intelligence.",
    "STUART1": "Pleasure to be here, Emma. There's just so much to unpack with these LLMs. The road from discriminative to generative models alone is a paradigm shift not many saw coming.",
    "EMMA3": "Absolutely, Stuart. Let's start with that, shall we? Ethan, can you break down the basics of generative versus traditional information extraction for us?",
    "ETHAN2": "Sure, Emma. Traditional information extraction is all about labels and categories—like organizing your closet by color and season. But with generative IE, it's like you're weaving new clothes from the same fabric to create whatever piece you need, anytime.",
    "EMMA4": "That's quite an image, Ethan! And how do these LLMs come into play here?",
    "ETHAN3": "Well, LLMs are the looms in this analogy. They're not just spotting patterns; they're building narratives. They take in the text and spit out structured data, crafting context and understanding on the fly.",
    "EMMA5": "Hmm, could we tap into a specific example, maybe named entity recognition?",
    "ETHAN4": "Named entity recognition is the groundwork of info extraction. Think of it as meeting new people and remembering their names and titles. With LLMs, we've seen a leap forward. Techniques like GPT-NER have transformed NER from a simple introduction to a concerto of entity interactions.",
    "EMMAAsync1": "And I'm cer—",
    "ETHANsync1": "Exactly, that's—",
    "EMMA6": "Oh, sorry Ethan, you go.",
    "ETHAN5": "No problem at all. I was going to say, this approach, coupled with self-improvement frameworks, adds a dynamic layer, allowing models to learn and adapt incredibly well, especially in zero-shot scenarios.",
    "STUART2": "Oh, and do not forget relation extraction! LLMs are like those diligent researchers who don't just spot relationships, but they also categorize them. The QA4RE model, for instance, turns this into a multiple-choice test that LLMs are surprisingly good at.",
    "EMMA7": "So, this is more complex than finding pairs. It's orchestrating an entire dance of interactions... and hold on, Stuart, are you suggesting that this is a test LLMs are eager to take?",
    "STUART3": "Absolutely, Emma! And they're acing it by incorporating reasoning and representations right into the text. It's fascinating stuff!",
    "ETHAN6": "Let me add—you mentioned reasoning, Stuart. That's a golden nugget in event extraction. Models like Code4Struct and PGAD have leveraged coding paradigms to make sense of these complex scenarios.",
    "EMMA8": "Wait, coding paradigms? Ethan, are we moving into the territory of universal information extraction?",
    "ETHAN7": "Sharp catch, Emma! That's where the real magic happens. We're talking about models that are jacks-of-all-trades, navigating through a variety of tasks with the finesse of a librarian who knows every book in the library.",
    "EMMA9": "A universal librarian—that's a resource worth having. How does this universal approach differ, say, when using natural language vs. code?",
    "STUART4": "It's like the difference between a generalist and a specialist. Natural Language-based LLMs are dab hands at understanding and generating text, while Code-based LLMs are meticulously precise with the structure.",
    "EMMA10": "Oh, the age-old breadth versus depth debate... But when it comes to adapting LLMs to generative IE, there's a toolbox of strategies, like data augmentation, right Ethan?",
    "ETHAN8": "Exactly, from conjuring up labeled data to inverse generation, LLMs can enrich the training process immensely. It's like a master chef experimenting with ingredients to perfect a recipe.",
    "EMMA11": "I'm sensing you're a foodie, Ethan! But these strategies don't stop at data augmentation, do they? We also have to look at the prompts we're using for these LLMs. Can you share some insight into that?",
    "ETHAN9": "Gladly, Emma. A lot hinges on how you communicate with your model. Are we playing Jeopardy? Are we reasoning step-by-step? These prompt designs can mean the difference between a passable performance and a standing ovation.",
    "STUART5": "Indeed, and that's not just in theory. Take the zero-shot learning approaches like cross-domain generalization. It's about teaching these models to think on their feet—or circuits—in completely new situations.",
    "EMMA12": "Right, expecting them to pull a MacGyver and escape any tight spot with nothing but a paper clip and a rubber band. Good one, Stuart. With all these innovations, what are the key applications we're seeing in specific domains?",
    "ETHAN10": "Each domain is like a new playing field, Emma. For instance, medical researchers are tapping into LLMs for parsing clinical notes. Legal experts are using them to dissect heavy jargon-filled documents—LLMs are becoming indispensable across the board.",
    "EMMA13": "And with different plays come different players. However, with advanced techniques does come the issue of reliably evaluating these LLMs, right? What are the benchmarks or challenges we're facing?",
    "ETHAN11": "Oh, performance analysis has its own share of hurdles. For instance, in open IE settings, LLMs can struggle without a clear set of labels. And the quality of our algorithm's output? That's still often at the mercy of the quality of input data—garbage in, garbage out.",
    "EMMA14": "Such a classic problem, yet so persistent. Now, if we peek into the crystal ball, what does the future hold for LLMs in generative IE?",
    "ETHAN12": "The march forward is all about flexibility—universal models that can adjust their lenses for any scale of the picture. Future attempts will likely also hone in-context learning strategies and even prompt designs.",
    "EMMA15": "So it's a blend of adaptability and creativity. Before we wrap up, could each of you give a quick takeaway for our listeners diving into this riveting paper?",
    "STUART6": "Certainly, Emma. My key takeaway is: Watch the space of LLMs closely. They're not just models; they're evolving ecosystems in information extraction.",
    "ETHAN13": "And mine is simple: Embrace the complexity. As intimidating as these LLMs may seem, their potential to simplify our interaction with vast amounts of text is just beginning to be tapped.",
    "EMMA16": "Thank you, Ethan, and a big thanks to Stuart, as well. It's been an enlightening conversation. To our listeners, check out PaperBrain to explore scientific literature like never before! Until next time, keep mining for knowledge!",
}
