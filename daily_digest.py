import requests
from bs4 import BeautifulSoup

papers_data = []
def fetch_papers(category: list):
    # Define the URL
    url = f"https://arxiv.org/list/{category}/new"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    h2 = soup.find_all("h2")
    date = ' '.join(soup.find("h3").text.strip().split()[-4:])
    for item in h2:
        
        papers = item.find_next_sibling("dl")

        for p_id, p_info in zip(papers.find_all("dt"), papers.find_all("dd")):

            paper_id = p_id.find("span", {"class": "list-identifier"}).text.strip().split(":")[1].split()[0]
            title = p_info.find("div", {"class": "list-title mathjax"}).text.strip()
            authors = p_info.find("div", {"class": "list-authors"}).text.strip()
            subjects = p_info.find("div", {"class": "list-subjects"}).text.strip()
            abstract = p_info.find("p", {"class": "mathjax"}).text.strip()
            
            paper_data ={
                "id": paper_id,
                "title": title,
                "authors": authors,
                "subjects": subjects,
                "abstract": abstract
            }
            papers_data.append(paper_data)

    return papers_data, date


def rank_papers(interest: str, papers_list: list, client):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
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
                "content": f"""You are an expert in ranking research papers based on relevance. \
                            You will receive an input from the user which will have their Research Interests,\
                            along with titles, id, abstract of articles/research paper for that query.\
                            Once you have all the information, return the ID, Title, Abstract, Authors of the \
                            5 most relevant paper
                            
                            INTERESTS:
                            {interest}                        
                                
                            GIVEN PAPERS:
                            {papers_list}"""
            },
            
        ],

    )

    output = completion.choices[0].message.content
    return output


