#import flask
from flask import Flask, request 

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