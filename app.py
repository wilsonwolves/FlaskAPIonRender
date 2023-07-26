import flask
#from flask import Flask
import threading
from flask import request
import json

app = flask.Flask(__name__)

@app.route('/askdirector', methods=['post'])
def askdirector_endpoint():
    payload = request.json   # payload should be {"input": "{text}"}    
    return flask.Response(json.dumps({"status": "success"}), mimetype='application/json')

@app.route('/test', methods=['post'])
def test_endpoint():
    payload = request.json   # payload should be {"input": "{text}"}    
    # return the payload as a response
    return flask.Response(json.dumps(payload), mimetype='application/json')

@app.route('/test2', methods=['post'])
def test_endpoint():
    payload = request.json   # payload should be {"input": "{text}"}    
    # return the payload as a response
    return payload
    


@app.route('/')
def hello_world():
    return 'Hello, World!'