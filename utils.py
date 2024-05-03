import os
import json
from openai import OpenAI
import tiktoken
from tqdm import tqdm
from paper import Paper
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def pinecone_connect():
    """
    Connects to the Pinecone service, creates an index if it
    doesn't exist, and returns the Pinecone client and index object.

    Returns:
        A tuple containing the Pinecone client and index object.
    """
    index_name = os.getenv("PINECONE_INDEX_NAME")

    pc = Pinecone(
      api_key=os.getenv("PINECONE_API_KEY"),
      environment='us-west-2',
      pool_threads=30  # find next to api key in console
    )
    index = pc.Index(index_name)
    # create a serverless
    if index_name not in str(pc.list_indexes()):
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-west-2'))
    else:
        pass
    
    return pc, index


def pinecone_connect_2():
    """
    Connects to the Pinecone service, creates an index if it
    doesn't exist, and returns the Pinecone client and index object.

    Returns:
        A tuple containing the Pinecone client and index object.
    """
    index_name = os.getenv("PINECONE_INDEX_NAME_2")

    pc = Pinecone(
      api_key=os.getenv("PINECONE_API_KEY_2"),
      environment=os.getenv('PINECONE_ENVIRONMENT_2'),
      pool_threads=30  # find next to api key in console
    )
    index = pc.Index(index_name)
    # create a serverless
    if index_name not in str(pc.list_indexes()):
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-west1-gcp-freee'))
    else:
        pass
    
    return pc, index


def load_data(file_path, categories, start_year, end_year):
    """
    Returns a generator over the papers contained in `file_path`, belonging to
    the categories in `categories`, and published in or after `start_year`.
    
    Args:
        file_path: The path to the JSON file containing the arXiv data
        categories: A list of category strings
        start_year: An integer specifying the earliest year to include
        
    Returns:
        A generator over the papers satisfying the criteria.
    """
    json_file = open(file_path, "r", encoding="utf-8")
    papers = (Paper(json.loads(line)) for line in json_file)
    papers = (paper for paper in papers
              if paper.has_category(categories) and paper.has_valid_id)
    return (paper for paper in papers if paper.year >= start_year and paper.year < end_year)


def pinecone_embedding_count(index_name):
    """
    Helper function to get the total number of embeddings stored in the Pinecone
    index with the name specified in `index_name`.
    
    Args:
        index_name: The name of the Pinecone index
        
    Returns:
        The total number of embeddings stored in the Pinecone index.
    """
    pc, index = pinecone_connect()
    index = pc.Index(index_name)
    return index.describe_index_stats()["total_vector_count"]


def estimate_embedding_price(papers, price_per_1k):
    """
    Estimates the price of embedding the papers in `papers` using OpenAI's
    tiktoken tokenizer.
    
    Args:
        papers: A list of `Paper` objects
        price_per_1k: Price per 1000 tokens
    
    Returns:
        A tuple containing the estimated number of tokens and a price.
    """
    enc = tiktoken.get_encoding("gpt2")
    num_tokens = 0
    for paper in tqdm(papers):
        num_tokens += len(enc.encode(paper.embedding_text))
    print(num_tokens)
    price = num_tokens / 1000 * price_per_1k
    return num_tokens, price


def get_embeddings(texts, model="text-embedding-ada-002"):
    """
    Returns a list of embeddings for each string in `texts` using the OpenAI
    embedding model specified in `model`.
    
    Args:
        texts: A list of strings to embed
        model: The name of the OpenAI embedding model to use
        
    Returns:
        A list of embeddings.
    """
    # For
    # client = OpenAI(api_key=)
    # response = client.embeddings.create(input=texts, model=model)
    # embed_data = response.data[0]

    response = client.embeddings.create(input=texts, model=model)
    return response.data

def embed_and_upsert(papers, index_name, model, batch_size=90):
    """
    Embeds the embedding text of each paper in `papers` using the embedding
    model specified in `model`. The embeddings are then upserted to the Pinecone
    index with name `index_name` in batches of size `batch_size`.
    
    Args:
        papers: The list of papers for which to embed their embedding text
        index_name: The name of the index in which the embeddings will be upserted
        model: The name of the OpenAI embedding model to use
        batch_size: The batch size to use when upserting embeddings to Pinecone
    """
    pc, index = pinecone_connect()
    with pc.Index(index_name,) as index:
        for i in tqdm(range(0, len(papers), batch_size)):
            batch = papers[i:i+batch_size]
            texts = [paper.embedding_text for paper in batch]
            embed_data = get_embeddings(texts, model)
    
            pc_data = [(p.id, e.embedding, p.metadata)
                       for p, e in zip(batch, embed_data)]
            index.upsert(pc_data)


def pinecone_retrieval(index, vector, k, categories=None, year=None):
    """
    Checks if filtering is required based on the user input. If user provides
    `categories` or `year` preferences then filtering is done. Else simply the
    results are returned from Pinecone without any filtering.
    💡 This function is made as there isn't any built-in feature in the python client

    Args:
        query_vector: Embedding of the query
        Index: initialized Pinecone Index
        categories: string of categories selected by the user
        year: string of year selected by the user
    """

    filter_params = {}

    if categories:
        filter_params['categories'] = {'$in': categories.split()}

    if year:
        filter_params['year'] = {'$in': [int(y) for y in year.split()]}

    query_response = index.query(
        top_k=k,
        include_values=True,
        include_metadata=True,
        vector=vector,
        filter=filter_params if filter_params else None
    )

    return query_response


def create_paper_dict(match):
    """
    Creates a dictionary representing a paper based on the provided match.

    Args:
        match: A dictionary representing a match from the query response.

    Returns:
        A dictionary containing the following keys:
        - 'id': The ID of the paper
        - 'title': The title of the paper
        - 'summary': The abstract of the paper
        - 'authors': A set of authors of the paper
        - 'pdf_url': The URL to the PDF of the paper
        - 'date': The publication date of the paper
        - 'categories': The categories of the paper
        - 'similarity_score': The similarity score of the paper match, rounded to the nearest integer.
    """
    return {
        'id': match['id'],
        'title': match['metadata']['title'],
        'summary': match['metadata']['abstract'],
        'authors': {match['metadata']['authors']},
        'pdf_url': f"https://arxiv.org/pdf/{match['id']}.pdf",
        'date': f"{match['metadata']['month']}, {int(match['metadata']['year'])}",
        'categories': match['metadata']['categories'],
        'similarity_score': round(match['score']*100),
    }
