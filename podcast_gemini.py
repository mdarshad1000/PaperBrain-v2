import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import logging

logging.basicConfig(level=logging.INFO, )


load_dotenv()


def pdf_to_text(pdf_file):
    logging.info('Opening PDF file: %s', pdf_file)
    # Open the PDF file in read mode
    with open(pdf_file, 'rb') as file:
        # Create a PDF file reader object
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        logging.info('Number of pages in PDF file: %d', num_pages)

        # Initialize an empty string to store the text of all pages
        full_text = ''
        # Extract text from each page
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            full_text += page.extract_text()
    special_tokens = ['<eos>', '<bos>', '<pad>', '<EOS>', '<PAD>', '<BOS>']
    for token in special_tokens:
        full_text = full_text.replace(
            token, '(' + token.strip('<>').lower() + ')')

    logging.info('Finished reading PDF file')
    # with open('output.txt', 'w') as output_file:
    #     output_file.write(full_text)
    return full_text


def generate_key_insights(research_paper_text: str):
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    logging.info('Generating key insights using GEMINI')
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

    system_instruction = """
    You are a research expert, highly skilled in extracting key information from research papers. 
    Given a research paper, you extract the important sections and information from the paper.
    The final report should contain headings, subheadings, and relevant content in a distilled and detailed format.
    Make at least 5-6 topics.
    
    The report should contain the right amount of jargon, not too much not too less.
    Some potential topics could be LIMITATIONS, APPLICATIONS, STRENGTHS, FUTURE DIRECTIONS, METHODS, MAIN FINDINGS. 
    
    IMPORTANT NOTE - You don't necessarily have to use these topics if they don't seem fit.
    """

    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                  generation_config=generation_config,
                                  system_instruction=system_instruction,
                                  safety_settings=safety_settings)

    convo = model.start_chat(history=[
    ])

    retry_count = 0
    while retry_count <= 5:
        try:
            logging.info('Attempt %d to send message', retry_count + 1)
            convo.send_message(
                f"""
                    Given below is a Research Paper. Generate a highly detailed, long format report of the research paper.
                    Contain a good mix of stats, jargon, layman explanation etc. Be to the point and 
                    touch up on all the aspects of the paper.
                    OUTPUT FORMAT:

                    1:  TOPIC 1
                        - SubTopic 1
                        <<Information about subtopic 1>>
                        - SubTopic 2
                        <<Information about subtopic2 >>
                        - SubTopic3
                        <<Information about subtopic3 >>
                    
                    
                    2:  TOPIC 2
                        - SubTopic 1
                        <<Information about subtopic 1>>
                        - SubTopic 2
                        <<Information about subtopic2 >>
                        - SubTopic3
                        <<Information about subtopic3 >>

                        ......
                    
                    N:  TOPIC N
                    - SubTopic 1
                    <<Information about subtopic 1>>
                    - SubTopic 2
                    <<Information about subtopic2 >>
                    - SubTopic3
                    <<Information about subtopic3 >>

                    RESEARCH PAPER:

                    {research_paper_text}
                """)
            logging.info('Finished generating key insights')
            return convo.last.text
        except Exception as e:
            logging.error("Error while sending message: %s", e)
            time.sleep(3)
        retry_count += 1
