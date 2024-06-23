import os
import time
import json
import fitz
import logging
import requests

from PIL import Image
from io import BytesIO

import google.generativeai as genai

from app.service.openai_service import OpenAIUtils

from config import (
    GEMINI_SYSTEM_INSTRUCTION,
    GEMINI_USER_INSTRUCTION,
    GPT_SYSTEM_PROMPT_MULTISPEAKER,
    GPT_USER_PROMPT_MULTISPEAKER,
    TECHNICAL_STYLE_SYSTEM,
    TECHNICAL_STYLE_USER,
    MODERATE_STYLE_SYSTEM,
    MODERATE_STYLE_USER,
    EASY_STYLE_SYSTEM,
    EASY_STYLE_USER,
    FUNNY_STYLE_SYSTEM,
    FUNNY_STYLE_USER,
)


def get_podcast_thumbnail(paperurl: str, style: str):

    BADGE_PATH = "static/badges/" + style + ".png"
    resp = requests.get(paperurl, stream=True)
    pdf_bytes = resp.content  # Get the bytes of the PDF directly

    pdf_document = fitz.open(None, pdf_bytes)  # Open the PDF from bytes
    first_page = pdf_document[0]
    pix = first_page.get_pixmap()
    
    # Close the PDF document
    pdf_document.close()
    # Open the main image
    main_image = Image.open(BytesIO(pix.tobytes("png")))  # Convert the pixmap to PNG bytes

    # Get the badge image
    badge_image = Image.open(BADGE_PATH)
    badge_image = badge_image.resize((badge_image.width // 6, badge_image.height // 6))

    badge_position = (main_image.width - badge_image.width - 1, 7)
    # Paste the badge image onto the main image at the top left corner (0, 0)
    main_image.paste(badge_image, badge_position)

    # Convert the modified image back to bytes
    img_byte_arr = BytesIO()
    main_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr


def generate_key_insights(research_paper_text: str):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY_2"))
    logging.info("Generating key insights using GEMINI")
    # Set up the model
    generation_config = {
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 0,
        # "max_output_tokens": 8192,
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    ]

    system_instruction = GEMINI_SYSTEM_INSTRUCTION

    models = ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]

    for model_name in models:
        retry_count = 0
        while retry_count <= 2:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,
                    system_instruction=system_instruction,
                    safety_settings=safety_settings,
                )
                convo = model.start_chat(history=[])
                convo.send_message(
                    GEMINI_USER_INSTRUCTION.format(
                        research_paper_text=research_paper_text
                    )
                )
                logging.info("Finished generating key insights")
                key_insight = convo.last.text
                print("KEY INSIGHTS: ", key_insight)
                return key_insight
            except Exception as e:
                logging.error("Error while sending message: %s", e)
                wait_time = (
                    40 if model_name == "gemini-1.5-flash" else 3
                )  # Increase wait time for flash model
                time.sleep(wait_time)
                retry_count += 1

    logging.error("Failed to generate key insights with all models")
    return None


def generate_podcast_script(
    title,
    abstract,
    authors,
    key_findings,
    style,
    speaker_one,
    speaker_two,
    speaker_three,
):
    s_one_first_name = speaker_one.split(" ")[0]
    s_two_first_name = speaker_two.split(" ")[0]
    s_three_first_name = speaker_three.split(" ")[0]

    if style == "expert":
        system_style = TECHNICAL_STYLE_SYSTEM
        user_style = TECHNICAL_STYLE_USER
    elif style == "moderate":
        system_style = MODERATE_STYLE_SYSTEM
        user_style = MODERATE_STYLE_USER
    elif style == "easy":
        system_style = EASY_STYLE_SYSTEM
        user_style = EASY_STYLE_USER
    elif style == "funny":
        system_style = FUNNY_STYLE_SYSTEM
        user_style = FUNNY_STYLE_USER
    else:
        raise ValueError("Invalid style provided")

    client = OpenAIUtils.get_openai_client()

    # Format the input text
    user_prompt = "\n".join(
        [
            GPT_USER_PROMPT_MULTISPEAKER(
                user_style=user_style,
                s_one_first_name=s_one_first_name,
                s_two_first_name=s_two_first_name,
                s_three_first_name=s_three_first_name,
            ),
            f"Title: {title}",
            f"Abstract: {abstract}",
            f"Authors: {authors}",
            f"Key Findings: {key_findings}",
        ]
    )

    try:
        logging.info("Sending request to OpenAI...")
        completion = client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": GPT_SYSTEM_PROMPT_MULTISPEAKER(
                        system_style=system_style,
                        speaker_one=speaker_one,
                        speaker_two=speaker_two,
                        speaker_three=speaker_three,
                        s_one_first_name=s_one_first_name,
                        s_two_first_name=s_two_first_name,
                        s_three_first_name=s_three_first_name,
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as e:
        logging.error("Failed to send request to OpenAI: %s", e)
        raise Exception(f"Failed to send request to OpenAI: {e}")

    try:
        response = completion.choices[0].message.content
        response = response.strip()
        response_dict = json.loads(response)
    except json.JSONDecodeError as e:
        logging.error("Failed to decode JSON response from OpenAI: %s", e)
        raise ValueError("Failed to decode JSON response from OpenAI")

    return response_dict
