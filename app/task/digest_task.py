from app.service.celery_service import celery_app
from app.service.aws_service import DynamoDB
from app.engine.digest_utils import fetch_papers, generate_relevance_score

from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

dynamo_db = DynamoDB()

@celery_app.task(queue="digestq")
def create_daily_digest(categories: List[str], interests: str, user_id: str, date: str):
    print(f"Starting daily digest creation for user: {user_id} on date: {date}")

    # Scrape papers from arXiv
    papers = fetch_papers(categories, date)
    papers_list = list(papers)
    if not papers_list:
        print(f"No papers found for categories: {categories} on date: {date}")
        return []

    print(f"Found {len(papers_list)} papers for categories: {categories} on date: {date}")

    papers_w_score = []

    for i in range(0, len(papers_list), 10):
        papers_batch = papers_list[i : i + 10]
        str_papers_batch = ""
        for idx, paper in enumerate(papers_batch, start=1):
            str_papers_batch += f"{idx}. {paper}\n\n"

        print(f"Generating relevance scores for batch starting with paper index: {i}")
        response = generate_relevance_score(interests, str_papers_batch)
        try:
            # for OpenAI
            for paper in response.papers:
                papers_w_score.append(paper)
        except AttributeError:
            # for Gemini
            for paper in response['papers']:
                papers_w_score.append(paper)

    relevant_papers = [paper for paper in papers_w_score if paper.relevancy_score >= 7]
    sorted_relevant_papers = sorted(relevant_papers, key=lambda x: x.relevancy_score, reverse=True)

    print(f"Total relevant papers found: {len(sorted_relevant_papers)}")

    # Converting the list of Paper objects to a list
    result = [
        {
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract,
            "relevancy_score": paper.relevancy_score,
            "reasons_for_relevancy": paper.reasons_for_relevancy,
        }
        for paper in sorted_relevant_papers
    ]

    print(f"Adding digest for user: {user_id} on date: {date} to DynamoDB")
    dynamo_db.add_digest(user_id, date, result)

    return result