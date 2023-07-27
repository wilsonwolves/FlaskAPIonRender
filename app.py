#import flask
from flask import Flask, request, Response
import json

app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/detect-language', methods = ['POST'])
def detect_language():
    #sentence = request.args.get('sentence')
    sentence = request.form['sentence']
    return 'The detected language is: '+sentence
 
@app.route('/api/users', methods=['POST'])
def get_users():
    return {
        'users': [
            {
                'id': 1,
                'full_name': 'John M Doe',
                'first_name': 'John',
                'middle_name': 'M',
                'last_name': 'Doe',
                'email': 'JohnDoe@email.com',
                'status': 'active'
            }]
    }

#THIS WORKS TOO: curl -X POST -H "Content-Type: application/json" -d '{"sentence":"Hello World"}' http://localhost:5000/api/test
@app.route('/api/test', methods=['POST'])
def post_users():
    payload = request.json
    return {
        'data': [
            {
                'text': payload['sentence'],
                'first_name': 'John',
                'middle_name': 'M',
                'last_name': 'Doe'
            }]
    }

#THIS WORKS: 
@app.route('/update', methods=['post'])
def update_endpoint():
    payload = request.json  # payload should be {"title": "{KB title to update}", "input": "{text}"} 
    return Response(json.dumps({"status": "success"}), mimetype='application/json')

 
@app.route('/makeprofile', methods=['post'])
def update_endpoint():
    payload = request.json
    # get the industry,company,lastsales,currentprofile,addinfo values from the payload:
    industry = payload['industry']
    company = payload['company']
    lastsales = payload['lastsales']
    currentprofile = payload['currentprofile']
    addinfo = payload['addinfo']
    # put the industry,company,lastsales,currentprofile,addinfo values into a json response:
    json_response = json.dumps({"industry": industry, "company": company, "lastsales": lastsales, "currentprofile": currentprofile, "addinfo": addinfo})
    return Response(json_response, mimetype='application/json')




    
