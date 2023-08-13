#import flask
from flask import Flask, request, Response
import json
import os
from time import time, sleep
import yaml
import openai
from uuid import uuid4
import sys

openai.api_key = os.environ["OPENAI_API_KEY"]

# to fix issue with sqlite3:
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# used to be:
#import chromadb
#from chromadb.config import Settings

# instantiate ChromaDB
persist_directory = "asm/data" #"chromadb"
import chromadb
chroma_client = chromadb.PersistentClient(path=persist_directory)
#chroma_client = chromadb.Client(Settings(persist_directory=persist_directory,chroma_db_impl="duckdb+parquet",))
collection = chroma_client.get_or_create_collection(name="asm1")
#####################################################################

def save_yaml(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)
def open_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()
def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)
# gpt-3.5-turbo-0613
# gpt-3.5-turbo-16k-0613
# gpt-4
# gpt-4-0314
# gpt-4-0613
def chatbot(messages, model="gpt-3.5-turbo-0613", temperature=0):
    max_retry = 2
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            text = response['choices'][0]['message']['content']            
            return text, response['usage']['total_tokens']
        except Exception as oops:            
            if 'maximum context length' in str(oops):
                a = messages.pop(1)                
                continue
            retry += 1
            if retry >= max_retry:                
                exit(1)            
            sleep(2 ** (retry - 1) * 5)


def build_activitieslist(payload):
    system = 'Based on the provided customer information, especially focusing on the products they have purchased and their manufacturing processes, what are some potential industry activities they might be involved in?';
    messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': payload['preprofile']}]
    response, tokens = chatbot(messages)
    save_file('asm/data/log_%s_activities.txt' % time(), 'Updated document %s:\n%s' % (tokens,response))
    return response

def build_profile(payload):    
    system = 'You are a internet research specialist.  Your job is to review the company information and provide any additional information that you have about the company.  You will use the Company Name, Location, Industry and Manufacturing Process details to help you identify additional feedback about the company.  The [Product] section of the information represents products they have purchased to help inform their employees about the work the company does.  Your analysis should be thorough and comprehensive. If you do not have anything to contribute then respond with "I do not have any additional information about this company."'
    #system = system.replace('<<PREPROFILE>>', payload['preprofile'])
    #messages = [{'role': 'system', 'content': system}]
    messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': payload['preprofile']}]
    response, tokens = chatbot(messages) 
    #save_file('asm/root-asm-tmp.txt', 'subfolder test')    
    #save_file('asm/data/tmp.txt', response)    
    save_file('asm/data/log_%s_profile.txt' % time(), 'Updated document %s:\n%s' % (tokens,response))
    #dirfiles = os.listdir('asm/data/')
    # _files = os.listdir('asm/data/') 
    # for x_file in _files:
    #     # Check if the report already exists in the output folder
    #     filename = 'asm/data/' + x_file
    #     response += '\n\n' + filename

    return response

def get_productprofileindustries(payload):
    ALL_MESSAGES = list()
    # get the product description from the payload:
    product_description = payload['description']
    product_title = payload['title']
    #product_id = payload['product_id']
    systemtext = 'You are provided with a product TITLE and DESCRIPTION. Your job is to evaluate this product and determine which industries it belongs to. The output should be a list of industries.  Do not provide additional comments or explanations.  Just provide the list of industries that would utilize this product.'
    usertext = '##TITLE: <<PRODUCTTITLE>>. \n##DESCRIPTION: <<PRODUCTDESCRIPTION>>.'
    usertext = usertext.replace('<<PRODUCTTITLE>>', product_title)
    usertext = usertext.replace('<<PRODUCTDESCRIPTION>>', product_description)    
    messages = [{'role': 'system', 'content': systemtext},{'role': 'user', 'content': usertext}]
    response, tokens = chatbot(messages)  
    #save_file('asm/root-asm-tmp.txt', 'subfolder test')    
    #save_file('asm/data/tmp.txt', response)    
    save_file('asm/data/log_%s_product_industries.txt' % time(), 'Updated document %s:\n%s' % (tokens,response))
    #dirfiles = list()
    # put the files in the directory into a list:
    #dirfiles = os.listdir('asm/data/')
    _files = os.listdir('asm/data/') 
    for x_file in _files:
        # Check if the report already exists in the output folder
        filename = 'asm/data/' + x_file
        response += '\n\n' + filename
    return response 

