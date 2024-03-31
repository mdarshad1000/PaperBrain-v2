
from openai import OpenAI
from pydub import AudioSegment
from dotenv import load_dotenv
import os
import json

load_dotenv()

# SYSTEM_PROMPT = """
#     You are a podcast script writer, highly skilled in generating engaging intellectual questions and answers in an 
#     easy-to-understand podcast style.

#     Podcasters: 
#         The Interviewer's name is Noah Bennett, and the expert name is Ethan Sullivan. Keep in mind that Ethan is not a
#         co-author or anyone related to the paper, he is just an Expert.

#     Tone: 
#         Maintain a conversational yet authoritative tone. Noah and Ethan should engage the audience by discussing the paper's
#         content with enthusiasm and expertise. 

#     Make sure to have a very catchy introduction and a very cool sounding conclusion (farewell to expert and audience). 
#     Provide output in valid json having Keys 1, 2, ... n, where Odd numbers are for interviewer and Even numbers are for expert.
#     Generate 15-17 dialouges at maximum.
    
#     Additional Notes:
#         Use a blend of technical language and layman terms to make the content accessible to a wide audience.
#         Keep the discussion engaging and avoid jargon overload.
#         Ensure that each section flows naturally into the next, maintaining a coherent narrative throughout the script.
# """
SYSTEM_PROMPT = """
    You are a podcast script writer, highly skilled in generating engaging intellectual questions and answers in an 
    easy-to-understand podcast style.

    Podcasters: 
        The Interviewer's name is Noah Bennett, and the expert name is Ethan Sullivan. Keep in mind that Ethan is not a
        co-author or anyone related to the paper, he is just an Expert. You may consult another Specialist Emma Anderson
        in between the podcast, or even at the starting too (rarely). When consulting her, give a very quick introduction.
        She should have a maximum of 3 dialogues. Include Emma in the conversation in a very smooth and intelligent way.

    Tone: 
        Maintain a conversational yet authoritative tone. Noah and Ethan should engage the audience by discussing the paper's
        content with enthusiasm and expertise. Emma should be consulted for her two cents like the specialist she is.

    Very Important Note:
        Provide output in valid JSON format having Keys NOAH1, NOAH2, ... NOAHn for Noah's dialogue where 1, 2, ... n are the dialogue number.
        Similarly, the Keys for ETHAN should be ETHAN1, ETHAN2, ..., ETHANn where 1, 2, ... n are the dialogue number.
        Lastly, the Keys for EMMA should be EMMA1, EMMA2, ... EMMAn where 1, 2, ... n are the dialogue number.

        
    Make sure to have a very catchy introduction and a very cool sounding conclusion (farewell to expert and audience). 
    Generate 15-17 dialouges at maximum.
    
    Additional Notes:
        Use a blend of technical language and layman terms to make the content accessible to a wide audience.
        Keep the discussion engaging and avoid jargon overload.
        Ensure that each section flows naturally into the next, maintaining a coherent narrative throughout the script.
    """

USER_PROMPT = """
    Based on the given context from a research paper, generate an entire podcast script having 4-5 questions. 
    Keep the podcast engaging, ask follow up questions. You may use analogies sometimes to explain the concepts. 
    In the introduction always include the phrase 'Welcome to Paper Brain'.
    In the conclusion always include 'Check out PaperBrain to explore scientific literature like never before!'
    You are also provided the metadata of the Paper i.e TITLE, AUTHORS, ABSTRACT. Make use of these information
    in the introduction.
    
    \n\n
    CONTEXT:
    \n
    """

clientOAI = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def generate_script(key_findings: str):

    key_findings_str = ''.join(key_findings)
    completion = clientOAI.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type":"json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT + key_findings_str}
        ]
    )

    response = completion.choices[0].message.content
    response = response.strip()
    response_dict = json.loads(response)
    with open('all_files.json', 'w') as f:
        json.dump(response_dict, f)

    return response_dict


def generate_audio_whisper(response_dict: dict, paper_id: str):
    final_audio = AudioSegment.empty()
    intermediate_files = []

    # Load intro music and append to the beginning of the final audio
    intro_music = AudioSegment.from_mp3("music_essentials/intro.mp3")
    final_audio += intro_music

    # for key in sorted(response_dict.keys(), key=int):  # Ensure keys are sorted numerically
    #     if int(key) % 2 == 0:
    #         voice = "onyx"
    #     else:
    #         voice = "echo"
    for key in response_dict.keys():
        if "EMMA" in key:
            voice = "nova"
        elif "ETHAN" in key:
            voice = "onyx"
        else:
            voice = "echo"
        tts_response = clientOAI.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=response_dict[key]
        )
        # Generate a unique filename for each segment
        filename = f"podcast/{key}.mp3"
        tts_response.stream_to_file(filename)
        intermediate_files.append(filename)

        # Append this audio segment to the final audio
        segment = AudioSegment.from_mp3(filename)
        final_audio += segment

    # Load the background music
    bg_music = AudioSegment.from_mp3("music_essentials/bg_music.mp3")
    # Reduce the volume of the background music
    bg_music = bg_music - 30  # Adjust volume reduction as needed


    # Overlay the background music onto the final audio
    final_mix = final_audio.overlay(bg_music, loop=True)

    # Add outro
    outro_music = AudioSegment.from_mp3("music_essentials/outro.mp3")
    clipped_outro = outro_music[-5500:]
    final_mix += clipped_outro - 15 # lower the volume of outro
    
    # Export the mixed audio to a new file
    final_mix.export(f"podcast/{paper_id}.mp3", format="mp3")

    # Delete intermediate files
    for file in intermediate_files:
        os.remove(file)

    return "DONE"



