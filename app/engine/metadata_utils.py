from dotenv import load_dotenv
from paperswithcode.models.dataset import *
from bs4 import BeautifulSoup
import requests

load_dotenv()

def get_paper_info(client, arxiv_id):
    pwc_info = client.paper_list(arxiv_id=arxiv_id)
    return pwc_info.results[0] if pwc_info.results else None

def get_no_of_citations(arxiv_id: str):
    url = f"https://scholar.google.com/scholar_lookup?arxiv_id={arxiv_id}"
    response = requests.get(url)
    response_text = response.text
    soup = BeautifulSoup(response_text, "html.parser")
    a_tags = soup.find_all("a", href=True)

    for a_tag in a_tags:
        if "/scholar?cites" in a_tag["href"]:
            return a_tag.text
    return None


def scholar_lookup(paper_id: str) -> str:
    """Get Google Scholar `cite_id` synchronously using requests library"""
   

def get_repo_info(client, arxiv_id):
    paper_info = get_paper_info(client, arxiv_id)
    if paper_info:
        repo = client.paper_repository_list(paper_info.id)
        return [
            {
                "url": item.url,
                "owner": item.owner,
                "name": item.name,
                "description": item.description,
                "stars": item.stars,
                "framework": item.framework,
                "is_official": item.is_official
            }
            for item in repo.results if all(
                getattr(item, attr) != '' for attr in ['url', 'owner', 'name', 'description', 'stars', 'framework', 'is_official']
            )
        ]
    return []

def get_dataset_info(client, arxiv_id):
    paper_info = get_paper_info(client, arxiv_id)
    if paper_info:
        datasets = client.paper_dataset_list(paper_info.id)
        return [
            {
                "id": item.id,
                "name": item.name,
                "full_name": item.full_name,
                "url": item.url,
            }
            for item in datasets.results if all(
                getattr(item, attr) != '' for attr in ['id', 'name', 'full_name', 'url']
            )
        ]
    return []

def get_methods_info(client, arxiv_id):
    paper_info = get_paper_info(client, arxiv_id)
    if paper_info:
        methods = client.paper_method_list(paper_info.id)
        return [
            {
                "id": item.id,
                "name": item.name,
                "full_name": item.full_name,
                "description": item.description,
                "paper": item.paper,
            }
            for item in methods.results if all(
                getattr(item, attr) != '' for attr in ['id', 'name', 'full_name', 'description', 'paper']
            )
        ]
    return []

def get_tasks_info(client, arxiv_id):
    paper_info = get_paper_info(client, arxiv_id)
    if paper_info:
        tasks = client.paper_task_list(paper_info.id)
        return [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
            }
            for item in tasks.results if all(
                getattr(item, attr) != '' for attr in ['id', 'name', 'description']
            )
        ]
    return []