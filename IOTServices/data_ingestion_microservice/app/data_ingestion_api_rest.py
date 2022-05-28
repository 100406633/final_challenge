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
        print("POST", file=sys.stderr)
        params = request.get_json()
        print("after request.get_json()", file=sys.stderr)
        if len(params) != 3:
            return {"response": "Incorrect parameters"}, 401
        mycursor = insert_device_state(params)
        return {"response": f"{mycursor.rowcount} records inserted"}, 200

    elif request.method == 'GET':
        print("GET", file=sys.stderr)
        myselect = get_device_state()
        print(myselect, file=sys.stderr)
        data = {i: {"room": myselect[i][0], "type": myselect[i][1], "value": myselect[i][2]}
                for i in range(len(myselect))}
        print("data:\n", data, file=sys.stderr)
        return data


app.run(host=HOST, port=PORT, debug=True)
