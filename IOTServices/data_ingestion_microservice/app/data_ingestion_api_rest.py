from flask import Flask, request
from flask_cors import CORS
from data_ingestion import insert_device_state, get_device_state
import os
import sys


app = Flask(__name__)
CORS(app)


@app.route('/device_state',methods=['GET','POST'])
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
        params = request.get_json()
        print("after request.get_json()", file=sys.stderr)
        print(params, file=sys.stderr)
        if len(params) != 3:
            return {"response": "Incorrect parameters"}, 401
        myselect = get_device_state(params)
        print(myselect, file=sys.stderr)
        return myselect


# def device_state():
#     global json_params,counter
#     if request.method == 'POST':
#         params = request.get_json()
#         if len(params) != 3:
#             return {"response":"Incorrect parameters"}, 401
#         mycursor = insert_device_state(params)
#         json_params[counter]=params
#         counter+=1
#         return {"response":f"{mycursor.rowcount} records inserted."},200
#
#     if request.method == 'GET':
#         counter = 0
#         var = json_params
#         json_params = {}
#         return var
#         """ params = request.get_json()
#         if len(params) != 3:
#             return {"response":"Incorrect parameters"}, 401
#         myselect = select_device_state(params)
#         return myselect"""

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
app.run(host= HOST, port= PORT, debug=True)

