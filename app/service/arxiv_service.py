import io
import arxiv
import fitz
import logging
import asyncio
import aiohttp
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)

class ArxivManager:

    def search(self, query=None, list_of_ids=None, max_results=10, sort_by=arxiv.SortCriterion.Relevance):
        if list_of_ids:
            search = arxiv.Search(id_list=list_of_ids, max_results=max_results, sort_by=sort_by)
        else:
            search = arxiv.Search(query=query, max_results=max_results, sort_by=sort_by)
        
        results = search.results()
        return [
            {
                "id": result.entry_id.split("/")[-1].split("v")[0],
                "title": result.title,
                "summary": result.summary,
                "authors": [author.name for author in result.authors],
                "pdf_url": result.pdf_url,
                "date": datetime.strptime(str(result.published), "%Y-%m-%d %H:%M:%S%z").strftime("%B, %Y"),
                "categories": result.categories,
            }
            for result in results
        ]
    
    @staticmethod
    def id_from_url(paperurl):
        return paperurl.split("/")[-1].split("v")[0].strip(".pdf")
    
    @staticmethod
    def url_from_id(paper_id):
        return f"https://arxiv.org/pdf/{paper_id}"


    @staticmethod
    async def get_metadata(paper_id):
        paper = arxiv.Search(id_list=[paper_id]).results()

        paper_info = [
                {
                    "TITLE": item.title,
                    "AUTHORS": ", ".join(author.name for author in item.authors),
                    "ABSTRACT": item.summary,
                }
            for item in paper
        ]
    
        title = paper_info[0]['TITLE']
        authors = paper_info[0]['AUTHORS']
        abstract = paper_info[0]['ABSTRACT']

        return title, authors, abstract
        
    @staticmethod
    async def get_pdf_txt(paperurl: str, exclude_references=True):
        """
        Fully asynchronous PDF processing pipeline
        """
        async def process_pdf_text(pdf_contents: str) -> str:
            """Process PDF text asynchronously"""
            if exclude_references:
                ref_index = pdf_contents.lower().rfind("reference")
                if ref_index != -1:
                    pdf_contents = pdf_contents[:ref_index]

            special_tokens = ['<eos>', '<bos>', '<pad>', '<EOS>', '<PAD>', '<BOS>']
            for token in special_tokens:
                pdf_contents = pdf_contents.replace(token, '(' + token.strip('<>').lower() + ')')
            return pdf_contents

        stream = io.BytesIO()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(paperurl) as resp:
                if resp.status == 200:
                    async for chunk in resp.content.iter_chunked(8192):
                        stream.write(chunk)
                else:
                    raise Exception(f"Failed to download PDF, status code: {resp.status}")
        
        stream.seek(0)


        # Create a ThreadPoolExecutor for PDF processing
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            # Run PDF text extraction in thread pool
            raw_text = await loop.run_in_executor(pool, lambda: ArxivManager._extract_text_concurrently(stream))
            # Process the text asynchronously
            pdf_contents = await process_pdf_text(raw_text)

            
        return pdf_contents

    @staticmethod
    def _extract_text_concurrently(stream):
        """
        Extracts text from the PDF using threads for each page's text extraction.
        """
        with fitz.Document(stream=stream) as pdf:
            data = "".join([page.get_text() for page in pdf.pages()])
            return data

    @staticmethod
    def get_pdf_txt_sync(paperurl: str, exclude_references=True):
        resp = requests.get(paperurl, stream=True)
        stream = io.BytesIO(resp.content)

        page_txts = []
        with fitz.Document(stream=stream) as pdf:
            for page in pdf.pages():
                txt = page.get_text()
                page_txts.append(txt)
        
        pdf_contents = "".join(page_txts)

        if exclude_references:
            # find last occurrence of 'references' in case the paper content mentions it before the heading
            try:
                idx = pdf_contents.lower().rindex("reference")
                pdf_contents = pdf_contents[:idx]
            except ValueError as e:
                pass
        # TODO: Find all "tokens" which might throw 500 Internal Server Error for GeminiAPICall.
        # removing tokens which raise 500 in Gemini call
        special_tokens = ['<eos>', '<bos>', '<pad>', '<EOS>', '<PAD>', '<BOS>']
        for token in special_tokens:
            pdf_contents = pdf_contents.replace(
                token, '(' + token.strip('<>').lower() + ')')
            
        return pdf_contents
