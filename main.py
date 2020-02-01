from google.cloud import vision
from flask import Flask, render_template, request

app = Flask(__name__)

# Create vision Product Search Client
client = vision.ProductSearchClient()

@app.route('/')
def home():


    return render_template('index.html')

@app.route('/upload')
def upload():
    image = request.files['file']
    session['file'] =

