import re
import os
import json
import requests
import google.generativeai as genai

from bs4 import BeautifulSoup
from typing import List, Generator, Dict
from pydantic import BaseModel

from config import DIGEST_SYSTEM_PROMPT
from app.service.openai_service import OpenAIUtils
from app.service.redis_service import redis_client

# Extract categories using regex
def extract_categories(text: str) -> List[str]:
    pattern = r"\(([^)]+)\)"
    matches = re.findall(pattern, text)
    return [match for match in matches if re.match(r"^[a-zA-Z.-]+$", match)]


# Fetch papers from arXiv for given categories
def fetch_papers(categories: List[str], date: str) -> Generator[Dict[str, str], None, None]:
    for category in categories:

        redis_key = f"{date}-{category}"

        # Check if the papers are already scraped and cached
        cached_data = redis_client.get(redis_key)
        if cached_data:
            # Load cached data
            papers = json.loads(cached_data)
            for paper in papers:
                yield paper
            continue

        # If not cached, scrape from arXiv
        base_url = f"https://arxiv.org/list/{category}/new"
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, "html.parser")
        dl = soup.find("dl")
        if dl is None:
            continue

        scraped_papers = []
        for p_id, p_info in zip(dl.find_all("dt"), dl.find_all("dd")):
            paper_id = p_id.find_all("a")[1].get("href").split("/")[-1]
            title = (
                p_info.find("div", {"class": "list-title mathjax"})
                .text.lstrip("Title:")
                .strip()
            )
            abstract = p_info.find("p", {"class": "mathjax"}).text.strip()
            authors = p_info.find("div", {"class": "list-authors"}).text
            categories_text = p_info.find("div", {"class": "list-subjects"}).text
            categories = extract_categories(categories_text)

            paper_data = {
                "id": paper_id,
                "title": title,
                "authors": authors,
                "abstract": abstract,
                # "categories": categories, # You can uncomment if you need categories
            }
            scraped_papers.append(paper_data)
            yield paper_data

        # Store scraped data in Redis with 24-hour expiration
        redis_client.set(redis_key, json.dumps(scraped_papers), ex=86400)

# Define paper model for responses
class Paper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    relevancy_score: int
    reasons_for_relevancy: str


# Response model to handle relevant papers
class RelevantPapersResponse(BaseModel):
    papers: List[Paper]


# Function to generate relevance score for a list of papers
def generate_relevance_score(interests: str, papers: str):
    sync_agentic_client = OpenAIUtils.get_agentic_client_sync()
    completion = sync_agentic_client.beta.chat.completions.parse(
        model="agentic-turbo",
        messages=[
            {
                "role": "system",
                "content": DIGEST_SYSTEM_PROMPT + "\n" + interests,
            },
            {"role": "user", "content": papers},
        ],
        response_format=RelevantPapersResponse,
    )
    return completion.choices[0].message.parsed



def generate_relevance_score_gemini(interests: str, papers: str):
    # IMPROVE: Fails to generate accurate response (relevancy_score) compared to OpenAI
    json_schema = RelevantPapersResponse.schema_json(indent=2)
    genai.configure(api_key=os.getenv("GEMINI_API_KEY_2"))
    model = genai.GenerativeModel(
        "gemini-1.5-pro-002",
        system_instruction=f"""
            RelevantPapersResponse = {json_schema}
            Return a `RelevantPapersResponse`
            {DIGEST_SYSTEM_PROMPT}
        """ + '\n' + interests,
        generation_config={
            "response_mime_type": "application/json",
        },
    )
    response = model.generate_content(papers) 
    response_str = response.text

    json_response = json.loads(response_str)
    # final_response = json_response.get('papers')
    # with open('app/engine/tesjt.json', 'w') as f:
    #     json.dump(final_response, f)
    return json_response