import os
import json
import requests
import sys
from flask import Flask, request
from flask_cors import CORS

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

DATA_INGESTION_API_URL = "http://"+os.getenv("DATA_INGESTION_API_ADDRESS")+":"+os.getenv("DATA_INGESTION_API_PORT")
MESSAGE_ROUTER_API_URL = "http://"+os.getenv("MESSAGE_ROUTER_API_ADDRESS")+":"+os.getenv("MESSAGE_ROUTER_API_PORT")

app = Flask(__name__)
CORS(app)


@app.route('/device_state', methods=['GET', 'POST'])
def device_state():
    if request.method == 'POST':
        print("BACKEND POST", file=sys.stderr)
        params = request.get_json()
        print(params, file=sys.stderr)
        r = requests.post(
            MESSAGE_ROUTER_API_URL+"/device_state",
            json=params
        )
        return json.dumps(r.json()), r.status_code

    elif request.method == 'GET':
        print("BACKEND GET", file=sys.stderr)
        r = requests.get(DATA_INGESTION_API_URL+"/device_state")
        # print(json.dumps(r.json()), file=sys.stderr)
        return json.dumps(r.json()), r.status_code

    else:
        return "unexpected error in backend"


# it is paramount that this line be here, below the @app.route decorator (for some reason)
app.run(host=HOST, port=PORT, debug=True)
