from dotenv import load_dotenv
import os
from pinecone import Pinecone, ServerlessSpec

load_dotenv()


class PineconeService:
    def __init__(self, api_key=None, index_name=None, environment=None):
        self._api_key = api_key if api_key else os.getenv("PINECONE_API_KEY")
        self._index_name = index_name if index_name else os.getenv("PINECONE_INDEX_NAME")
        self._environment = environment if environment else os.getenv('PINECONE_ENVIRONMENT')
        self._pc = None
        self._index = None

    @property
    def pc(self):
        if self._pc is None:
            self._pc = Pinecone(
                api_key=self._api_key,
                environment=self._environment,
                pool_threads=30
            )
        return self._pc

    @property
    def index(self):
        if self._index is None:
            self._index = self.pc.Index(self._index_name)
            if self._index_name not in str(self.pc.list_indexes()):
                self.pc.create_index(
                    name=self._index_name,
                    dimension=1536,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=os.getenv('PINECONE_ENVIRONMENT')))
        return self._index
    

    def retrieval(self, vector, k, categories=None, year=None):
        filter_params = {}
        if categories:
            filter_params['categories'] = {'$in': categories.split()}
        if year:
            filter_params['year'] = {'$in': [int(y) for y in year.split()]}
        query_response = self.index.query(
            top_k=k,
            include_values=True,
            include_metadata=True,
            vector=vector,
            filter=filter_params if filter_params else None
        )
        return query_response

    async def check_paper_exists(self, paper_id: str) -> bool:
        response = self.index.query(
            top_k=1,
            include_metadata=True,
            vector=[0.0 for _ in range(1536)],
            filter={"paper_id": {"$eq": paper_id}},
        )
        return False if len(response['matches']) == 0 else True

    def check_namespace_exists(self, paper_id):
        return paper_id in self.index.describe_index_stats().namespaces
