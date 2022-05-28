import os
import sys
import datetime
import mysql.connector


def connect_database():
    mydb = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
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
        mycursor.execute(sql, values)
        mydb.commit()
        return mycursor


def get_device_state():
    mydb = connect_database()
    with mydb.cursor() as mycursor:
        # sql = "WITH a AS (SELECT room, type, value, TIMESTAMPDIFF(SECOND, date, CURRENT_TIMESTAMP) AS diff FROM device_state) " \
        #       "SELECT room, type, value FROM a"
        sql = "WITH a AS (SELECT room, type, value, TIMESTAMPDIFF(SECOND, date, CURRENT_TIMESTAMP) AS diff FROM device_state), " \
              "b AS (SELECT room, type, value, MIN(diff) FROM a GROUP BY (room, type, value)) " \
              "SELECT room, type, value FROM b"
        # sql = "SELECT room,type,value FROM device_state WHERE room=%s AND type=%s ORDER BY date desc limit 1"
        # sql = "SELECT room,type,value FROM device_state WHERE room='"+ str(params['room']) + "' and type ='" + str(params['type']) + "' ORDER BY date desc limit 1"
        print(f"sql = {sql}", file=sys.stderr)
        # values = (
        #     "Room1",
        #     "temperature"
        # )
        # mycursor.execute(sql, values)
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return result[0]
