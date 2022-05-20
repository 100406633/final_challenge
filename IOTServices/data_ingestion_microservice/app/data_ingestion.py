import os
import sys
import datetime
import mysql.connector

def connect_database():

    mydb = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user = os.getenv('DB_USER'),
        password = os.getenv('DB_PASSWORD'),
        database = os.getenv('DB_NAME')
    )
    return mydb

def insert_device_state(params):
    mydb = connect_database()
    with mydb.cursor() as mycursor:
        sql = "INSERT INTO device_state (room, type, value, date) VALUES (%s, %s, %s, %s)"
        print(f"params = {params}", file=sys.stderr)
        print(f"sql = {sql}", file=sys.stderr)
        values = (
            params["room"],
            params["type"],
            params["value"],
            datetime.datetime.now()
        )
        mycursor.execute(sql,values)
        mydb.commit()
        return mycursor