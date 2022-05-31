import os
import json
import threading
import requests
import sys
import paho.mqtt.client as mqtt
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)


def on_connect(client, userdata, flags, rc):
    print("Connected on subscriber with code ", rc)

    client.subscribe(ALL_TOPICS)
    print(f"Subscribed to {ALL_TOPICS}")

    client.subscribe(CONFIG_TOPIC)
    print(f"Subscribed to {CONFIG_TOPIC}")


def on_message(client, userdata, msg):
    global index_room
    print(f"Message received at {msg.topic} with message {msg.payload.decode()}")
    topic = msg.topic.split('/')

    if "config" in topic:
        if saved_rooms.get(msg.payload.decode()) is None:
            room_name = f"Room{index_room}"
            saved_rooms[msg.payload.decode()] = room_name
            index_room += 1
            print(f"Digital twin with ID {msg.payload.decode()} saved as {room_name}")
            client.publish(f"{msg.topic}/room", payload=room_name, qos=0, retain=True)
            print(f"Published {room_name} at TOPIC {msg.topic}/room")

    elif "telemetry" in topic:
        if topic[-1] == "last-will":
            print("Raspberry", topic[3], "disconnection received")
        else:
            payload = json.loads(msg.payload)
            requests.post(
                API_URL,
                json={"room": topic[2], "type": topic[-1], "value": payload["value"], "timestamp": payload["timestamp"]}
            )


def send_command(params):
    type_dev = params["type"]
    value = params["value"]
    room = params["room"]
    topic = f"hotel/rooms/{room}/command/"

    commands = {"air-conditioner-mode": "air-conditioner",
                "blind-mode": "blind", "blind-level": "blind-level",
                "indoor-light-mode": "indoor", "indoor-light-level": "indoor-level",
                "outdoor-light-mode": "outdoor", "outdoor-light-level": "outdoor-level"}

    if type_dev not in commands:
        return {"response": "Incorrect type param"}, 401

    topic += commands[type_dev]
    client.publish(topic, payload=json.dumps({"mode": value}), qos=0, retain=True)
    print(f"Command message has been sent through {topic}")
    return {"response": "Message sent successfully"}, 200


@app.route('/device_state', methods=['POST'])
def device_state():
    if request.method == 'POST':
        print("MESSAGE ROUTER POST", file=sys.stderr)
        params = request.get_json()
        return send_command(params)


def mqtt_listener():
    client.loop_forever()


if __name__ == "__main__":
    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))

    ALL_TOPICS = "hotel/rooms/+/telemetry/+"
    CONFIG_TOPIC = "hotel/rooms/+/config"

    API_URL = f"http://{os.getenv('DATA_INGESTION_API_HOST')}:{os.getenv('DATA_INGESTION_API_PORT')}/device_state"

    index_room = 1
    saved_rooms = {}

    client = mqtt.Client()
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)

    listener_thread = threading.Thread(target=mqtt_listener)
    listener_thread.start()
    # mqtt_listener()

    CORS(app)
    app.run(host=os.getenv("API_HOST"), port=int(os.getenv("API_PORT")), debug=False)

    listener_thread.join()
