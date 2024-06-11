# import feedparser
# from typing import List
# import cohere
# import os
# from dotenv import load_dotenv

# load_dotenv()

# def get_cohere_client():
#     return cohere.Client(os.getenv("COHERE_API_KEY"))

# url = 'https://rss.arxiv.org/rss/cs.cv'
# feed = feedparser.parse(url)

# papers = []  # Initialize an empty list to store paper information
# for entry in feed.entries:
#     idd = entry.id
#     title = entry.title
#     abstract = entry.description.split('Abstract: ')[1].split(' (arXiv')[0]
#     authors = entry.authors[0]['name']
#     link = (entry.link).replace('abs', 'pdf')
#     announce_type = entry.arxiv_announce_type
#     if announce_type == 'cross':
#         continue  # Skip the current iteration if it's a cross-listed paper

#     paper_info = {
#         "Id": idd,
#         "Title": title,
#         "Abstract": abstract,
#         "Authors": authors,
#         "Link": link
#     }
#     papers.append(paper_info)  # Add the dictionary to the papers list



# def rerank_retrievals(cohere_client, query: str, docs: List[str], top_N: int = 10):
#     responses = cohere_client.rerank(
#         model="rerank-english-v3.0",
#         query=query,
#         documents=docs,
#         top_n=top_N,
#     ).results
#     return responses

# query = """
#     Large language model pretraining and finetunings.
#     Multimodal machine learning.
#     Do not care about specific application, for example, information extraction, summarization, etc.
#     Not interested in paper focus on specific languages, e.g., Arabic, Chinese, etc.
# """

# reranked_papers = rerank_retrievals(
#     get_cohere_client(), query=query, docs=[item["Title"] + item["Abstract"] for item in papers], top_N=10
# )

# # Assuming reranked_papers is the list you've provided in your message
# for reranked_paper in reranked_papers:
#     index = reranked_paper.index
#     paper_info = papers[index]  # Use the index to access the paper from the papers list
#     print(paper_info)
#     print()
#     print()
#     print()

