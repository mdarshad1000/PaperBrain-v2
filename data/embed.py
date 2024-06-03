from utils import load_data, embed_and_upsert

# define constants
JSON_FILE_PATH = "arxiv-metadata-oai-snapshot.json"

# CATEGORIES = ["cs.ai", "cs.cv",]
# CATEGORIES = ["cs.cl", "cs.lg",]
# CATEGORIES = ["cs.os", "cs.db", "cs.cc"]
# CATEGORIES = ["cs.ds", "cs.et", "cs.fl", "cs.gl", "cs.gr", "cs.gt", "cs.hc", "cs.it",]
# CATEGORIES = ["cs.ir", "cs.lo", "cs.ma", "cs.mm", "cs.ms", "cs.na", "cs.ne",]
# CATEGORIES = ["cs.ar", "cs.ce", "cs.cg", "cs.cr", "cs.dc", "cs.cy", "cs.dl", "cs.dm"]
CATEGORIES = ["cs.ni", "cs.oh", "cs.pf", "cs.pl", "cs.ro", "cs.sc", "cs.sd", "cs.se", "cs.si", "cs.sy"]



START_YEAR = 2010
END_YEAR = 2025
EMBED_MODEL = "text-embedding-ada-002"
PRICE_PER_1K = 0.0001
PINECONE_INDEX_NAME='paperbrain-search'


papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR, END_YEAR))
print(CATEGORIES,len(papers))




# print(73+131+230+335+1808+9207+5250+10495+19286+25883+26524+28706+32898+680)
# print(p.id for p in papers)
embed_and_upsert(papers, PINECONE_INDEX_NAME, model=EMBED_MODEL)