import json, os, threading, random, pprint, time, subprocess
import paho.mqtt.client as mqtt

RANDOMIZE_SENSORS_INTERVAL = 30
MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_1_PORT = 1883
MQTT_2_PORT = 1884



index_room = 1
json_temperature = []
json_air = []
json_blind = []
current_temperature = "0"
temperature = 0
current_air = "0"
current_blind = "0"
connect_raspberry = False

def get_host_name():
    bashCommandName = 'echo $HOSTNAME'
    host = subprocess \
               .check_output(['bash', '-c', bashCommandName]) \
               .decode("utf-8")[0:-1]
    return host


container_id = get_host_name()
CONFIG_TOPIC = f"hotel/rooms/{container_id}/config"

sensors = {
    "indoor_light": {
        "active": True,
        "level": random.randint(0, 100)
    },
    "outside_light": {
        "active": True,
        "level": random.randint(0, 100)
    },
    "blind": {
        "is_open": True,
        "level": random.randint(0, 100)
    },
    "air_conditioner": {
        "active": True,
        "level": random.randint(10, 30)
    },
    "presence": {
        "active": True,
        "detected": True if random.randint(0, 1) == 1 else False
    },
    "temperature": {
        "active": True,
        "temperature": random.randint(0, 40)
    }
}


def on_connect_1883(client, userdata, flags, rc):
    print("Digital Twin connected with code:", rc)
    client.publish(CONFIG_TOPIC, payload=container_id, qos=0, retain=False)
    print("Sent id", container_id, "to topic", CONFIG_TOPIC)
    client.subscribe(CONFIG_TOPIC + "/room")
    print(f"Subscribed to, {CONFIG_TOPIC}/room")


def on_message_1883(client, userdata, msg):
    global room_number
    print(f"Message received in MQTT-1883 {msg.topic} with message {msg.payload.decode()}")
    topic = msg.topic.split('/')
    if topic[-2] == "config":
        room_number = msg.payload.decode()
        print("Room number received as:", room_number)


def on_publish_1883(client, userdata, result):
    print("data published")


def on_disconnect_1883(client, userdata, flags, rc):
    pass


def connect_mqtt_1883():
    global room_number, MQTT_SERVER, MQTT_1_PORT, temperature, current_temperature
    client = mqtt.Client("Client-1883")
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect_1883
    client.on_publish = on_publish_1883
    client.on_message = on_message_1883
    client.on_disconnect = on_disconnect_1883
    client.connect(MQTT_SERVER, MQTT_1_PORT, 60)
    client.loop_start()
    while room_number == "":
        print("WAITING ROOM NUMBER IN THREAD", threading.currentThread().ident)
        time.sleep(1)

    TELEMETRY_TOPIC = f"hotel/rooms/{room_number}/telemetry/"
    TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "temperature"
    AIR_CONDITIONER_TOPIC = TELEMETRY_TOPIC + "air_conditioner"
    BLIND_TOPIC = TELEMETRY_TOPIC + "blind"
    while True:
        if temperature != current_temperature:
            client.publish(TEMPERATURE_TOPIC, payload=temperature,qos=0,retain=False)
            print("Published", temperature,"in", TEMPERATURE_TOPIC)
            current_temperature = temperature
        time.sleep(1)
    client.loop_stop()

def on_connect_1884(client, userdata, flags, rc):
    global room_number

    PHYSICAL_ROOM_CONFIG_TOPIC = f"hotel/physical_rooms/{room_number}/config"
    client.subscribe(PHYSICAL_ROOM_CONFIG_TOPIC)
    print(f"Subscribed to, {PHYSICAL_ROOM_CONFIG_TOPIC}")

    RASPBERRY_TELEMETRY_TOPIC = f"hotel/physical_rooms/{room_number}/telemetry/+"
    client.subscribe(RASPBERRY_TELEMETRY_TOPIC)
    print(f"Subscribed to, {RASPBERRY_TELEMETRY_TOPIC}")


def on_message_1884(client, userdata, msg):
    global temperature, room_number, connect_raspberry
    print(f"Message received in MQTT-1884 {msg.topic} with message {msg.payload.decode()}")
    topic = msg.topic.split('/')
    if topic[-1] == "temperature":
        print("Received temperature", msg.payload.decode())
        temperature = msg.payload.decode()

    elif topic[-1] == "config":
        connect_raspberry = True
        room_number = msg.payload.decode()

def on_publish_1884(client, userdata, result):
    print("data published")


def on_disconnect_1884(client, userdata, flags, rc):
    pass


def connect_mqtt_1884():
    global room_number, MQTT_SERVER, MQTT_2_PORT
    client = mqtt.Client("Client-1884")
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect_1884
    client.on_publish = on_publish_1884
    client.on_message = on_message_1884
    client.on_disconnect = on_disconnect_1884

    while room_number == "":
        print("WAITING ROOM NUMBER IN THREAD", threading.currentThread().ident)
        time.sleep(1)
    client.connect(MQTT_SERVER, MQTT_2_PORT, 60)
    client.loop_forever()

def randomize_sensors():
    global sensors, connect_raspberry
    if not connect_raspberry:

        sensors = {
            "indoor_light": {
                "active": True if random.randint(0, 1) == 1 else False,
                "level": random.randint(0, 100)
            },
            "outside_light": {
                "active": True if random.randint(0, 1) == 1 else False,
                "level": random.randint(0, 100)
            },
            "blind": {
                "is_open": True if random.randint(0, 1) == 1 else False,
                "level": random.randint(0, 100)
            },
            "air_conditioner": {
                "active": True if random.randint(0, 1) == 1 else False,
                "level": random.randint(0, 100)
            },
            "presence": {
                "active": True if random.randint(0, 1) == 1 else False,
                "detected": True if random.randint(0, 1) == 1 else False
            },
            "temperature": {
                "active": True if random.randint(0, 1) == 1 else False,
                "temperature": random.randint(0, 40)
            }
        }
        print("Set randomized sensors.")
        pprint.pprint(sensors)
        threading.Timer(RANDOMIZE_SENSORS_INTERVAL, randomize_sensors).start()


if __name__ == "__main__":
    room_number = ""
    t1 = threading.Thread(target=connect_mqtt_1883)
    t2 = threading.Thread(target=connect_mqtt_1884)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
