from flask import Flask, render_template, request, logging, redirect

from google.cloud import storage
from google.protobuf.json_format import MessageToDict

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
UPLOADED = 'processed_pic'
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods = ['POST'])
def upload_image():
    if request.method == 'POST':
        file = request.files['fileToUpload']
        if file:
            file.save(UPLOADED)
            return redirect('/process')
    return render_template('index.html')


@app.route('/process')
def process():
    # filename = PREFIX + session.get('file', None)


    products = bt.get_similar_products_file(PROJ_ID, LOCATION, PROD_SET_ID, PROD_CAT, UPLOADED, "")
    products.sort(key=lambda x : -x.score)
    res = products[0:3]
    for x in range(3):
        res[x].product.name = res[x].product.name[res[x].product.name.rfind('/')+1:]
    print(res[0].product.name)
    return render_template('output.html', product_list=res)


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