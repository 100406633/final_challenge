import os
import sys
from flask import Flask, request
from flask_cors import CORS
from data_ingestion import insert_device_state, get_device_state


HOST = os.getenv("HOST")
PORT = os.getenv("PORT")

app = Flask(__name__)
CORS(app)


@app.route('/device_state', methods=['GET', 'POST'])
def device_state():
    if request.method == 'POST':
        print("DATA INGESTION POST", file=sys.stderr)
        params = request.get_json()
        if len(params) != 4:
            return {"response": "Incorrect parameters"}, 401
        cursor = insert_device_state(params)
        return {"response": f"{cursor.rowcount} records inserted"}, 200

    elif request.method == 'GET':
        print("DATA INGESTION GET", file=sys.stderr)
        query = get_device_state()
        data = {i: {"room": query[i][0], "type": query[i][1], "value": query[i][2]}
                for i in range(len(query))}
        return data


# it is paramount that this line be here, below the @app.route decorator (for some reason)
app.run(host=HOST, port=PORT, debug=False)
