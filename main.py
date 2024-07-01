# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.

from flask import Flask, request, jsonify, after_this_request
import threading

import WATI as wa
import operations as op
import openai
import pymongo
from dotenv import load_dotenv
from dotenv import dotenv_values
from concurrent.futures import ThreadPoolExecutor
import asyncio

import os
import mongoDB as mdb
import json
load_dotenv()

# config = dotenv_values(".env")

# openai.organization = config['org']
# openai.api_key = config['api_key']

openai.organization = os.environ['org']
openai.api_key = os.environ['api_key']

# openai.api_key = os.environ['api_key']
# openai.organization = os.environ['org']
# openai.api_key = os.environ['api_key']


# print("openai.organization ", openai.organization)

# Flask constructor takes the name of
# current module (__name__) as argument.
# run_with_ngrok(app)

# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.
# st.title("Ekatra QnA")

app = Flask(__name__)
# Adjust max_workers as needed


# @app.route('/')
# def hello():
#     return 'Webhooks with Python'

def init_mongo():
    client = pymongo.MongoClient(
        "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
    db = client["trained_documents"]
    collection = db["catalyst_SCI"]


async def async_task(data):
    # if bool(data):
    # await asyncio.sleep(3)
    print("WATI Payload ", data, "\n")
    senderID = data['waId']
    name = data['senderName']
    # if (data['text'] == 'hi'):
    #     wa.sendText("Hello", senderID)
    if data['text'] != None:
        if data['text'].lower() == 'ask catalyst':

            existing_record = mdb.find_user(senderID)
            if existing_record:
                print("1. existing_record")
                mdb.update_chat_status(senderID, "open")
                wa.sendText("""Welcome to Ask Catalyst! Our AI assistant, powered by Mobius, is here to help you navigate the world of social entrepreneurship and innovation.

As an NLP model trained on the Catalyst 2030 knowledge base, we can provide answers and insights for any questions you might have related to Catalyst or social entrepreneurship in general.

So go ahead, simply type in your question and we'll do our best to provide you with a helpful response. Let's explore the world of social entrepreneurship together!""", senderID)
            else:
                print("2. existing_record ")
                record_created = mdb.create_record(senderID, name)
                print("record_created ", record_created)

                if record_created == "Success":
                    wa.sendText("""Welcome to Ask Catalyst! Our AI assistant, powered by Mobius, is here to help you navigate the world of social entrepreneurship and innovation.

As an NLP model trained on the Catalyst 2030 knowledge base, we can provide answers and insights for any questions you might have related to Catalyst or social entrepreneurship in general.

So go ahead, simply type in your question and we'll do our best to provide you with a helpful response. Let's explore the world of social entrepreneurship together!""", senderID)

        else:
            options = ["Start Day", "Let's Begin", "Yes, Next", "Continue", "Next", "Skip", "Ste-by-Step", "Start Now", "No, give me sometime", "Remind me later", "Yes, I would", "No, I’ll pass", "Okay, Next", "WomenWill", "Start WomenWill", "I am ready.", "No, I am not ready.", "WomenWill Program", "शुरू करें", "Track Registration", "Event Updates", "Invite your friends", "Yes, I have", "IT Track", "Social Track", "Education Track", "Yes", "No", "Ok", "Ekatra QnA Bot", "Hi", 'Hello, tell me about Ekatra QnA Bot', ".", "Hi", "Hello", "Hey", "Learn with ekatra", "ekatra demo", "?", "!", "?*", "!*", "Hey ekatra,\nTell me about Ask YC!",
                       "Neo update 2023", "Tell me more", "Good News!", "Start Upscale", "It's correct", "Yes, I would like to", "Yes, Update", "Start Course", "No, I'll pass.", "Chat with an AI", "Hello, tell me about ekatra", "MDLZ Next", "Knowledge Base", "MDLZ Mobius Chat", "Start MDLZ", "Mondelēz", "Yes, Let's do this!", "No, I'll pass.", "English", "Hindi", "Climate Change", "Entrepreneurship", "Day 1", "Start Course!", "What's New?", "Yes, Tell me!", "No, Not Interested", "Join the waitlist!", "That's exciting!", "Generate Course", "30 minutes", "1 hour", "2 hour", "About Mondelēz", "About Mondelez", "Hello, tell me about \"Financial Literacy Course\"", "Ask YC", "Hi, I'm interested in the Bachelor of Design program. Can you tell me more about it?", "Yes, Please.", "Sounds interesting", "Career Opportunities", "🙏🏻 How to apply?", "Ask TPH", "Financial Literacy", "Ekatra, Course Generate", "ask kernel", "Ekatra, Generate Course", "Hello, Tell me about FutureX Program"]

            keyword = data['text']
            keyword = keyword.lower()
            print(keyword, "tell me about ask yc!" in keyword,
                  "Hey ekatra,\nTell me about Ask YC!" == keyword)
            match = 0
            for option in options:
                if option.lower() == keyword or "Track" in keyword or "Invite" in keyword or "GNS" in keyword or "vnit" in keyword or "Global Nagpur Summit" in keyword or "Track" in keyword or len(keyword) == 1 or "hello, tell me about ekatra" in keyword or "tell me about ask yc!" in keyword:
                    match += 1
                    mdb.update_chat_status(senderID, "Closed")

            print("matched ", match)
            if (match == 0):

                status = mdb.check_status(senderID)
                print(status)

                if status == "open":
                    query = data['text']
                    content_embeddings = mdb.retrieve_npy_file()

                    # print(content_embeddings)
                    concat_list = mdb.retrieve_list()

                    ans = op.process_main(
                        senderID, query, content_embeddings, concat_list)
                    wa.sendText(ans, senderID)
                    mdb.chat_log(senderID, query, ans)
    else:
        print("Ok ", data)
    return "OK", 200

executor = ThreadPoolExecutor()


@app.route('/catalyst', methods=['POST', 'GET'])
async def process():
    print("1. In Process")
    data = request.json
    response_data = {'success': True}

    response = jsonify(response_data)

    # Create a ThreadPoolExecutor to run async_task concurrently
    # Create a ThreadPoolExecutor to run async_task concurrently
    def run_async_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_task(data))
        print(result)  # Do something with the result if needed

    # Submit the function to the thread pool for execution
    executor.submit(run_async_task)

    # Return the response immediately, without waiting for async_task to complete
    return response, 200
    # response = jsonify(response_data)

    # Create a ThreadPoolExecutor to run async_task concurrently
    # with ThreadPoolExecutor() as executor:
    #     # Submit the async_task to the ThreadPoolExecutor
    #     executor.submit(async_task, data)

    # loop = asyncio.get_event_loop()
    # task = loop.create_task(async_task(data))

    # You can continue processing here while the async_task runs in the background

    # await task  # Wait for the async_task to complete (optional)

    # return jsonify(response_data), 200


# test()
if __name__ == '__main__':
    from waitress import serve
    # port = int(os.environ.get("PORT", 4000))

    serve(app, host='0.0.0.0', port=4000)
    # app.run(debug=True, port=4000)
