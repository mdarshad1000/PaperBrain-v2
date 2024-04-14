from utils import load_data, embed_and_upsert

# define constants
JSON_FILE_PATH = "arxiv-metadata-oai-snapshot.json"
CATEGORIES = ["cs.lo"] # cs.hc, cs.ai, cs.cl, cs.ne, cs.ro, cs.lg, cs.se, cs.os, cs.db, cs.ar cs.ce, cs.cc, cs.cg, cs.cr, cs.cy, cs.dc, cs.dl, cs.dm, cs.ds, cs.et, cs.fl, cs.gl, cs.gr, cs.gt, cs.ir, cs.it, cs.lo  cs.cv(99%), econ.math,
START_YEAR = 2024
END_YEAR = 2025
EMBED_MODEL = "text-embedding-ada-002"
PRICE_PER_1K = 0.0001
PINECONE_INDEX_NAME='paperbrain-search'


papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR, END_YEAR))
print(CATEGORIES,len(papers))
# 2007-2008=59
# 2008-2025=7876



# print(73+131+230+335+1808+9207+5250+10495+19286+25883+26524+28706+32898+680)
# print(p.id for p in papers)
embed_and_upsert(papers, PINECONE_INDEX_NAME, model=EMBED_MODEL)