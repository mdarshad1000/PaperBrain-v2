# pdf = load_pdf('desktop/pdf.1')
# import pinecone
# import tfidf
# from llama_index.core.query_engine import RouterQueryEngine


# pinecone.init(
#     metrics='euclidean'
# )

# txt = pypdf.convert(pdf)

# txt = 'my name is arshad. i am 23 yrs old. i am jobless'

# chunks = txt.split('\n\n') -> ['my name is arshad', 'i am 23 yrs old', 'i am jobless']

# dense_vectors = [[1,2,3], [3,5,6], [9,0,0]]

# for chunk in chunks:
#     chunk_vector = openai.embed(chunk) -> [0.1, 0.3432, ...]
#     dense_vectors.append(chunk_vector)

# # same goes for tfidf
# sparse_vector = [[1,2,3], [3,5,6], [9,0,0]]

# final_data = [[metadata, dense, sparse], [], []]
# for i, j in zip(vectors, chunks):
#     final_data.update({i:j})

# final_data.upsert_to_vdb

# # data retrieval
# user_query = 'what is your name?'
# mini_llm.call('arshad is my nmae')


# query_vector = openai.embed(user_query) -> [2,9,0]


# relevant_chunks = vector_db.retrieve(vector=query_vector, top_k=2, dense=True) -> 
# relevant_chunks_2 = vector_db.retrieve(vector=query_vector, top_k=2, dense=False)

# # output
# {
#     1: {
#         metadata: 'my name is arshad',
#         vector: [1,2,3],
#         score: 0.9
#     },
#     2 : {
#         metadata: 'i am 23',
#         vector: [0,2,3],
#         score: 0.8
#     }
# }



# def generate(query, context):
#     answer = openai.gpt4(f'i will .....this is the context {context} and this is the user query {query}')

#     return answer

# print(generate(user_query, str(relevant_chunks.metadata)))


    


# json = {
#     1: 'my name is arshad',
#     2:'i am 23 yrs old',
# }

# # arxiv = {
# #     1: {
# #         abstract:fjdsafjl;kasd,
# #         title:jfkldasjfl;kasd,
# #         author:dfjlkdsajf
# #     },
# #     2{

# #     }
# # }

# # RAG fusion
# # Hyde
# # Reranker
# # query expansion
# # query decomposition
# # 

