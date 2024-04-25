import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import os
 
load_dotenv()

def pdf_to_text(pdf_file):
    # Open the PDF file in read mode
    with open(pdf_file, 'rb') as file:
        # Create a PDF file reader object
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)

        # Initialize an empty string to store the text of all pages
        full_text = ''

        # Extract text from each page
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num] 
            full_text += page.extract_text()
        
    return full_text


def generate_key_insights(title, authors, abstract, research_paper_text: str):
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    # Set up the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
    }
    safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
    ]


    system_instruction = "You are a research expert, highly skilled in extracting key information from research papers. Given a research paper, you extract the important sections and information from the paper. The final report should contain headings, subheadings, and relevant content in a distilled and detailed format. Make sure to add the TITLE, AUTHORS, ABSTRACT.  Make at least 5-6 topics.\n\nThe report should contain the right amount of jargon, not too much not too less.\n\Some topics could be LIMITATIONS, APPLICATIONS, STRENGTHS, FUTURE DIRECTIONS, METHODS, MAIN FINDINGS. Make these topics only if relevant to the research paper.\n\n        1:  TOPIC 1\n        - SubTopic 1\n            <<Information about subtopic 1>>\n        - SubTopic 2\n            <<Information about subtopic2 >>\n        - SubTopic3\n            <<Information about subtopic3 >>\n               \n           ...\n\n        - SubTopicN\n            <<Information about subtopic N >>\n\n\n\n        2:  TOPIC 2\n        - SubTopic 1\n            <<Information about subtopic 1>>\n        - SubTopic 2\n            <<Information about subtopic2 >>\n        - SubTopic3\n            <<Information about subtopic3 >> \n\n           ...\n\n        - SubTopicN\n            <<Information about subtopicN >>\n\n        ......\n\n        N:  TOPIC N\n        - SubTopic 1\n            <<Information about subtopic 1>>\n        - SubTopic 2\n            <<Information about subtopic2 >>\n        - SubTopic3\n            <<Information about subtopic3 >>\n               \n           ...\n        - SubTopicN\n            <<Information about subtopicN >>\n   \n"

    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                generation_config=generation_config,
                                system_instruction=system_instruction,
                                safety_settings=safety_settings)

    convo = model.start_chat(history=[
    ])

    convo.send_message(
        f"""
            Given below is a Research Paper. Generate a highly detailed, long format report of the research paper.
            Contain a good mix of stats, jargon, layman explanation etc. Be to the point and 
            touch up on all the aspects of the paper.

            TITLE: {title}

            ABSTRACT: {abstract}

            AUTHORS: {authors}

            RESEARCH PAPER:
            {research_paper_text}
        """)
    return convo.last.text