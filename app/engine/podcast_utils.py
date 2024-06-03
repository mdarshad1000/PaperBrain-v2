import os
import time
import logging
import json

import google.generativeai as genai
from app.service.openai_service import OpenAIUtils

from config import (
    GEMINI_SYSTEM_INSTRUCTION,
    GEMINI_USER_INSTRUCTION,
    GPT_SYSTEM_PROMPT, 
    GPT_USER_PROMPT
)

def generate_key_insights(research_paper_text: str):
    genai.configure(api_key=os.getenv('GEMINI_API_KEY_2'))
    logging.info('Generating key insights using GEMINI')
    # Set up the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 8192,
    }
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]

    system_instruction = GEMINI_SYSTEM_INSTRUCTION

    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                  generation_config=generation_config,
                                  system_instruction=system_instruction,
                                  safety_settings=safety_settings)

    convo = model.start_chat(history=[
    ])

    retry_count = 0
    while retry_count < 3:
        try:
            logging.info('Attempt %d to send message', retry_count + 1)
            convo.send_message(
                GEMINI_USER_INSTRUCTION.format(
                research_paper_text=research_paper_text))
            logging.info('Finished generating key insights')
            return convo.last.text
        except Exception as e:
            logging.error("Error while sending message: %s", e)
            time.sleep(3)
        retry_count += 1


def generate_podcast_script(title, abstract, authors, key_findings):

    client = OpenAIUtils.get_openai_client()

    # Format the input text
    user_prompt = "\n".join([
        GPT_USER_PROMPT,
        f"Title: {title}",
        f"Abstract: {abstract}",
        f"Authors: {authors}",
        f"Key Findings: {key_findings}"
    ])

    try:
        logging.info("Sending request to OpenAI...")
        completion = client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": GPT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
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
