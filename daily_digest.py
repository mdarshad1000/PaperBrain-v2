import requests
from bs4 import BeautifulSoup
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
        

def fetch_papers(categories: list):
    papers_data = []

    for category in categories:
        if os.path.exists(f'daily_papers/{category}.json'):
            continue
             
        else:
            # Define the URL for each category
            url = f"https://arxiv.org/list/{category}/new"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            h2 = soup.find_all("h2")
            for item in h2:
                papers = item.find_next_sibling("dl")

                for p_id, p_info in zip(papers.find_all("dt"), papers.find_all("dd")):
                    paper_id = p_id.find("span", {"class": "list-identifier"}).text.strip().split(":")[1].split()[0]
                    title = p_info.find("div", {"class": "list-title mathjax"}).text.strip()
                    authors = p_info.find("div", {"class": "list-authors"}).text.strip()
                    subjects = p_info.find("div", {"class": "list-subjects"}).text.strip()
                    abstract = p_info.find("p", {"class": "mathjax"}).text.strip()
                    paper_data = {
                        "id": paper_id,
                        "title": title,
                        "authors": authors,
                        "subjects": subjects,
                        "abstract": abstract
                    }
                    papers_data.append(paper_data)

            # Write the papers_data to a new JSON file
            with open(f'daily_papers/{category}.json', 'w') as json_file:
                json.dump(papers_data, json_file, indent=4)



def recommend_papers(categories, interests):

    all_papers = []

    for category in categories:
        with open(f'daily_papers/{category}.json', 'r') as f:
            papers = json.load(f)
            all_papers.extend(papers)
            
    all_papers_json_str = json.dumps(all_papers)

    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    # Set up the model
    generation_config = {
        "temperature": .2,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 15000,
        "response_mime_type": "application/json",
        }
    safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
    ]


    system_instruction = """
                        TASK:
                            You are an expert research assistant who is skilled in recommending research papers based on USER's resarch interest.
                            You will be provided with a JSON of Research Papers as well as USER's INTERESTS. Go through each research paper and
                            compare if it is relvant to USER's research interest.
                            Give a relevancy score on a scale of 1-10 based on how relevant the paper is for the USER.
                            Give a 1-2 line short description as to why the paper is Relevant for the user.

                        POINTS TO KEEP IN MIND:
                            Your output should contain a maximum of 15 papers.
                            Your output should contain a minimum of 3 papers.
                            Do not recommend papers with rating below 7.

                    
                        {{INPUT FORMAT}}:
                        
                        [
                            {
                                "id": paper_id 1
                                "title": Title of the Paper 1,
                                "authors": Authors of the Paper 1,
                                "subjects": Subjects/Categories 1,
                                "abstract": Abstract of the Paper 1,
                            },
                            {
                                "id": paper_id 2
                                "title": Title of the Paper 2,
                                "authors": Authors of the Paper 2,
                                "subjects": Subjects/Categories 2,
                                "abstract": Abstract of the Paper 2,
                            },
                            
                            ...

                            {
                                "id": paper_id n
                                "title": Title of the Paper n,
                                "authors": Authors of the Paper n,
                                "subjects": Subjects/Categories n,
                                "abstract": Abstract of the Paper n, 
                            }
                        ]

                        
                        {{OUTPUT FORMAT}}:

                        [
                            {
                                "id": paper_id 1
                                "title": Title of the Paper 1,
                                "authors": Authors of the Paper 1,
                                "abstract": Abstract of the Paper 1,
                                "relevancy score": "an integer score out of 10",
                                "Reasons for match": "1-2 sentence short reasonings" about how it matches with USER's interest.
                            },
                            {
                                "id": paper_id 2
                                "title": Title of the Paper 2,
                                "authors": Authors of the Paper 2,
                                "abstract": Abstract of the Paper 2,
                                "relevancy score": "an integer score out of 10",
                                "Reasons for match": "1-2 sentence short reasonings" about how it matches with USER's interest.
                            },
                            
                            ...

                            {
                                "id": paper_id n
                                "title": Title of the Paper n,
                                "authors": Authors of the Paper n,
                                "abstract": Abstract of the Paper n,
                                "relevancy score": "an integer score out of 10",
                                "Reasons for match": "1-2 sentence short reasonings" about how it matches with USER's interest.
                            },
                        ]
                        """


    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                generation_config=generation_config,
                                system_instruction=system_instruction,
                                safety_settings=safety_settings)

    convo = model.start_chat(history=[
    ])

    convo.send_message("""
                            You have been asked to read a list of a few arxiv papers, each with title, authors and abstract.
                            Based on my specific research interests, relevancy score out of 10 for each paper, based on my specific research interest, with a higher score indicating greater relevance. A relevance score more than 7 will need person's attention for details.
                            Additionally, please generate 1-2 sentence summary for each paper explaining why it's relevant to my research interests.
                            At least return 3 papers and at max 15.
                            Once you have all the information, return the 
                            "ID"
                            "Title"
                            "Abstract"
                            "Authors": 
                            "Relevancy score": "an integer score out of 10",
                            "Reasons for match": "1-2 sentence short reasonings" about how it matches with USER's interest.
                            
                            INTERESTS:
                            {interest}                        
                                
                            GIVEN PAPERS:
                            {papers_list}""".format(interest=interests, papers_list=all_papers_json_str)
    )
    return convo.last.text



def rank_papers(interest: str, papers_list: list, client):
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type":"json_object"},
        messages=[
            {
                "role": "system",
                "content": """You are an expert assistant who can select papers based on user's resarch interest.\
                            Your response should be in a JSON format
                            """
            },
            {   
                "role": "user",
                "content": """
                            You have been asked to read a list of a few arxiv papers, each with title, authors and abstract.
                            Based on my specific research interests, relevancy score out of 10 for each paper, based on my specific research interest, with a higher score indicating greater relevance. A relevance score more than 7 will need person's attention for details.
                            Additionally, please generate 1-2 sentence summary for each paper explaining why it's relevant to my research interests.
                            At least return 3 papers and at max 10.
                            Once you have all the information, return the 
                            "ID"
                            "Title"
                            "Abstract"
                            "Authors": 
                            "Relevancy score": "an integer score out of 10",
                            "Reasons for match": "1-2 sentence short reasonings" along with 
                            
                            INTERESTS:
                            {interest}                        
                                
                            GIVEN PAPERS:
                            {papers_list}""".format(interest=interest, papers_list=papers_list)
            },  

        ],

    )

    output = completion.choices[0].message.content
    return output

categories = ['cs.cv']
interests = """
        Large language model pretraining and finetunings
        Multimodal machine learning
        Do not care about specific application, for example, information extraction, summarization, etc.
        Not interested in paper focus on specific languages, e.g., Arabic, Chinese, etc.
        """

fetch_papers(categories=['cs.ai'])
print(recommend_papers(categories=categories, interests=interests))
