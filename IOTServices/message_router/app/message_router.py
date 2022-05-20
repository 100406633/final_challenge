import json, os
import paho.mqtt.client as mqtt
import requests

MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_PORT = 1883

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
        requests.post(
            API_URL,
            json={"room":room_name,"type":topic[-1],"value":msg.payload.decode()}
        )

def connect_mqtt():
    global MQTT_SERVER, MQTT_PORT
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)


if __name__ == "__main__":
    client = mqtt.Client()
    connect_mqtt()
    client.loop_forever()
