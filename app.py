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

@app.route('/detect-language', methods = ['POST','GET'])
def detect_language():
    sentence = request.args.get('sentence')
    return 'The detected language is: '+sentence

@app.route('/api/users')
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


@app.route('/api/test', methods=['POST'])
def get_users():
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

@app.route('/update', methods=['post'])
def update_endpoint():
    payload = request.json  # payload should be {"title": "{KB title to update}", "input": "{text}"} 
    return Response(json.dumps({"status": "success"}), mimetype='application/json')

