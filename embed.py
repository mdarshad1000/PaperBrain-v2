from helpers import load_data, embed_and_upsert

# define constants
JSON_FILE_PATH = "arxiv-metadata-oai-snapshot.json"
# CATEGORIES = ["", "cs.lg", "", "", "", ""]
CATEGORIES = ["cs.lg"] # cs.hc, cs.ai, cs.cl, cs.ne, cs.cv(99%), econ.math, cs.ro, cs.lg(30%),
START_YEAR = 2019
END_YEAR = 2020
EMBED_MODEL = "text-embedding-ada-002"
PRICE_PER_1K = 0.0004
PINECONE_INDEX_NAME='paperbrain-search'


papers = list(load_data(JSON_FILE_PATH, CATEGORIES, START_YEAR, END_YEAR))
print(len(papers))
# 2007-2008=73
# 2008-2009=131
# 2009-2010=230
# 2010-2011=335
# 2011-2013=1808
# 2013-2017=9207
# 2017-2018=5250
# 2018-2019=10495
# 2019-2020=
# 2020-2021
# 2021-2022
# 2022-2023
# 2023-2024


# print(p.id for p in papers)
embed_and_upsert(papers, PINECONE_INDEX_NAME, model=EMBED_MODEL)