# ---------------------------------------------------------------
# Flask API
# ---------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def index():
    return 'Gettin there!'

#---------------------------------------------------------------
# getproductprofileindustries
# parameters:  product_id, title, description
@app.route('/getproductprofileindustries', methods=['post'])
def getproductprofileindustries_endpoint():
    payload = request.json
    out = get_productprofileindustries(payload)
    # get the product description from the payload:
    # product_description = payload['description']    
    json_response = json.dumps({"data": out})
    return Response(json_response, mimetype='application/json')
       
#---------------------------------------------------------------
@app.route('/makeactivitieslist', methods=['post'])
def makeactivitieslist_endpoint():
    payload = request.json
    out = build_activitieslist(payload)
    json_response = json.dumps({"output": out})
    return Response(json_response, mimetype='application/json')

#---------------------------------------------------------------
@app.route('/makeprofile', methods=['post'])
def makeprofile_endpoint():
    payload = request.json
    out = build_profile(payload)
    # get the industry,company,lastsales,currentprofile,addinfo values from the payload:
    # industry = payload['industry']
    # company = payload['company']
    # lastsales = payload['lastsales']
    # currentprofile = payload['currentprofile']
    # addinfo = payload['addinfo']
    # put the industry,company,lastsales,currentprofile,addinfo values into a json response:
    #json_response = json.dumps({"industry": industry, "company": company, "lastsales": lastsales, "currentprofile": currentprofile, "addinfo": addinfo})
    json_response = json.dumps({"industry": out})
    return Response(json_response, mimetype='application/json')

#---------------------------------------------------------------
def doit():

    all_messages = list()
    # update main scratchpad
    if len(all_messages) > 5:
        all_messages.pop(0)        
    main_scratchpad = '\n\n'.join(all_messages).strip()


    # Update the knowledge base    
    if collection.count() == 0:
        # yay first KB!
        kb_convo = list()
        kb_convo.append({'role': 'system', 'content': open_file('system_instantiate_new_kb.txt')})
        kb_convo.append({'role': 'user', 'content': main_scratchpad})
        article = chatbot(kb_convo)
        new_id = str(uuid4())
        collection.add(documents=[article],ids=[new_id])
        #save_file('db_logs/log_%s_add.txt' % time(), 'Added document %s:\n%s' % (new_id, article))
    else:
        results = collection.query(query_texts=[main_scratchpad], n_results=1)
        kb = results['documents'][0][0]
        kb_id = results['ids'][0][0] 
        # Expand current KB
        kb_convo = list()
        kb_convo.append({'role': 'system', 'content': open_file('system_update_existing_kb.txt').replace('<<KB>>', kb)})
        kb_convo.append({'role': 'user', 'content': main_scratchpad})
        article = chatbot(kb_convo)
        collection.update(ids=[kb_id],documents=[article])
        #save_file('db_logs/log_%s_update.txt' % time(), 'Updated document %s:\n%s' % (kb_id, article)) 
        # Split KB if too large
        kb_len = len(article.split(' '))
        # if kb_len > 1000:
        #     kb_convo = list()
        #     kb_convo.append({'role': 'system', 'content': open_file('system_split_kb.txt')})
        #     kb_convo.append({'role': 'user', 'content': article})
        #     articles = chatbot(kb_convo).split('ARTICLE 2:')
        #     a1 = articles[0].replace('ARTICLE 1:', '').strip()
        #     a2 = articles[1].strip()
        #     collection.update(ids=[kb_id],documents=[a1])
        #     new_id = str(uuid4())
        #     collection.add(documents=[a2],ids=[new_id])
        #     save_file('db_logs/log_%s_split.txt' % time(), 'Split document %s, added %s:\n%s\n\n%s' % (kb_id, new_id, a1, a2))
    #chroma_client.persist()







