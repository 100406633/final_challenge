import json, os
import threading

from flask import Flask, request
from flask_cors import CORS
import paho.mqtt.client as mqtt
import requests
MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
app = Flask(__name__)
TELEMETRY_TOPIC = "hotel/rooms/+/telemetry/"
TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "temperature"
AIR_CONDITIONER_TOPIC = TELEMETRY_TOPIC + "air_conditioner"
CONFIG_TOPIC = "hotel/rooms/+/config"
BLIND_TOPIC = TELEMETRY_TOPIC + "blind"
ALL_TOPICS = "hotel/rooms/+/telemetry/+"
API_URL = "http://data_ingestion_microservice:5000/device_state"
index_room = 1
json_temperature = []
json_air = []
json_blind = []
current_temperature = "0"
current_air = "0"
current_blind = "0"
saved_rooms = {}


def on_connect(client, userdata, flags, rc):
    print("Connected on subscriber with code ", rc)
    client.subscribe(TEMPERATURE_TOPIC)
    print("Subscribed to ", TEMPERATURE_TOPIC)
    client.subscribe(AIR_CONDITIONER_TOPIC)
    print("Subscribed to ", AIR_CONDITIONER_TOPIC)
    client.subscribe(BLIND_TOPIC)
    print("Subscribed to ", BLIND_TOPIC)

    client.subscribe(ALL_TOPICS)
    client.subscribe(CONFIG_TOPIC)
    # subscribe to all command topics
    print("Subscribed to all")
    print("Subscribed to ", CONFIG_TOPIC)


def on_message(client, userdata, msg):
    global current_temperature, current_air, current_blind, index_room, room_name
    print("Message received at ", msg.topic, " with message ", msg.payload.decode())
    topic = msg.topic.split('/')
    if topic[-1] == "config":
        if saved_rooms.get(msg.payload.decode()) is None:
            room_name = "Room" + str(index_room)
            saved_rooms[msg.payload.decode()] = room_name
            print("Digital with id", msg.payload.decode(), "saved as", room_name)
            index_room += 1
            client.publish(msg.topic + "/room", payload=room_name, qos=0, retain=True)
            print("Published", room_name, "at TOPIC", msg.topic + "/room")

    if "telemetry" in topic:
        room_name = topic[2]
        if topic[-1] == "temperature":
            requests.post(
                API_URL,
                json={"room": room_name, "type": topic[-1], "value": msg.payload.decode()}
            )

def send_command(params):
    type_dev = params["type"]
    value = params["value"]
    room = params["room"]
    topic = "hotel/rooms"+room+"/command/air-conditioner"
    if type_dev == "air-conditioner-mode":
        client.publish(topic,payload=json.dumps({"mode":value}), qos=0, retain=True)
        print("Command message has been sent through "+topic)
        return {"response":"Message sent successfully"}, 200
    else:
        return {"response":"Incorrect type param"},401

@app.route('/device_state', methods=['POST'])
def device_state():
    if request.method == 'POST':
        params = request.get_json()
        return send_command(params)


def mqtt_listener():
    client.loop_forever()

if __name__ == "__main__":
    client = mqtt.Client()
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    t1 = threading.Thread(target=mqtt_listener())
    t1.setDaemon(True)
    t1.start()
    CORS(app)
    app.run(host=os.getenv("API_HOST"),port=int(os.getenv("API_PORT")), debug=True)
    client.loop_forever()
