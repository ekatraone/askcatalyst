import pymongo
import gridfs
import numpy as np
from bson import ObjectId


def store_text(large_text, senderID):
    client = pymongo.MongoClient(
        "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")

    db = client["nlp_files"]
    collection = db["pdf-files"]
    # encoded_data = base64.b64encode(large_text)

    doc = {
        "userID": senderID,
        "text": large_text}
    collection.update_one({"_id": 1}, {"$set": doc}, upsert=True)

    result = collection.find_one({"text": large_text})

    # decoded_data = base64.b64decode(result['text'])
    # print("encoded_data ", decoded_data[:500])
    # print(result['text'])
    return result['text']


def retrieve_npy_file():
    client = pymongo.MongoClient(
        "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
    db = client["trained_documents"]
    collection = db["catalyst_SCI"]

    # create a GridFS object for the database
    fs = gridfs.GridFS(db)
    # file_id = 'ObjectId(640ef255dbe077e09b7c553a)'

    doc = collection.find_one({'filename': 'catalyst_SCI.npy'})
    # print(doc)
    file_id = ObjectId(doc['file_id'])

    gridout = fs.get(file_id)

    binary_data = gridout.read()

    arr = np.frombuffer(binary_data, dtype=np.float32)

    embeddings_arr = arr.reshape((26695, 384))

    return embeddings_arr


def retrieve_list():
    client = pymongo.MongoClient(
        "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
    db = client["trained_documents"]
    collection = db["catalyst_SCI"]

    doc = collection.find_one({'filename': 'catalyst_SCI.npy'})
    # print(doc)
    concat_list = doc['concat_list']
    # print(doc['concat_list'])

    return concat_list


def create_record(phone, name):
    try:
        client = pymongo.MongoClient(
            "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
        db = client["trained_documents"]
        collection = db["catalyst_users"]

        user_data = {"userID": phone, "name": name,
                     "status": "open", "chat_log": []}
        updated_status = {"$set": {"status": "open"}}

        result = collection.update_one(user_data, updated_status, upsert=True)

        if result.upserted_id:
            print("New record created.")

        else:
            print("Record updated.")
        return "Success"
    except Exception as e:
        print("create_record error", e)


def find_user(senderID):
    try:
        client = pymongo.MongoClient(
            "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
        db = client["trained_documents"]
        collection = db["catalyst_users"]

        query = {"userID": senderID}

        # print("query ", collection.find_one(query))
        return collection.find_one(query)

    except Exception as e:
        print("find_user error", e)


def chat_log(userID, query, answer):
    client = pymongo.MongoClient(
        "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
    db = client["trained_documents"]
    collection = db["catalyst_users"]

    user_data = {"userID": userID}
    chat_log = {
        "$push": {"chat_log": "\nQ: " + query + "\nA: " + answer}}

    result = collection.update_one(user_data, chat_log, upsert=True)


def check_status(userID):
    client = pymongo.MongoClient(
        "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
    db = client["trained_documents"]
    collection = db["catalyst_users"]
    doc = collection.find_one({'userID': userID})

    if doc:
        status = doc['status']
    else:
        status = "No document found."
        print("No document found.")
    # print(doc['concat_list'])

    return status


def retrieve_last_five(userID):
    client = pymongo.MongoClient(
        "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
    db = client["trained_documents"]
    collection = db["catalyst_users"]
    doc = collection.find_one({'userID': userID})

    chat_log = {"chat_log": {"$slice": -5}}

    result = collection.find_one(doc, chat_log)
    if result:
        # print(result["chat_log"])
        return result.get("chat_log", "No document found.")
    else:
        print("No document found.")


def update_chat_status(phone, status):
    try:
        client = pymongo.MongoClient(
            "mongodb+srv://root:root@cluster0.m3gwy.mongodb.net/?retryWrites=true&w=majority")
        db = client["trained_documents"]
        collection = db["catalyst_users"]

        user_data = {"userID": phone}
        updated_status = {"$set": {"status": status}}

        collection.update_one(user_data, updated_status, upsert=True)
        # print("update_chat_status ", r)
    except Exception as e:
        print("update_chat_status error", e)
