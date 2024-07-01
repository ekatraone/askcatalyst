from dotenv import dotenv_values
from dotenv import load_dotenv
import sys
from numpy.linalg import norm
import numpy as np
from sentence_transformers import SentenceTransformer
import PyPDF2
import nltk
import mongoDB as mdb
# import WATI as wa
import os
from nltk.tokenize import sent_tokenize
import openai
nltk.download('punkt')
sys.setrecursionlimit(5500)

load_dotenv()


# config = dotenv_values(".env")

# openai.organization = config['org']
# openai.api_key = config['api_key']

openai.organization = os.environ['org']
openai.api_key = os.environ['api_key']

# openai.organization = os.getenv("OPENAI_ORG")
# openai.api_key = os.getenv("OPENAI_KEY")


def read_pdf(text_ext):
    """
    This function reads the pdf file and extracts the text from it.

    Parameters:
    fname (str): Name of the pdf file

    Returns:
    text_ext (list): List of extracted text from the pdf file
    """
    # pdfFileObj = open(fname, 'rb')
    # reader = PyPDF2.PdfReader(pdfFileObj)
    # text_ext = []
    # print(len(reader.pages))
    # for i in range(len(reader.pages)):
    #     pageObj = reader.pages[i]
    #     # print(pageObj)
    #     # extracting text from page
    #     text_ext.append(pageObj.extract_text())
    # print("text_ext ", text_ext[:500])
    return text_ext


def tokenize_sent(text_ext):
    """
    This function apply sent_tokenize to the text and stores the result in a list.

    Parameters:
    text_ext (list): List of extracted text from the pdf file

    Returns:
    sent_toks (list): List of tokenized sentences
    """
    sent_toks = []

    for i in text_ext:
        sent_toks.append(sent_tokenize(i))
    # print("len(sent_toks) ", len(sent_toks))

    return sent_toks


def create_content_embeddings(concat_list):
    """
    This function creates embeddings for the document sentences.

    Parameters:
    concat_list (list): List of tokenized sentences

    Returns:
    embeddings (list): List of embeddings of the sentences
    """
    print("3")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(concat_list)

    return embeddings


def create_query_embeddings(query_text):
    """
    This function creates embeddings for the query.
    Parameters:
    query_text (str): Query entered by the user

    Returns:
    query_embedding (list): List of embeddings of the query
    """

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    query_embedding = model.encode(query_text)
    return query_embedding


def calculate_cosine(query_embedding, embeddings, concat_list):
    """

    This function calculates cosine similarity between the query and the sentences.

    Parameters:
    query_embedding (list): List of embeddings of the query
    embeddings (list): List of embeddings of the sentences
    concat_list (list): List of tokenized sentences

    Returns:
    cosine_lis (list): List of cosine similarity values
    """
    cosine_lis = []

    for i in range(len(concat_list)):
        cosine = np.dot(query_embedding,
                        embeddings[i]) / (norm(query_embedding)*norm(embeddings[i]))
        cosine_lis.append(cosine)

    # print("cosine_lis ", cosine_lis)
    return (cosine_lis)


def fetch_top_rank_ans(cosine_lis, N):
    """
    This function fetches the top N ranked sentences.

    Parameters:
    cosine_lis (list): List of cosine similarity values
    N (int): Number of sentences to be ranked

    Returns:
    indexes_final (list): List of top N ranked sentences
    """

    list1 = cosine_lis
    indexes_final = sorted(
        range(len(list1)), key=lambda i: list1[i], reverse=True)[:N]

    print("indexes_final ", indexes_final)
    indices = range(len(list1))

    sorted_indices = sorted(indices, key=lambda i: list1[i], reverse=True)
# print(sorted_indices)
    indexes_final = []
    for i in range(N):
        indexes_final.append(sorted_indices[i])
    len(indexes_final)
    return indexes_final


def fetch_most_relevant(indexes_final, concat_list, list1, query, chat_log):
    """
    This function fetches the most relevant sentences, pass it as a context to GPT-3 prompt along with user's query.

    Parameters:
    indexes_final (list): List of top N ranked sentences
    concat_list (list): List of tokenized sentences
    list1 (list): List of cosine similarity values
    query (str): Query entered by the user

    Returns:
    prompt (str): GPT-3 prompt
    """

    try:
        dicts = {}

        keys = indexes_final
        for i in keys:
            dicts[i] = concat_list[i]

        most_relevant_document_sections = [dicts]

        len(most_relevant_document_sections)

        chosen_sections = []
        chosen_sections_len = 0
        chosen_sections_indexes = []

        indices = range(len(list1))
        sorted_indices = sorted(indices, key=lambda i: list1[i], reverse=True)

        # print(len(indexes_final))

        for section_index in range(len(indexes_final)):

            if chosen_sections_len > 500:
                break
            chosen_sections.append(
                concat_list[sorted_indices[section_index]].replace("\n", " "))
            chosen_sections_indexes.append(str(section_index))

        # Useful diagnostic information
        print(f"Selected {len(chosen_sections)} document sections:")

        header = """You are a Catalyst AI, and you are here to help answer any questions related to only Catalyst 2030, social entrepreneurship, innovators, SDGs and the context provided. Catalyst 2030 is a global movement of social entrepreneurs and innovators, launched at the World Economic Forum in 2020. Our mission is to catalyze collaboration across sectors to unleash collective potential for global systems change, and our vision is to achieve the Sustainable Development Goals (SDGs) by 2030 through an unprecedented mobilization of social entrepreneurs, partners, and resources. Our core values include placing people and nature at the center of everything we do, having a co-creative mindset, collaborative leadership, humble audacity, and a spirit of generosity. You are here to help answer any questions you have about our mission, values, and how we work towards achieving the SDGs.. and if the answer is not contained within the text below, say "I don't have that information"\n\nContext:\n"""

        # print(query)
        prompt = header + "".join(chosen_sections) + "\n\nQ: " + query + "\nA:"
        return prompt
    except Exception as e:
        print("Error in prompt ", e)


def process_main(senderID, query, embeddings, concat_list):

    query_embedding = create_query_embeddings(query)
    # print(query_embedding)
    cosine_lis = calculate_cosine(
        query_embedding, embeddings, concat_list)
    # print(cosine_lis)
    indexes_final = fetch_top_rank_ans(cosine_lis, 5)
    print("indexes_final ", indexes_final)

    chat_log = mdb.retrieve_last_five(senderID)
    # print(chat_log)

    prompt = fetch_most_relevant(
        indexes_final, concat_list, cosine_lis, query, chat_log)
    # print("prompt ", prompt)

    response_openai = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a Catalyst AI, and you are here to help answer any questions related to only Catalyst 2030, social entrepreneurship, innovators, SDGs and the context provided"},
            {"role": "user", "content": prompt}


        ],
        max_tokens=350
    )
    ans = response_openai['choices'][0].message.content
    print("response ", response_openai['choices'][0].message.content, "\n")
    return ans