# x = [
#     "[{'TITLE\\n': 'RAFT: Adapting Language Model to Domain Specific RAG', 'AUTHORS\\n': 'Tianjun Zhang, Shishir G. Patil, Naman Jain, Sheng Shen, Matei Zaharia, Ion Stoica, Joseph E. Gonzalez', 'ABSTRACT\\n': 'Pretraining Large Language Models (LLMs) on large corpora of textual data is\\nnow a standard paradigm. When using these LLMs for many downstream\\napplications, it is common to additionally bake in new knowledge (e.g.,\\ntime-critical news, or private domain knowledge) into the pretrained model\\neither through RAG-based-prompting, or fine-tuning. However, the optimal\\nmethodology for the model to gain such new knowledge remains an open question.\\nIn this paper, we present Retrieval Augmented FineTuning (RAFT), a training\\nrecipe that improves the model\\'s ability to answer questions in a \"open-book\"\\nin-domain settings. In RAFT, given a question, and a set of retrieved\\ndocuments, we train the model to ignore those documents that don\\'t help in\\nanswering the question, which we call, distractor documents. RAFT accomplishes\\nthis by citing verbatim the right sequence from the relevant document that\\nwould help answer the question. This coupled with RAFT\\'s chain-of-thought-style\\nresponse helps improve the model\\'s ability to reason. In domain-specific RAG,\\nRAFT consistently improves the model\\'s performance across PubMed, HotpotQA, and\\nGorilla datasets, presenting a post-training recipe to improve pre-trained LLMs\\nto in-domain RAG. RAFT\\'s code and demo are open-sourced at\\ngithub.com/ShishirPatil/gorilla.'}]",
#     "The main findings of this paper are as follows:\n\n1. The RAFT-7B model, which is a finetuned version of LlaMA-2, outperforms both domain-specific finetuned models and general-purpose models with RAG in reading and extracting information from in-domain documents.\n\n2. The inclusion of reference documents in the LlaMA2-7B-chat model with RAG improves its performance in domain-specific question-answering tasks.\n\n3. Domain-specific finetuning without documents in context (DSF) is useful for aligning the answering style of the model and getting familiar with the domain context.\n\n4. Equipping a domain-specific finetuned model with external knowledge using RAG (DSF + RAG) allows the model to refer to the context for knowledge it does not know.\n\n5. The use of Chain-of-Thought responses is demonstrated to be important for the model's learning process.\n\n6. The datasets used in the experiments include Natural Questions (NQ), Trivia QA, HotpotQA, HuggingFace, Torch Hub, TensorFlow Hub, and PubMed QA. These datasets represent diverse domains such as open-domain question-answering, coding/API documents, and biomedical research question-answering.\n\n7. The benchmarks proposed in the Gorilla paper measure the generation of correct, functional, and executable API calls based on documentation.\n\nOverall, the findings suggest that the RAFT-7B model performs well in extracting information from in-domain documents, and the inclusion of reference documents and external knowledge can improve the performance of domain-specific question-answering models. The use of Chain-of-Thought responses is also important for model learning.",
#     "The methods used in this paper include:\n\n1. LlaMA2-7B-chat model with 0-shot prompting: This is a commonly used instruction-finetuned model for QA tasks. It involves providing clearly written instructions but no reference documentation.\n\n2. LlaMA2-7B-chat model with RAG (Llama2 + RAG): Similar to the previous method, this approach also uses the LlaMA2-7B-chat model but includes reference documents. This technique is particularly useful for dealing with domain-specific QA tasks.\n\n3. Domain-specific Finetuning with 0-shot prompting (DSF): This method involves performing standard supervised finetuning without including documents in context. It helps align the answering style of the model and familiarize it with the domain context.\n\n4. Domain-specific Finetuning with RAG (DSF + RAG): This method equips a domain-specific finetuned model with external knowledge using RAG. It allows the model to refer to the context for knowledge it doesn't know.\n\nThese methods were used as baselines in the experiments conducted in the paper to compare the performance of the RAFT-7B model. The RAFT-7B model, which is a finetuned version of LlaMA-2, was found to be better at reading and extracting information from in-domain documents compared to the domain-specific finetuned model and the general-purpose model with RAG.",
#     "The main strengths of this paper are:\n\n1. Comprehensive evaluation: The paper evaluates the performance of the RAFT-7B model compared to various baselines using multiple datasets from different domains, including open-domain question-answering, coding/API documents, and medical research question-answering. This comprehensive evaluation ensures that the strengths of the model are tested across diverse domains.\n\n2. Better performance on in-domain documents: The RAFT-7B model, which is a finetuned version of LlaMA-2, outperforms both domain-specific finetuned models and general-purpose models with RAG in reading and extracting information from in-domain documents. This indicates that the model has a strong ability to understand and process domain-specific information.\n\n3. Integration of external knowledge: The paper demonstrates the importance of equipping a domain-specific finetuned model with external knowledge using RAG. This allows the model to refer to the context for knowledge it does not know, enhancing its ability to generate correct and functional API calls based on the documentation.\n\n4. Emphasis on learning with Chain-of-Thought responses: The paper highlights the importance of the model learning with Chain-of-Thought responses. This approach ensures that the model can generate coherent and contextually appropriate answers, improving the overall quality of its responses.\n\n5. Use of popular and diverse datasets: The paper selects datasets that represent popular and diverse domains, including Wikipedia-based open-domain question-answering, coding/API documents, and medical research question-answering. This ensures that the model's strengths are evaluated across a range of domains, making the findings more applicable and generalizable.\n\nOverall, the strengths of this paper lie in its comprehensive evaluation, better performance on in-domain documents, integration of external knowledge, emphasis on learning with Chain-of-Thought responses, and use of popular and diverse datasets. These strengths contribute to the advancement of question-answering models and their ability to generate accurate and functional API calls based on documentation.",
#     "The main limitations of this paper are:\n\n1. Limited scope: The paper focuses on benchmarks for generating correct API calls based on documentation. It does not cover a wide range of domains and is mainly tailored for biomedical research question-answering. This limited scope may restrict the applicability of the findings to other domains.\n\n2. Lack of comparison with other models: The paper only considers specific baselines for their experiments, such as LlaMA2-7B-chat model with 0-shot prompting and LlaMA2-7B-chat model with RAG. However, it does not compare the performance of their proposed model with other existing models or approaches in the field. This makes it difficult to assess the relative effectiveness of their approach.\n\n3. Limited evaluation metrics: The paper does not provide a comprehensive analysis of the evaluation metrics used to assess the performance of their model. It would be helpful to have a detailed discussion on the strengths and limitations of the chosen metrics and how they capture the desired outcomes of the task.\n\n4. Lack of real-world application evaluation: The paper primarily focuses on evaluating the performance of their model on benchmark datasets. However, it does not provide insights into how well the model performs in real-world scenarios or practical applications. This limits the practical utility of the proposed approach.\n\n5. Lack of discussion on computational efficiency: The paper does not discuss the computational efficiency of their model. It would be valuable to understand the computational requirements and scalability of the proposed approach, especially when dealing with large-scale datasets or real-time applications.\n\nOverall, while the paper presents interesting findings and proposes a novel approach, it has certain limitations in terms of scope, comparison with other models, evaluation metrics, real-world application evaluation, and computational efficiency. These limitations should be considered when interpreting the results and considering the applicability of the proposed approach in practical settings.",
#     "The main application of this paper is to study and propose techniques for adapting a pretrained Language Model (LLM) to a specific domain in the context of domain-specific open-book exams. The paper focuses on how to make the LLM more robust in handling a varying number of retrieved documents and distractors in this specific domain.\n\nSpecifically, the paper discusses the following applications:\n\n1. Generating correct, functional, and executable API calls based on documentation: The benchmarks in the paper measure how to generate accurate API calls using the LLM based on the provided documentation.\n\n2. Biomedical research question-answering: The paper mentions PubMed QA, a question-answering dataset tailored for biomedical research. The LLM is applied to answer medical and biology questions based on a given set of documents.\n\n3. Domain-specific open-book exams: The paper explores the use of LLMs in domain-specific open-book exams, where the LLM is fine-tuned on a specific domain and can utilize any information from that domain to respond to prompts. Examples of domain-specific domains include enterprise documents, latest news, and code repositories. The LLM is used to answer questions within a collection of documents in the specific domain.\n\nOverall, the paper aims to provide insights and techniques for adapting pretrained LLMs to specific domains, improving their performance in generating accurate API calls, answering biomedical research questions, and handling domain-specific open-book exams."
#   ]
# y = generate_script(x)
# generate_audio_whisper(y, 'urdu_story')