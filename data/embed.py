from utils import load_data, embed_and_upsert

# define constants
JSON_FILE_PATH = "./arxiv-metadata-oai-snapshot.json"
# CATEGORIES = ["cs.ai", "cs.cv", "cs.cl", "cs.lg","cs.os", "cs.db", "cs.cc", "cs.ds", "cs.et", "cs.fl", "cs.gl", "cs.gr", "cs.gt", "cs.hc", "cs.it","cs.ir", "cs.lo", "cs.ma", "cs.mm", "cs.ms", "cs.na", "cs.ne", "cs.ar", "cs.ce", "cs.cg", "cs.cr", "cs.dc", "cs.cy", "cs.dl", "cs.dm", "cs.ni", "cs.oh", "cs.pf", "cs.pl", "cs.ro", "cs.sc", "cs.sd", "cs.se", "cs.si", "cs.sy"]
CATEGORIES = ['cs.cl']
START_YEAR = 2023
END_YEAR = 2024
EMBED_MODEL = "text-embedding-ada-002"
PRICE_PER_1K = 0.0001
PINECONE_INDEX_NAME='paperbrain-search'
MONTH='Jan'

papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR, END_YEAR))
print(CATEGORIES,len(papers))

distinct_months = set()
for paper in papers:
    if paper.month not in distinct_months:
        print(paper.month)
        distinct_months.add(paper.month)


# embed_and_upsert(papers, PINECONE_INDEX_NAME, model=EMBED_MODEL)