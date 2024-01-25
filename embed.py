from helpers import load_data, embed_and_upsert

# define constants
JSON_FILE_PATH = "arxiv-metadata-oai-snapshot.json"
# CATEGORIES = ["cs.cv", "cs.lg", "cs.cl", "cs.ai", "cs.ne", "cs.ro"]
CATEGORIES = ["cs.cv"] # cs.hc, cs.ai, econ.math, cs.cv
START_YEAR = 2007
EMBED_MODEL = "text-embedding-ada-002"
PRICE_PER_1K = 0.0004 
PINECONE_INDEX_NAME='paperbrain-search'


papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR))
print(len(papers))
embed_and_upsert(papers, PINECONE_INDEX_NAME, model=EMBED_MODEL)