l = [
  {
    "abstract": "We present a question-and-answer (Q\\&A) application designed to support the contract management process by leveraging combined information from contract documents (PDFs) and data retrieved from contract management systems (database). This data is processed by a large language model (LLM) to provide precise and relevant answers. The accuracy of these responses is further enhanced through the use of Retrieval-Augmented Generation (RAG), text-to-SQL techniques, and agents that dynamically orchestrate the workflow. These techniques eliminate the need to retrain the language model. Additionally, we employed Prompt Engineering to fine-tune the focus of responses. Our findings demonstrate that this multi-agent orchestration and combination of techniques significantly improve the relevance and accuracy of the answers, offering a promising direction for future information systems.",
    "reasons_for_relevancy": "Highly relevant as it incorporates AI agents and RAG within large language models, aligning with interests in AI and RAG evaluation.",
    "title": "Contrato360 2.0: A Document and Database-Driven Question-Answer System using Large Language Models and Agents",
    "relevancy_score": 10,
    "authors": [
      "Antony Seabra",
      "Claudio Cavalcante",
      "Joao Nepomuceno",
      "Lucas Lago",
      "Nicolaas Ruberg",
      "Sergio Lifschitz"
    ]
  },
  {
    "abstract": "Retrieving relevant context is a common approach to reduce hallucinations and enhance answer reliability. Explicitly citing source documents allows users to verify generated responses and increases trust. Prior work largely evaluates citation correctness - whether cited documents support the corresponding statements. But citation correctness alone is insufficient. To establish trust in attributed answers, we must examine both citation correctness and citation faithfulness. In this work, we first disentangle the notions of citation correctness and faithfulness, which have been applied inconsistently in previous studies. Faithfulness ensures that the model's reliance on cited documents is genuine, reflecting actual reference use rather than superficial alignment with prior beliefs, which we call post-rationalization. We design an experiment that reveals the prevalent issue of post-rationalization, which undermines reliable attribution and may result in misplaced trust. Our findings suggest that current attributed answers often lack citation faithfulness (up to 57 percent of the citations), highlighting the need to evaluate correctness and faithfulness for trustworthy attribution in language models.",
    "reasons_for_relevancy": "Highly relevant due to its focus on RAG Evaluation and the need to separate correctness from faithfulness in attribution, aligned with AI insights.",
    "title": "Correctness is not Faithfulness in RAG Attributions",
    "relevancy_score": 10,
    "authors": [
      "Jonas Wallat",
      "Maria Heuss",
      "Maarten de Rijke",
      "Avishek Anand"
    ]
  },
  {
    "abstract": "We propose a methodology that combines several advanced techniques in Large Language Model (LLM) retrieval to support the development of robust, multi-source question-answer systems. This methodology is designed to integrate information from diverse data sources, including unstructured documents (PDFs) and structured databases, through a coordinated multi-agent orchestration and dynamic retrieval approach. Our methodology leverages specialized agents-such as SQL agents, Retrieval-Augmented Generation (RAG) agents, and router agents - that dynamically select the most appropriate retrieval strategy based on the nature of each query. To further improve accuracy and contextual relevance, we employ dynamic prompt engineering, which adapts in real time to query-specific contexts. The methodology's effectiveness is demonstrated within the domain of Contract Management, where complex queries often require seamless interaction between unstructured and structured data. Our results indicate that this approach enhances response accuracy and relevance, offering a versatile and scalable framework for developing question-answer systems that can operate across various domains and data sources.",
    "reasons_for_relevancy": "Relevant due to the focus on AI agents, RAG methodologies, and LLM retrieval strategies, matching interests in AI agents and RAG evaluation.",
    "title": "Dynamic Multi-Agent Orchestration and Retrieval for Multi-Source Question-Answer Systems using Large Language Models",
    "relevancy_score": 9,
    "authors": [
      "Antony Seabra",
      "Claudio Cavalcante",
      "Joao Nepomuceno",
      "Lucas Lago",
      "Nicolaas Ruberg",
      "Sergio Lifschitz"
    ]
  },
  {
    "abstract": "Knowledge stored in large language models requires timely updates to reflect the dynamic nature of real-world information. To update the knowledge, most knowledge editing methods focus on the low layers, since recent probes into the knowledge recall process reveal that the answer information is enriched in low layers. However, these probes only and could only reveal critical recall stages for the original answers, while the goal of editing is to rectify model's prediction for the target answers. This inconsistency indicates that both the probe approaches and the associated editing methods are deficient. To mitigate the inconsistency and identify critical editing regions, we propose a contrast-based probe approach, and locate two crucial stages where the model behavior diverges between the original and target answers: Information Enrichment in low layers and Probability Promotion in high layers. Building upon the insights, we develop the Joint knowledge Editing for information Enrichment and probability Promotion (JEEP) method, which jointly edits both the low and high layers to modify the two critical recall stages. Considering the mutual interference and growing forgetting due to dual modifications, JEEP is designed to ensure that updates to distinct regions share the same objectives and are complementary. We rigorously evaluate JEEP by editing up to thousands of facts on various models, i.e., GPT-J (6B) and LLaMA (7B), and addressing diverse editing objectives, i.e., adding factual and counterfactual knowledge. In all tested scenarios, JEEP achieves best performances, validating the effectiveness of the revealings of our probe approach and the designs of our editing method. Our code and data are available at this https URL.",
    "reasons_for_relevancy": "Relevant due to its focus on knowledge editing in LLMs like GPT-J and LLaMA, closely related to AI agents and model behavior.",
    "title": "Joint Knowledge Editing for Information Enrichment and Probability Promotion",
    "relevancy_score": 9,
    "authors": [
      "Wenhang Shi",
      "Yiren Chen",
      "Shuqing Bian",
      "Xinyi Zhang",
      "Zhe Zhao",
      "Pengfei Hu",
      "Wei Lu",
      "Xiaoyong Du"
    ]
  },
  {
    "abstract": "Large language models can generate factually inaccurate content, a problem known as hallucination. Recent works have built upon retrieved-augmented generation to improve factuality through iterative prompting but these methods are limited by the traditional RAG design. To address these challenges, we introduce EWE (Explicit Working Memory), a novel approach that enhances factuality in long-form text generation by integrating a working memory that receives real-time feedback from external resources. The memory is refreshed based on online fact-checking and retrieval feedback, allowing EWE to rectify false claims during the generation process and ensure more accurate and reliable outputs. Our experiments demonstrate that the EWE outperforms strong baselines on four fact-seeking long-form generation datasets, increasing the factuality metric, VeriScore, by 2 to 10 points absolute without sacrificing the helpfulness of the responses. Further analysis reveals that the design of rules for memory updates, configurations of memory units, and the quality of the retrieval datastore are crucial factors for influencing model performance.",
    "reasons_for_relevancy": "Directly related to research interest in RAG evaluation and improving factuality, relevant for studying advancements in AI agents.",
    "title": "Improving Factuality with Explicit Working Memory",
    "relevancy_score": 9,
    "authors": [
      "Mingda Chen",
      "Yang Li",
      "Karthik Padthe",
      "Rulin Shao",
      "Alicia Sun",
      "Luke Zettlemoyer",
      "Gargi Gosh",
      "Wen-tau Yih"
    ]
  },
  {
    "abstract": "Large Language Models (LLMs) have achieved impressive results in knowledge-based Visual Question Answering (VQA). However existing methods still have challenges: the inability to use external tools autonomously, and the inability to work in teams. Humans tend to know whether they need to use external tools when they encounter a new question, e.g., they tend to be able to give a direct answer to a familiar question, whereas they tend to use tools such as search engines when they encounter an unfamiliar question. In addition, humans also tend to collaborate and discuss with others to get better answers. Inspired by this, we propose the multi-agent voting framework. We design three LLM-based agents that simulate different levels of staff in a team, and assign the available tools according to the levels. Each agent provides the corresponding answer, and finally all the answers provided by the agents are voted to get the final answer. Experiments on OK-VQA and A-OKVQA show that our approach outperforms other baselines by 2.2 and 1.0, respectively.",
    "reasons_for_relevancy": "Involves AI agents that use LLMs in a multi-agent framework for VQA, closely aligning with AI agent interests.",
    "title": "Multi-Agents Based on Large Language Models for Knowledge-based Visual Question Answering",
    "relevancy_score": 9,
    "authors": [
      "Zhongjian Hu",
      "Peng Yang",
      "Bing Li",
      "Zhenqi Wang"
    ]
  },
  {
    "abstract": "Large language models (LLMs) have brought exciting new advances to mobile UI agents, a long-standing research field that aims to complete arbitrary natural language tasks through mobile UI interactions. However, existing UI agents usually demand high reasoning capabilities of powerful large models that are difficult to be deployed locally on end-users' devices, which raises huge concerns about user privacy and centralized serving cost. One way to reduce the required model size is to customize a smaller domain-specific model with high-quality training data, e.g. large-scale human demonstrations of diverse types of apps and tasks, while such datasets are extremely difficult to obtain. Inspired by the remarkable coding abilities of recent small language models (SLMs), we propose to convert the UI task automation problem to a code generation problem, which can be effectively solved by an on-device SLM and efficiently executed with an on-device code interpreter. Unlike normal coding tasks that can be extensively pretrained with public datasets, generating UI automation code is challenging due to the diversity, complexity, and variability of target apps. Therefore, we adopt a document-centered approach that automatically builds fine-grained API documentation for each app and generates diverse task samples based on this documentation. By guiding the agent with the synthetic documents and task samples, it learns to generate precise and efficient scripts to complete unseen tasks. Based on detailed comparisons with state-of-the-art mobile UI agents, our approach effectively improves the mobile task automation with significantly higher success rates and lower latency/token consumption. Code will be open-sourced.",
    "reasons_for_relevancy": "Relevant due to its focus on AI agents and code generation for UI automation, aligning with interests in AI Agents.",
    "title": "AutoDroid-V2: Boosting SLM-based GUI Agents via Code Generation",
    "relevancy_score": 8,
    "authors": [
      "Hao Wen",
      "Shizuo Tian",
      "Borislav Pavlov",
      "Wenjie Du",
      "Yixuan Li",
      "Ge Chang",
      "Shanhui Zhao",
      "Jiacheng Liu",
      "Yunxin Liu",
      "Ya-Qin Zhang",
      "Yuanchun Li"
    ]
  },
  {
    "abstract": "International enterprises, organizations, or hospitals collect large amounts of multi-modal data stored in databases, text documents, images, and videos. While there has been recent progress in the separate fields of multi-modal data exploration as well as in database systems that automatically translate natural language questions to database query languages, the research challenge of querying database systems combined with other unstructured modalities such as images in natural language is widely unexplored.\\nIn this paper, we propose XMODE - a system that enables explainable, multi-modal data exploration in natural language. Our approach is based on the following research contributions: (1) Our system is inspired by a real-world use case that enables users to explore multi-modal information systems. (2) XMODE leverages a LLM-based agentic AI framework to decompose a natural language question into subtasks such as text-to-SQL generation and image analysis. (3) Experimental results on multi-modal datasets over relational data and images demonstrate that our system outperforms state-of-the-art multi-modal exploration systems, excelling not only in accuracy but also in various performance metrics such as query latency, API costs, planning efficiency, and explanation quality, thanks to the more effective utilization of the reasoning capabilities of LLMs.",
    "reasons_for_relevancy": "Aligns with interest in AI Agents and makes use of LLMs.",
    "title": "Explainable Multi-Modal Data Exploration in Natural Language via LLM Agent",
    "relevancy_score": 8,
    "authors": [
      "Farhad Nooralahzadeh",
      "Yi Zhang",
      "Jonathan Furst",
      "Kurt Stockinger"
    ]
  },
  {
    "abstract": "Long Context Language Models (LCLMs) have emerged as a new paradigm to perform Information Retrieval (IR), which enables the direct ingestion and retrieval of information by processing an entire corpus in their single context, showcasing the potential to surpass traditional sparse and dense retrieval methods. However, processing a large number of passages within in-context for retrieval is computationally expensive, and handling their representations during inference further exacerbates the processing time; thus, we aim to make LCLM retrieval more efficient and potentially more effective with passage compression. Specifically, we propose a new compression approach tailored for LCLM retrieval, which is trained to maximize the retrieval performance while minimizing the length of the compressed passages. To accomplish this, we generate the synthetic data, where compressed passages are automatically created and labeled as chosen or rejected according to their retrieval success for a given query, and we train the proposed Compression model for Long context Retrieval (CoLoR) with this data via preference optimization while adding the length regularization loss on top of it to enforce brevity. Through extensive experiments on 9 datasets, we show that CoLoR improves the retrieval performance by 6% while compressing the in-context size by a factor of 1.91.",
    "reasons_for_relevancy": "Relevant due to its focus on Information Retrieval and Long Context Language Models, which relate to AI agent efficiency.",
    "title": "Efficient Long Context Language Model Retrieval with Compression",
    "relevancy_score": 8,
    "authors": [
      "Minju Seo",
      "Jinheon Baek",
      "Seongyun Lee",
      "Sung Ju Hwang"
    ]
  },
  {
    "abstract": "Although prevailing supervised and self-supervised learning (SSL)-augmented sequential recommendation (SeRec) models have achieved improved performance with powerful neural network architectures, we argue that they still suffer from two limitations: (1) Preference Drift, where models trained on past data can hardly accommodate evolving user preference; and (2) Implicit Memory, where head patterns dominate parametric learning, making it harder to recall long tails. In this work, we explore retrieval augmentation in SeRec, to address these limitations. To this end, we propose a Retrieval-Augmented Sequential Recommendation framework, named RaSeRec, the main idea of which is to maintain a dynamic memory bank to accommodate preference drifts and retrieve relevant memories to augment user modeling explicitly. It consists of two stages: (i) collaborative-based pre-training, which learns to recommend and retrieve; (ii) retrieval-augmented fine-tuning, which learns to leverage retrieved memories. Extensive experiments on three datasets fully demonstrate the superiority and effectiveness of RaSeRec.",
    "reasons_for_relevancy": "Incorporates retrieval augmentation, relevant to RAG evaluation.",
    "title": "RaSeRec: Retrieval-Augmented Sequential Recommendation",
    "relevancy_score": 8,
    "authors": [
      "Xinping Zhao",
      "Baotian Hu",
      "Yan Zhong",
      "Shouzheng Huang",
      "Zihao Zheng",
      "Meng Wang",
      "Haofen Wang",
      "Min zhang"
    ]
  },
  {
    "abstract": "Benchmarking modern large language models (LLMs) on complex and realistic tasks is critical to advancing their development. In this work, we evaluate the factual accuracy and citation performance of state-of-the-art LLMs on the task of Question Answering (QA) in ambiguous settings with source citations. Using three recently published datasets-DisentQA-DupliCite, DisentQA-ParaCite, and AmbigQA-Cite-featuring a range of real-world ambiguities, we analyze the performance of two leading LLMs, GPT-4o-mini and Claude-3.5. Our results show that larger, recent models consistently predict at least one correct answer in ambiguous contexts but fail to handle cases with multiple valid answers. Additionally, all models perform equally poorly in citation generation, with citation accuracy consistently at 0. However, introducing conflict-aware prompting leads to large improvements, enabling models to better address multiple valid answers and improve citation accuracy, while maintaining their ability to predict correct answers. These findings highlight the challenges and opportunities in developing LLMs that can handle ambiguity and provide reliable source citations. Our benchmarking study provides critical insights and sets a foundation for future improvements in trustworthy and interpretable QA systems.",
    "reasons_for_relevancy": "Relevant due to its focus on evaluating large language models in tasks related to factual accuracy and citation, which aligns with interests in AI agents and QA systems.",
    "title": "Factuality or Fiction? Benchmarking Modern LLMs on Ambiguous QA with Citations",
    "relevancy_score": 8,
    "authors": [
      "Maya Patel",
      "Aditi Anand"
    ]
  },
  {
    "abstract": "With the widespread application of Large Language Models (LLMs) in the field of Natural Language Processing (NLP), enhancing their performance has become a research hotspot. This paper presents a novel multi-prompt ensemble decoding approach designed to bolster the generation quality of LLMs by leveraging the aggregation of outcomes from multiple prompts. Given a unique input $X$, we submit $n$ variations of prompts with $X$ to LLMs in batch mode to decode and derive probability distributions. For each token prediction, we calculate the ensemble probability by averaging the $n$ probability distributions within the batch, utilizing this aggregated probability to generate the token. This technique is dubbed Inner-Batch Ensemble. To facilitate efficient batch inference, we implement a Left-Padding strategy to maintain uniform input lengths across the n prompts. Through extensive experimentation on diverse NLP tasks, including machine translation, code generation, and text simplification, we demonstrate the efficacy of our method in enhancing LLM performance. The results show substantial improvements in BLEU scores, pass@$k$ rates, and LENS metrics over conventional methods.",
    "reasons_for_relevancy": "Focuses on AI agent optimization with ensemble decoding in LLMs, which is relevant for performance enhancement.",
    "title": "M-Ped: Multi-Prompt Ensemble Decoding for Large Language Models",
    "relevancy_score": 8,
    "authors": [
      "Jiaxin Guo",
      "Daimeng Wei",
      "Yuanchang Luo",
      "Shimin Tao",
      "Hengchao Shang",
      "Zongyao Li",
      "Shaojun Li",
      "Jinlong Yang",
      "Zhanglin Wu",
      "Zhiqiang Rao",
      "Hao Yang"
    ]
  },
  {
    "abstract": "The rise of LLMs has deflected a growing portion of human-computer interactions towards LLM-based chatbots. The remarkable abilities of these models allow users to interact using long, diverse natural language text covering a wide range of topics and styles. Phrasing these messages is a time and effort consuming task, calling for an autocomplete solution to assist users. We introduce the task of chatbot interaction autocomplete. We present ChaI-TeA: CHat InTEraction Autocomplete; An autcomplete evaluation framework for LLM-based chatbot interactions. The framework includes a formal definition of the task, coupled with suitable datasets and metrics. We use the framework to evaluate After formally defining the task along with suitable datasets and metrics, we test 9 models on the defined auto completion task, finding that while current off-the-shelf models perform fairly, there is still much room for improvement, mainly in ranking of the generated suggestions. We provide insights for practitioners working on this task and open new research directions for researchers in the field. We release our framework to serve as a foundation for future research.",
    "reasons_for_relevancy": "The paper focuses on LLM-based chatbots and introduces an evaluation framework, which aligns well with the interest in AI agents and relevant evaluations.",
    "title": "ChaI-TeA: A Benchmark for Evaluating Autocompletion of Interactions with LLM-based Chatbots",
    "relevancy_score": 8,
    "authors": [
      "Shani Goren",
      "Oren Kalinsky",
      "Tomer Stav",
      "Yuri Rapoport",
      "Yaron Fairstein",
      "Ram Yazdy",
      "Nachshon Cohen",
      "Alexander Libov",
      "Guy Kushilevitz"
    ]
  },
  {
    "abstract": "Retrieval-augmented generation systems rely on effective document retrieval capabilities. By design, conventional sparse or dense retrievers face challenges in multi-hop retrieval scenarios. In this paper, we present GeAR, which advances RAG performance through two key innovations: (i) graph expansion, which enhances any conventional base retriever, such as BM25, and (ii) an agent framework that incorporates graph expansion. Our evaluation demonstrates GeAR's superior retrieval performance on three multi-hop question answering datasets. Additionally, our system achieves state-of-the-art results with improvements exceeding 10% on the challenging MuSiQue dataset, while requiring fewer tokens and iterations compared to other multi-step retrieval systems.",
    "reasons_for_relevancy": "The paper is relevant as it directly addresses advancements in Retrieval-Augmented Generation (RAG) systems, aligning with the interest in RAG evaluation.",
    "title": "GeAR: Graph-enhanced Agent for Retrieval-augmented Generation",
    "relevancy_score": 8,
    "authors": [
      "Zhili Shen",
      "Chenxin Diao",
      "Pavlos Vougiouklis",
      "Pascual Merita",
      "Shriram Piramanayagam",
      "Damien Graux",
      "Dandan Tu",
      "Zeren Jiang",
      "Ruofei Lai",
      "Yang Ren",
      "Jeff Z. Pan"
    ]
  },
  {
    "abstract": "Large Language Models (LLMs) demonstrate remarkable capabilities, yet struggle with hallucination and outdated knowledge when tasked with complex knowledge reasoning, resulting in factually incorrect outputs. Previous studies have attempted to mitigate it by retrieving factual knowledge from large-scale knowledge graphs (KGs) to assist LLMs in logical reasoning and prediction of answers. However, this kind of approach often introduces noise and irrelevant data, especially in situations with extensive context from multiple knowledge aspects. In this way, LLM attention can be potentially mislead from question and relevant information. In our study, we introduce an Adaptive Multi-Aspect Retrieval-augmented over KGs (Amar) framework. This method retrieves knowledge including entities, relations, and subgraphs, and converts each piece of retrieved text into prompt embeddings. The Amar framework comprises two key sub-components: 1) a self-alignment module that aligns commonalities among entities, relations, and subgraphs to enhance retrieved text, thereby reducing noise interference; 2) a relevance gating module that employs a soft gate to learn the relevance score between question and multi-aspect retrieved data, to determine which information should be used to enhance LLMs' output, or even filtered altogether. Our method has achieved state-of-the-art performance on two common datasets, WebQSP and CWQ, showing a 1.9\\% improvement in accuracy over its best competitor and a 6.6\\% improvement in logical form generation over a method that directly uses retrieved text as context prompts. These results demonstrate the effectiveness of Amar in improving the reasoning of LLMs.",
    "reasons_for_relevancy": "This paper is relevant due to its focus on AI agents and the evaluation of Retrieval-Augmentation (RAG) methods to enhance LLM performance.",
    "title": "Harnessing Large Language Models for Knowledge Graph Question Answering via Adaptive Multi-Aspect Retrieval-Augmentation",
    "relevancy_score": 8,
    "authors": [
      "Derong Xu Xinhang Li",
      "Ziheng Zhang",
      "Zhenxi Lin",
      "Zhihong Zhu",
      "Zhi Zheng",
      "Xian Wu",
      "Xiangyu Zhao",
      "Tong Xu",
      "Enhong Chen"
    ]
  },
  {
    "abstract": "The growing ubiquity of Retrieval-Augmented Generation (RAG) systems in several real-world services triggers severe concerns about their security. A RAG system improves the generative capabilities of a Large Language Models (LLM) by a retrieval mechanism which operates on a private knowledge base, whose unintended exposure could lead to severe consequences, including breaches of private and sensitive information. This paper presents a black-box attack to force a RAG system to leak its private knowledge base which, differently from existing approaches, is adaptive and automatic. A relevance-based mechanism and an attacker-side open-source LLM favor the generation of effective queries to leak most of the (hidden) knowledge base. Extensive experimentation proves the quality of the proposed algorithm in different RAG pipelines and domains, comparing to very recent related approaches, which turn out to be either not fully black-box, not adaptive, or not based on open-source models. The findings from our study remark the urgent need for more robust privacy safeguards in the design and deployment of RAG systems.",
    "reasons_for_relevancy": "Relevant to RAG Evaluation and security aspects of RAG systems.",
    "title": "Pirates of the RAG: Adaptively Attacking LLMs to Leak Knowledge Bases",
    "relevancy_score": 7,
    "authors": [
      "Christian Di Maio",
      "Cristian Cosci",
      "Marco Maggini",
      "Valentina Poggioni",
      "Stefano Melacci"
    ]
  },
  {
    "abstract": "This paper presents a Multi-Agent Norm Perception and Induction Learning Model aimed at facilitating the integration of autonomous agent systems into distributed healthcare environments through dynamic interaction processes. The nature of the medical norm system and its sharing channels necessitates distinct approaches for Multi-Agent Systems to learn two types of norms. Building on this foundation, the model enables agents to simultaneously learn descriptive norms, which capture collective tendencies, and prescriptive norms, which dictate ideal behaviors. Through parameterized mixed probability density models and practice-enhanced Markov games, the multi-agent system perceives descriptive norms in dynamic interactions and captures emergent prescriptive norms. We conducted experiments using a dataset from a neurological medical center spanning from 2016 to 2020.",
    "reasons_for_relevancy": "Related to multi-agent systems, relevant to AI Agents.",
    "title": "Multi-Agent Norm Perception and Induction in Distributed Healthcare",
    "relevancy_score": 7,
    "authors": [
      "Chao Li",
      "Olga Petruchik",
      "Elizaveta Grishanina",
      "Sergey Kovalchuk"
    ]
  },
  {
    "abstract": "Interactive Recommendation (IR) has gained significant attention recently for its capability to quickly capture dynamic interest and optimize both short and long term objectives. IR agents are typically implemented through Deep Reinforcement Learning (DRL), because DRL is inherently compatible with the dynamic nature of IR. However, DRL is currently not perfect for IR. Due to the large action space and sample inefficiency problem, training DRL recommender agents is challenging. The key point is that useful features cannot be extracted as high-quality representations for the recommender agent to optimize its policy. To tackle this problem, we propose Contrastive Representation for Interactive Recommendation (CRIR). CRIR efficiently extracts latent, high-level preference ranking features from explicit interaction, and leverages the features to enhance users' representation. Specifically, the CRIR provides representation through one representation network, and refines it through our proposed Preference Ranking Contrastive Learning (PRCL). The key insight of PRCL is that it can perform contrastive learning without relying on computations involving high-level representations or large potential action sets. Furthermore, we also propose a data exploiting mechanism and an agent training mechanism to better adapt CRIR to the DRL backbone. Extensive experiments have been carried out to show our method's superior improvement on the sample efficiency while training an DRL-based IR agent.",
    "reasons_for_relevancy": "Discusses IR agents and DRL, touching upon AI agent creation.",
    "title": "Contrastive Representation for Interactive Recommendation",
    "relevancy_score": 7,
    "authors": [
      "Jingyu Li",
      "Zhiyong Feng",
      "Dongxiao He",
      "Hongqi Chen",
      "Qinghang Gao",
      "Guoli Wu"
    ]
  },
  {
    "abstract": "The performance of Large Language Models (LLMs) is based on the quality of the prompts and the semantic and structural integrity information of the input data. However, current prompt generation methods primarily focus on generating prompts for clean input data, often overlooking the impact of perturbed inputs on prompt performance. To address this limitation, we propose BATprompt (By Adversarial Training prompt), a novel method for prompt generation designed to withstand input perturbations (such as typos in the input). Inspired by adversarial training techniques, BATprompt demonstrates strong performance on a variety of perturbed tasks through a two-step process: adversarial perturbation and iterative optimization on unperturbed input via LLM. Unlike conventional adversarial attack methods, BATprompt avoids reliance on real gradients or model parameters. Instead, it leverages the advanced reasoning, language understanding and self reflection capabilities of LLMs to simulate gradients, guiding the generation of adversarial perturbations and optimizing prompt performance. In our experiments, we evaluate BATprompt on multiple datasets across both language understanding and generation tasks. The results indicate that BATprompt outperforms existing prompt generation methods, delivering superior robustness and performance under diverse perturbation scenarios.",
    "reasons_for_relevancy": "Involves AI agent optimization through prompt techniques relevant to LLM performance.",
    "title": "Robustness-aware Automatic Prompt Optimization",
    "relevancy_score": 7,
    "authors": [
      "Zeru Shi",
      "Zhenting Wang",
      "Yongye Su",
      "Weidi Luo",
      "Fan Yang",
      "Yongfeng Zhang"
    ]
  },
  {
    "abstract": "This paper presents a comprehensive overview of the first edition of the Academic Essay Authenticity Challenge, organized as part of the GenAI Content Detection shared tasks collocated with COLING 2025. This challenge focuses on detecting machine-generated vs. human-authored essays for academic purposes. The task is defined as follows: \"Given an essay, identify whether it is generated by a machine or authored by a human.'' The challenge involves two languages: English and Arabic. During the evaluation phase, 25 teams submitted systems for English and 21 teams for Arabic, reflecting substantial interest in the task. Finally, seven teams submitted system description papers. The majority of submissions utilized fine-tuned transformer-based models, with one team employing Large Language Models (LLMs) such as Llama 2 and Llama 3. This paper outlines the task formulation, details the dataset construction process, and explains the evaluation framework. Additionally, we present a summary of the approaches adopted by participating teams. Nearly all submitted systems outperformed the n-gram-based baseline, with the top-performing systems achieving F1 scores exceeding 0.98 for both languages, indicating significant progress in the detection of machine-generated text.",
    "reasons_for_relevancy": "Discusses AI agents in the form of essay detection models that involve transformer and LLMs.",
    "title": "GenAI Content Detection Task 2: AI vs. Human -- Academic Essay Authenticity Challenge",
    "relevancy_score": 7,
    "authors": [
      "Shammur Absar Chowdhury",
      "Hind Almerekhi",
      "Mucahid Kutlu",
      "Kaan Efe Keles",
      "Fatema Ahmad",
      "Tasnim Mohiuddin",
      "George Mikros",
      "Firoj Alam"
    ]
  },
  {
    "abstract": "In this paper, we explore the foundational mechanisms of memorization and generalization in Large Language Models (LLMs), inspired by the functional specialization observed in the human brain. Our investigation serves as a case study leveraging specially designed datasets and experimental-scale LLMs to lay the groundwork for understanding these behaviors. Specifically, we aim to first enable LLMs to exhibit both memorization and generalization by training with the designed dataset, then (a) examine whether LLMs exhibit neuron-level spatial differentiation for memorization and generalization, (b) predict these behaviors using model internal representations, and (c) steer the behaviors through inference-time interventions. Our findings reveal that neuron-wise differentiation of memorization and generalization is observable in LLMs, and targeted interventions can successfully direct their behavior.",
    "reasons_for_relevancy": "This paper delves into LLMs' memorization vs. generalization, relevant to the interest in AI agent functionalities and evaluations.",
    "title": "Think or Remember? Detecting and Directing LLMs Towards Memorization or Generalization",
    "relevancy_score": 7,
    "authors": [
      "Yi-Fu Fu",
      "Yu-Chieh Tu",
      "Tzu-Ling Cheng",
      "Cheng-Yu Lin",
      "Yi-Ting Yang",
      "Heng-Yi Liu",
      "Keng-Te Liao",
      "Da-Cheng Juan",
      "Shou-De Lin"
    ]
  },
  {
    "abstract": "Reasoning is critical for large language models (LLMs) to excel in a wide range of tasks. While methods like Chain-of-Thought (CoT) reasoning enhance LLM performance by decomposing problems into intermediate steps, they also incur significant overhead in token usage, leading to increased costs. We find that the reasoning process of current LLMs is unnecessarily lengthy and it can be compressed by including a reasonable token budget in the prompt, but the choice of token budget plays a crucial role in the actual compression effectiveness. We then propose a token-budget-aware LLM reasoning framework, which dynamically estimates token budgets for different problems based on reasoning complexity and uses the estimated token budgets to guide the reasoning process. Experiments show that our method effectively reduces token costs in CoT reasoning with only a slight performance reduction, offering a practical solution to balance efficiency and accuracy in LLM reasoning. Code: this https URL.",
    "reasons_for_relevancy": "The paper is relevant due to its exploration of reasoning in large language models (LLMs), tying into AI agent performance optimization.",
    "title": "Token-Budget-Aware LLM Reasoning",
    "relevancy_score": 7,
    "authors": [
      "Tingxu Han",
      "Chunrong Fang",
      "Shiyu Zhao",
      "Shiqing Ma",
      "Zhenyu Chen",
      "Zhenting Wang"
    ]
  }
]
# print(len(l))

import os
import timeit
from megaparse import MegaParse
from langchain_openai import ChatOpenAI
from megaparse.parser.megaparse_vision import MegaParseVision

# Function to be timed
def load_and_save_pdf():
    model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
    parser = MegaParseVision(model=model)
    megaparse = MegaParse(parser)
    response = megaparse.load("./rag.pdf")
    print(response)
    megaparse.save("./test.md")

# Time the execution of the function
execution_time = timeit.timeit(load_and_save_pdf, number=1)
print(f"Execution time: {execution_time} seconds")

