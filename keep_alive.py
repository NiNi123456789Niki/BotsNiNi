import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello from Flask!'

def keep_Alive():

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)