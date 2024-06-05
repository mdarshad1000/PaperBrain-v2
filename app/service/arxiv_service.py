import io
import arxiv
import fitz
import logging
import requests
from datetime import datetime

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


    @classmethod
    def get_metadata(cls, paper_id):
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
    
    @classmethod
    def get_pdf_txt(cls, paperurl: str, exclude_references=True):
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
    
