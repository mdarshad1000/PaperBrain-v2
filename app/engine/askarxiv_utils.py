import logging
from rake_nltk import Rake
from typing import List, Dict
from app.api.routers.semantic_search import create_paper_dict


def refine_query(query: str) -> str:
    rake = Rake()
    rake.extract_keywords_from_text(query)
    keywords = rake.get_ranked_phrases()
    return " ".join(keywords)


def keyword_search(arxiv_client, query: str, top_K: int) -> List[Dict]:
    refined_query = refine_query(query)
    result = arxiv_client.search(query=refined_query, max_results=top_K)
    return result


def semantic_search(
    pinecone_client, openai_client, query: str, top_K: int
) -> List[Dict]:
    res = openai_client.embeddings.create(input=query, model="text-embedding-ada-002")
    query_vector = res.data[0].embedding
    result = pinecone_client.retrieval(vector=query_vector, k=top_K)
    papers_list = [create_paper_dict(match) for match in result["matches"]]
    return papers_list


def rerank_retrievals(cohere_client, query: str, docs: List[str], top_N: int = 10):
    responses = cohere_client.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=docs,
        top_n=top_N,
    ).results
    return responses


def process_and_rank_papers(
    arxiv_client, pinecone_client, openai_client, cohere_client, query: str, top_K: int, top_N: int
) -> List[Dict]:

    keyword_papers = keyword_search(arxiv_client, query, top_K=top_K)
    # keyword_papers.clear()  # Empty the list for Testing

    semantic_papers = semantic_search(pinecone_client, openai_client, query, top_K=20 if len(keyword_papers) == 0 else top_K)
    
    logging.info('semantic length: %s', len(semantic_papers))
    logging.info('keyword length: %s', len(keyword_papers))

    unranked_papers = []
    if len(keyword_papers) != 0:
        for k_paper, s_paper in zip(keyword_papers, semantic_papers):
            unranked_papers.extend([k_paper, s_paper])
    else:
        for s_paper in semantic_papers:
            unranked_papers.append(s_paper)
    
    reranked_papers = rerank_retrievals(
        cohere_client, query=query, docs=[item["title"] + item["summary"] for item in unranked_papers], top_N=top_N
    )
    
    logging.info('Unranked length: %s', len(unranked_papers))
    
    reranked_paper_indices = [item.index for item in reranked_papers]
    reranked_list_of_papers = [unranked_papers[i] for i in reranked_paper_indices]

    return reranked_list_of_papers

def generate_response(
    openai_client, query: str, system_prompt: str, formatted_response: str
):
    oai_client = openai_client

    # Format the input text
    completion = oai_client.chat.completions.create(
        model="gpt-4o",
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
            {"role": "assistant", "content": str(formatted_response)},
        ]
    )
    response = completion.choices[0].message.content
    return response