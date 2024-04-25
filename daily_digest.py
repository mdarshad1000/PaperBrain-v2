import requests
from bs4 import BeautifulSoup
import os
import json  # Import the json module
        

def fetch_papers(categories: list):
    papers_data = []

    for category in categories:
        if os.path.exists(f'daily_papers/{category}.json'):
            return
             
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

        return 


def ranking_step_one(categories: list):
    pass


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


# fetch_papers(['cs.cv'])

