from flask import Flask, request
from flask_cors import CORS
from data_ingestion import insert_device_state, get_device_state
import os
import sys


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
        return {"response": f"{mycursor.rowcount} records inserted"},200
    elif request.method == 'GET':
        print("GET", file=sys.stderr)
        # params = request.get_json()
        # print("after request.get_json()", file=sys.stderr)
        # print(params, file=sys.stderr)
        # if len(params) != 3:
        #     return {"response": "Incorrect parameters"}, 401
        myselect = get_device_state()
        print(myselect, file=sys.stderr)
        return [{"room": myselect[0], "type": myselect[1], "value": myselect[2]}]


HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
app.run(host= HOST, port= PORT, debug=True)