###########################################################################
# Methods on Collection
# # change the name or metadata on a collection
# collection.modify(name="testname2")

# # get the number of items in a collection
# collection.count()

# # add new items to a collection
# # either one at a time
# collection.add(
#     embeddings=[1.5, 2.9, 3.4],
#     metadatas={"uri": "img9.png", "style": "style1"},
#     documents="doc1000101",
#     ids="uri9",
# )
# # or many, up to 100k+!
# collection.add(
#     embeddings=[[1.5, 2.9, 3.4], [9.8, 2.3, 2.9]],
#     metadatas=[{"style": "style1"}, {"style": "style2"}],
#     ids=["uri9", "uri10"],
# )
# collection.add(
#     documents=["doc1000101", "doc288822"],
#     metadatas=[{"style": "style1"}, {"style": "style2"}],
#     ids=["uri9", "uri10"],
# )

# # update items in a collection
# collection.update()

# # upsert items. new items will be added, existing items will be updated.
# collection.upsert(
#     ids=["id1", "id2", "id3", ...],
#     embeddings=[[1.1, 2.3, 3.2], [4.5, 6.9, 4.4], [1.1, 2.3, 3.2], ...],
#     metadatas=[{"chapter": "3", "verse": "16"}, {"chapter": "3", "verse": "5"}, {"chapter": "29", "verse": "11"}, ...],
#     documents=["doc1", "doc2", "doc3", ...],
# )

# # get items from a collection
# collection.get()

# # convenience, get first 5 items from a collection
# collection.peek()

# # do nearest neighbor search to find similar embeddings or documents, supports filtering
# collection.query(
#     query_embeddings=[[1.1, 2.3, 3.2], [5.1, 4.3, 2.2]],
#     n_results=2,
#     where={"style": "style2"}
# )

# # delete items
# collection.delete()
###########################################################################
###########################################################################
# You can include the embeddings when using get as followed:
# print(collection.get(include=['embeddings', 'documents', 'metadatas']))
    
# db1 = Chroma(
#     persist_directory=persist_directory1,
#     embedding_function=embeddings,
# )

# db2 = Chroma(
#     persist_directory=persist_directory2,
#     embedding_function=embeddings,
# )

# db2_data=db2._collection.get(include=['documents','metadatas','embeddings'])
# db1._collection.add(
#      embeddings=db2_data['embeddings'],
#      metadatas=db2_data['metadatas'],
#      documents=db2_data['documents'],
#      ids=db2_data['ids']
# )
# Langchain Chroma's default get() does not include embeddings, so calling collection.get through chromadb and asking for embeddings is necessary.
###########################################################################
# import chromadb
# # setup Chroma in-memory, for easy prototyping. Can add persistence easily!
# client = chromadb.Client()

# # Create collection. get_collection, get_or_create_collection, delete_collection also available!
# collection = client.create_collection("all-my-documents")

# # Add docs to the collection. Can also update and delete. Row-based API coming soon!
# collection.add(
#     documents=["This is document1", "This is document2"], # we handle tokenization, embedding, and indexing automatically. You can skip that and add your own embeddings as well
#     metadatas=[{"source": "notion"}, {"source": "google-docs"}], # filter on these!
#     ids=["doc1", "doc2"], # unique for each doc
# )

# # Query/search 2 most similar results. You can also .get by id
# results = collection.query(
#     query_texts=["This is a query document"],
#     n_results=2,
#     # where={"metadata_field": "is_equal_to_this"}, # optional filter
#     # where_document={"$contains":"search_string"}  # optional filter
# )








# # import chromadb and create a client
# import chromadb

