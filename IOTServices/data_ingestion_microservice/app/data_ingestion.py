import os
import datetime
import mysql.connector


def connect_database():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )


def insert_device_state(params):
    db = connect_database()
    with db.cursor() as cursor:
        sql = "INSERT INTO device_state (room, type, value, date) VALUES (%s, %s, %s, %s)"
        values = (
            params["room"],
            params["type"],
            params["value"],
            datetime.datetime.now()
        )
        cursor.execute(sql, values)
        db.commit()
        return cursor


def get_device_state():
    db = connect_database()
    with db.cursor() as cursor:
        sql = "WITH a AS (SELECT room, type, value, TIMESTAMPDIFF(SECOND, date, CURRENT_TIMESTAMP) AS diff FROM device_state), \
        b AS (SELECT room, type, MIN(diff) AS diff FROM a GROUP BY room, type) \
        SELECT * FROM a RIGHT JOIN b ON (a.room=b.room AND a.type=b.type AND a.diff=b.diff);"
        cursor.execute(sql)
        result = cursor.fetchall()
        return result
