from google.cloud import vision
from flask import Flask, render_template, request, logging, redirect
from google.cloud import storage

import os
import backtest as bt

CLOUD_STORAGE_BUCKET = 'uploaded-images-2020'
PREFIX = 'gs://test-fashion-data/'

app = Flask(__name__)
session = {}
# Create vision Product Search Client

PROJ_ID = "hack-sc-2020"
LOCATION = "us-west1"
PROD_SET_ID = "product-list"
PROD_CAT = "apparel-v2"
file_upload = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods = ['POST'])
def upload_image():
    file = request.files['fileToUpload'] # fileToUpload?

    session['file'] = file.filename

    # Create a Cloud Storage client.
    storage_client = storage.Client()

    # Get the bucket that the file will be uploaded to.
    bucket = storage_client.get_bucket(CLOUD_STORAGE_BUCKET)
    blob = bucket.blob(file.filename)

    blob.upload_from_file(file)
    blob.make_public()

    global file_upload
    file_upload = blob
    # Redirect to the home page.
    return redirect('/process')


@app.route('/process')
def process():
    # filename = PREFIX + session.get('file', None)

    if file_upload:
        products = bt.get_similar_products_remote(PROJ_ID, LOCATION, PROD_SET_ID, PROD_CAT, file_upload, "")
        session['products'] = []
        products.sort(key=lambda x : -x.score)
        res = products[:3]
        print(res)
        return render_template('index.html')

    return render_template('index.html')


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)