#import flask
from flask import Flask
import threading
from flask import request
import json

app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'