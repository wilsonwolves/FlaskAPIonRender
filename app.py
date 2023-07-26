#import flask
from flask import Flask, request, jsonify
import threading
import json

app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/detect-language')
def detect_language():
    sentence = request.args.get('sentence')
    return 'The detected language is: '+sentence