#import flask
from flask import Flask, request, Response
import json
import os
from time import time, sleep
import openai
openai.api_key = os.environ["OPENAI_API_KEY"]

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
    return json.loads(response)


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
    return Response(out, mimetype='application/json')




    
