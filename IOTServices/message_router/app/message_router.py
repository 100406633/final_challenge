import os
import json
import threading
import requests
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
    # subscribe to all command topics


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
        room_name = topic[2]
        if "temperature" in topic:
            requests.post(
                API_URL,
                json={"room": room_name, "type": topic[-1], "value": msg.payload.decode()}
            )


def send_command(params):
    type_dev = params["type"]
    value = params["value"]
    room = params["room"]
    if type_dev == "air-conditioner-mode":
        topic = f"hotel/rooms/{room}/command/air-conditioner"
        client.publish(topic, payload=json.dumps({"mode": value}), qos=0, retain=True)
        print(f"Command message has been sent through {topic}")
        return {"response": "Message sent successfully"}, 200
    else:
        return {"response": "Incorrect type param"}, 401


@app.route('/device_state', methods=['POST'])
def device_state():
    if request.method == 'POST':
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

    # listener_thread = threading.Thread(target=mqtt_listener, daemon=True)
    # listener_thread.start()
    mqtt_listener()

    CORS(app)
    app.run(host=os.getenv("API_HOST"), port=int(os.getenv("API_PORT")), debug=True)
    print("message_router set up")
