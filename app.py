#import flask
from flask import Flask, request, Response
import json
import os
from time import time, sleep
import yaml
import openai
openai.api_key = os.environ["OPENAI_API_KEY"]
import chromadb
from chromadb.config import Settings
from uuid import uuid4

# instantiate ChromaDB
persist_directory = "chromadb"
chroma_client = chromadb.Client(Settings(persist_directory=persist_directory,chroma_db_impl="duckdb+parquet",))
collection = chroma_client.get_or_create_collection(name="knowledge_base")
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

def build_profile(payload):    
    system = 'Write a one page profile of a company in the <<INDUSTRY>> industry. The company is called <<COMPANY>>. The company has <<LASTSALES>> in sales. The company is <<CURRENTPROFILE>>. <<ADDINFO>>'
    system = system.replace('<<INDUSTRY>>', payload['industry'])
    system = system.replace('<<COMPANY>>', payload['company'])
    system = system.replace('<<LASTSALES>>', payload['lastsales'])
    system = system.replace('<<CURRENTPROFILE>>', payload['currentprofile'])
    system = system.replace('<<ADDINFO>>', payload['addinfo'])
    messages = [{'role': 'system', 'content': system}]    
    #messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': query}]
    response, tokens = chatbot(messages) 
    # test the asm/data path:
    save_file('asm/data/tmp.txt', response)    
    save_file('asm/data/log_%s_profile.txt' % time(), 'Updated document %s:\n%s' % (tokens,response))
    return response


app = Flask(__name__)

@app.route('/')
def index():
    return 'Gettin there!'


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
    chroma_client.persist()







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
