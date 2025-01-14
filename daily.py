# import os
# import cohere
# import feedparser
# import numpy as np
# from typing import List
# from dotenv import load_dotenv

# load_dotenv()


# def get_cohere_client():
#     return cohere.Client(os.getenv("COHERE_API_KEY"))


# def get_papers(categories: List[str]) -> List[dict]:
#     papers = []
#     for category in categories:
#         url = f"https://rss.arxiv.org/rss/{category}"
#         feed = feedparser.parse(url)
#         for entry in feed.entries:
#             idd = entry.id
#             title = entry.title
#             abstract = entry.description.split("Abstract: ")[1].split(" (arXiv")[0]
#             authors = entry.authors[0]["name"]
#             link = (entry.link).replace("abs", "pdf")
#             categories = [tag["term"] for tag in entry.tags]  # Get all categories
#             announce_type = entry.arxiv_announce_type
#             if announce_type == "cross":
#                 continue  # Skip the current iteration if it's a cross-listed paper

#             paper_info = {
#                 "id": idd.split(":")[-1].split("v")[0],
#                 "title": title,
#                 "abstract": abstract,
#                 "authors": authors,
#                 "link": link,
#                 "category": categories,
#             }
#             papers.append(paper_info)  # Add the dictionary to the papers list
#     return papers


# def rerank_retrievals(cohere_client, query: str, docs: List[str], top_N: int = 10):
#     responses = cohere_client.rerank(
#         model="rerank-english-v3.0",
#         query=query,
#         documents=docs,
#         top_n=top_N,
#     ).results
#     return responses


# if __name__ == "__main__":
    
#     query = """
#         Fine tuning a large language model on a small dataset.
#     """
#     papers = get_papers(['cs.cv', 'cs.cl', 'cs.lg', 'cs.os', 'cs.db', 'cs.cc'])

    

#     # reranked_papers = rerank_retrievals(
#     #     get_cohere_client(), query=query, docs=[item["Title"] + item["Abstract"] for item in papers], top_N=10
#     # )

#     i = 0
#     # Assuming reranked_papers is the list you've provided in your message
#     for reranked_paper in papers:
#         # index = reranked_paper.index
#         # paper_info = papers[index]  # Use the index to access the paper from the papers list
#         # print(paper_info)
#         print(reranked_paper)
#         print()
#         print()
#         print()

#         i += 1
#     print(i)