# client = chromadb.Client()
# collection = client.create_collection("my-collection")
# # add the documents in the db
# collection.add(
#     documents=["This is a document about cat", "This is a document about car",
#      "This is a document about bike"],
#     metadatas=[{"category": "animal"}, {"category": "vehicle"}, 
#     {"category": "vehicle"}],
#     ids=["id1", "id2","id3"]
# )

# # add the documents in the db
# collection.add(
#     documents=["This is a document about cat", "This is a document about car",
#      "This is a document about bike"],
#     metadatas=[{"category": "animal"}, {"category": "vehicle"}, 
#     {"category": "vehicle"}],
#     ids=["id1", "id2","id3"]
# )

# # ask the querying to retrieve the data from DB
# results = collection.query(
#     query_texts=["vehicle"],
#     n_results=1
# )

# ------------------------------[Results]-------------------------------------
# {'ids': [['id2']],
#  'embeddings': None,
#  'documents': [['This is a document about car']],
#  'metadatas': [[{'category': 'vehicle'}]],
#  'distances': [[0.8069301247596741]]}











# # import files from the pets folder to store in VectorDB
# import os

# def read_files_from_folder(folder_path):
#     file_data = []

#     for file_name in os.listdir(folder_path):
#         if file_name.endswith(".txt"):
#             with open(os.path.join(folder_path, file_name), 'r') as file:
#                 content = file.read()
#                 file_data.append({"file_name": file_name, "content": content})

#     return file_data

# folder_path = "/content/pets"
# file_data = read_files_from_folder(folder_path)

# # get the data from file_data and create chromadb collection
# documents = []
# metadatas = []
# ids = []

# for index, data in enumerate(file_data):
#     documents.append(data['content'])
#     metadatas.append({'source': data['file_name']})
#     ids.append(str(index + 1))

# # create a collection of pet files 
# pet_collection = client.create_collection("pet_collection")

# # Add files to the chromadb collection
# pet_collection.add(
#     documents=documents,
#     metadatas=metadatas,
#     ids=ids
# )

# # query the database to get the answer from vectorized data
# results = pet_collection.query(
#     query_texts=["What is the Nutrition needs of the pet animals?"],
#     n_results=1
# )

# results






#     Using Different Embedding Models

# # import the sentence transformers
# from sentence_transformers import SentenceTransformer

# model = SentenceTransformer('paraphrase-MiniLM-L3-v2')

# documents = []
# embeddings = []
# metadatas = []
# ids = []

# # enumerate through file_data to collection each document and metadata
# for index, data in enumerate(file_data):
#     documents.append(data['content'])
#     embedding = model.encode(data['content']).tolist()
#     embeddings.append(embedding)
#     metadatas.append({'source': data['file_name']})
#     ids.append(str(index + 1))

# # create the new chromaDB and use embeddings to add and query data
# pet_collection_emb = client.create_collection("pet_collection_emb")

# # add the pets files into the pet_collection_emb database
# pet_collection_emb.add(
#     documents=documents,
#     embeddings=embeddings,
#     metadatas=metadatas,
#     ids=ids
# )

# # write text query and submit to the collection 
# query = "What are the different kinds of pets people commonly own?"
# input_em = model.encode(query).tolist()

# results = pet_collection_emb.query(
#     query_embeddings=[input_em],
#     n_results=1
# )
# results






# Embeddings Supported in ChromaDB
# ChromaDB supports sentence transformers models, OpenAI APIs, and Cohere or any other OS model to store embeddings.

# Sentence Transformer Embeddings
# # loading any model from sentence transformer library
# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
# model_name="all-MiniLM-L6-v2")



# OpenAI Models
# ChromaDB provides a wrapper function to use any embedding model API from OpenAI for AI applications

# # function to call OpenAI embeddings
# openai_ef = embedding_functions.OpenAIEmbeddingFunction(
#                 api_key="YOUR_API_KEY",
#                 model_name="text-embedding-ada-002"
#             )
