import requests
from bs4 import BeautifulSoup
import os
import json
from dotenv import load_dotenv
import logging
from concurrent.futures import ThreadPoolExecutor
import jsonschema

from openai import OpenAI


load_dotenv()

client = OpenAI()


logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

SYSTEM_INSTRUCTION = """
TASK:
    You are an expert research assistant who is skilled in recommending research papers based on USER's resarch interest.
    You will be provided with a JSON of Research Papers as well as USER's INTERESTS. Go through each research paper and
    compare if it is relvant to USER's research interest.
    Give a relevancy score on a scale of 1-10 based on how relevant the paper is for the USER.
    Give a 1-2 line short description as to why the paper is Relevant for the user. If the paper is not relevant then write NOT RELEVANT.

INPUT FORMAT:
[
    {
        "id": paper_id 1
        "title": Title of the Paper 1,
        "authors": Authors of the Paper 1,
        "subjects": Subjects/Categories 1,
        "abstract": Abstract of the Paper 1,
    },
    {
        "id": paper_id 2
        "title": Title of the Paper 2,
        "authors": Authors of the Paper 2,
        "subjects": Subjects/Categories 2,
        "abstract": Abstract of the Paper 2,
    },
    
    ...

    {
        "id": paper_id n
        "title": Title of the Paper n,
        "authors": Authors of the Paper n,
        "subjects": Subjects/Categories n,
        "abstract": Abstract of the Paper n, 
    }
]


OUTPUT FORMAT:
    {
        "id": paper_id 1
        "title": Title of the Paper 1,
        "authors": Authors of the Paper 1,
        "abstract": Abstract of the Paper 1,
        "relevancy_score": "an integer score out of 10",
        "reason_for_match": "1-2 sentence short reasonings" about how it matches with USER's interest.
    }
"""

import csv

def fetch_papers(categories: list):
    logging.info('Fetching papers started')
    papers_data = []

    for category in categories:
        if os.path.exists(f'daily_papers/{category}.csv'):
            continue
             
        else:
            # Define the URL for each category
            url = f"https://arxiv.org/list/{category}/new"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            h2 = soup.find_all("h2")
            for item in h2:
                papers = item.find_next_sibling("dl")

                for p_id, p_info in zip(papers.find_all("dt"), papers.find_all("dd")):
                    paper_id = p_id.find("span", {"class": "list-identifier"}).text.strip().split(":")[1].split()[0]
                    title = p_info.find("div", {"class": "list-title mathjax"}).text.strip().replace("Title: ", "")
                    authors = p_info.find("div", {"class": "list-authors"}).text.strip().replace("Authors:", "")
                    subjects = p_info.find("div", {"class": "list-subjects"}).text.strip().replace("Subjects: ", "")
                    abstract = p_info.find("p", {"class": "mathjax"}).text.strip()
                    paper_data = [paper_id, title, authors, subjects, abstract]
                    papers_data.append(paper_data)
            
            # Write the papers_data to a new CSV file
            with open(f'daily_papers/{category}.csv', 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["id", "title", "authors", "subjects", "abstract"])  # Write the header
                writer.writerows(papers_data)  # Write the data
    logging.info('Fetching papers completed')


PAPER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "authors": {"type": "string"},
        "abstract": {"type": "string"},
    },
    "required": ["id", "title", "authors", "abstract"],
}

def validate_paper(paper):
    try:
        jsonschema.validate(instance=paper, schema=PAPER_SCHEMA)
        return True
    except jsonschema.exceptions.ValidationError:
        return False

def process_paper(paper, interests, client):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            response_format={"type":"json_object"},

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_INSTRUCTION
                },
                {   
                    "role": "user",
                    "content":"""
                            You have been asked to read a paper with title, authors and abstract.
                            Based on my specific research interests, relevancy score out of 10 for the paper, based on my specific research interest, with a higher score indicating greater relevance. A relevance score more than 7 will need person's attention for details.
                            Additionally, please generate 1-2 sentence summary for the paper explaining why it's relevant to my research interests.
                            Once you have all the information, return the paper.

                            INTERESTS:
                            {interests}                        
                                
                            GIVEN PAPER:
                            {paper}""".format(interests=interests, paper=json.dumps(paper))
                },  
            ],
        )

        output = completion.choices[0].message.content
        scored_paper = json.loads(output)
        return scored_paper
    except Exception as e:
        logging.error(f"Failed to process paper {paper['id']}: {e}")
        return None

def rank_papers(categories, interests, client):
    logging.info('Recommendation process started')
    all_papers = []

    for category in categories:
        with open(f'daily_papers/{category}.json', 'r') as f:
            papers = json.load(f)
            all_papers.extend(papers)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_paper, paper, interests, client) for paper in all_papers if validate_paper(paper)]

    with open('scored_papers.jsonl', 'w') as jsonl_file:
        for future in futures:
            scored_paper = future.result()
            if scored_paper is not None:
                jsonl_file.write(json.dumps(scored_paper) + '\n')

    logging.info('Recommendation process done')


import json

def filter_paper():
    recommendation = []
    score_counts = {str(i): 0 for i in range(1, 11)}  # Initialize score counts
    x = 0
    with open('scored_papers.jsonl', 'r') as scored_papers:
        for item in scored_papers:
            paper = json.loads(item)
            score = str(paper['relevancy_score'])
            if score in score_counts:
                score_counts[score] += 1 # Increment the count for the score
            if int(score) == 8:
                paper['authors'] = paper['authors'].replace('\n', ',')
                paper['abstract'] = paper['abstract'].replace('\n', ' ')
                recommendation.append(paper)
                x += 1
            if x == 5:
                break
    # print(score_counts)  # Print the counts of each score
    return recommendation

# function calling
categories = ['cs.ai', 'cs.cl', 'cs.lg']
interests = """
    Large language model pretraining and finetunings.
    Multimodal machine learning.
    Do not care about specific application, for example, information extraction, summarization, etc.
    Not interested in paper focus on specific languages, e.g., Arabic, Chinese, etc.
"""
# fetch_papers(categories=categories)
# rank_papers(categories=categories, interests=interests, client=client)
recommendations = filter_paper()
print(json.dumps(recommendations, indent=4))

import tiktoken
def estimate_embedding_price(price_per_1m):
    enc = tiktoken.get_encoding("gpt2")
    num_tokens = 0
    all_papers = []

    for category in categories:
        with open(f'daily_papers/{category}.json', 'r') as f:
            papers = json.load(f)
            all_papers.extend(papers)
    print(len(all_papers))
    for paper in all_papers:
        paper_string = json.dumps(paper)  # Convert the paper dictionary to a string
        num_tokens += len(enc.encode(paper_string))  # Encode the string
    print(num_tokens)
    price = num_tokens / 1000000 * price_per_1m
    return num_tokens, f'USD {price}'
fetch_papers(categories=categories)
input_token = print(estimate_embedding_price(price_per_1m=0.50))
ouput_token = print(estimate_embedding_price(price_per_1m=1.50))
# # print("FINAL PRICE: ", input_token+ouput_token)