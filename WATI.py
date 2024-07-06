from io import BytesIO
import requests
import os
import PyPDF2
import mongoDB as mdb
import operations as op
import bson
import base64

import openai
from dotenv import load_dotenv
from dotenv import dotenv_values
import os
load_dotenv()

openai.organization = os.environ['org']
openai.api_key = os.environ['api_key']


def read_pdf(fname):
    """
    This function reads the pdf file and extracts the text from it.

    Parameters:
    fname (str): Name of the pdf file

    Returns:
    text_ext (list): List of extracted text from the pdf file
    """
    reader = PyPDF2.PdfReader(fname)
    text_ext = []
    for i in range(len(reader.pages)):
        pageObj = reader.pages[i]
        # extracting text from page
        text_ext.append(pageObj.extract_text())

    return text_ext


def get_media(url, senderID):
    # url =

    headers = {
        'Authorization': os.getenv("API"),
    }

    response = requests.request(
        "GET", url, headers=headers)

    # print(len(response.content))
    # print(response.text.content)
    try:
        # print(response.content[:5])
        text_ext = []
        # response = requests.get(url)
        my_raw_data = response.content
        # print("my_raw_data ", response.content)

        with BytesIO(my_raw_data) as data:
            read_pdf = PyPDF2.PdfReader(data)

            for page in range(len(read_pdf.pages)):
                pageObj = read_pdf.pages[page]
                # print(pageObj)
                # extracting text from page
                text_ext.append(pageObj.extract_text())
            # print("text_ext ", text_ext[:500])

            file_content = mdb.store_text(text_ext, senderID)

        # with open("file_"+senderID+".pdf", "wb") as file:
        #     print("Writing to file")
        #     content = mdb.store_text(response.content, senderID)
        #     # print("content[:50] ", content[:50])
        #     # file.write(response.content)
        return file_content
    except Exception as e:
        print(e)


# read_pdf("https://live-server-8076.wati.io/api/file/showFile?fileName=data/documents/03d63ab5-c503-411f-bb94-10a932e29683.pdf")

def sendText(text, senderID):
    import requests

    url = "https://"+os.getenv("URL")+"/api/v1/sendSessionMessage/"+senderID

    headers = {"Authorization": os.getenv("API")}

    body = {'messageText': text}

    response = requests.post(url, headers=headers, data=body)

    # print(response.text)


# pdfFile = get_media(
#     "https://live-server-8076.wati.io/api/file/showFile?fileName=data/documents/cf661bad-218e-40f1-881b-efa7f5aef0c2.pdf", "918779171731")

# print("1. ", pdfFile)

# print(pdfFile[9:-2])
# uuid_str = pdfFile[9:-2]
# uuid_bytes = bytes.fromhex(uuid_str.replace('-', ''))
# binary_obj = bson.Binary(uuid_bytes, subtype=0)
# encoded_data = binary_obj.base64
# decoded_data = base64.b64decode(encoded_data.encode('utf-8'))

# print(decoded_data)

# op.read_pdf(pdfFile)
# sendText("Hi", "918779171731")

# pdfFile = get_media(
#     "https://live-server-8076.wati.io/api/file/showFile?fileName=data/documents/cf661bad-218e-40f1-881b-efa7f5aef0c2.pdf", "918779171731")
# print("pdfFile ", type(pdfFile))
# # if pdfFile == 'Success':
# print("2. ", pdfFile[:5])
# pdfFile = " ".join(pdfFile)
# sent_toks = op.sent_tokenize(pdfFile)
# print("sent_toks ", sent_toks)
# # concat_list = [j for i in sent_toks for j in i]
# # print("2. sent_toks ", concat_list)
# embeddings = op.create_content_embeddings(sent_toks)
# query = "Give the introduction of the book"
# query_embedding = op.create_query_embeddings(query)
# cosine_lis = op.calculate_cosine(
#     query_embedding, embeddings, sent_toks)
# indexes_final = op.fetch_top_rank_ans(cosine_lis, 5)
# prompt = op.fetch_most_relevant(
#     indexes_final, sent_toks, cosine_lis, query)
# print("prompt ", prompt)
