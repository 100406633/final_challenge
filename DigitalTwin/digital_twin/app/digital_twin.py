import random
import os
import time
import json
import subprocess
import threading
import pprint
import paho.mqtt.client as mqtt


def get_host_name():
    bash_command_name = 'echo $HOSTNAME'
    return subprocess.check_output(['bash', '-c', bash_command_name]).decode("utf-8")[0:-1]


def on_connect_1883(client, userdata, flags, rc):
    print(f"Digital Twin connected with code: {rc}")
    client.publish(CONTAINER_CONFIG_TOPIC, payload=container_id, qos=0, retain=False)
    print(f"Sent ID {container_id} to topic {CONTAINER_CONFIG_TOPIC}")
    client.subscribe(CONTAINER_CONFIG_TOPIC + "/room")
    print(f"Subscribed to, {CONTAINER_CONFIG_TOPIC}/room")


def on_message_1883(client, userdata, msg):
    print(f"Message received in MQTT-1883 {msg.topic} with message {msg.payload.decode()}")
    topic = msg.topic.split('/')
    if "config" in topic:
        global room_number
        room_number = msg.payload.decode()
        print(f"Room number received as: {room_number}")
    elif "command" in topic and "air-conditioner" in topic:
        global sensors
        print(f"Air-conditioner command received {msg.payload}")
        payload = json.loads(msg.payload)  #this ain't gonna work
        sensors["air_conditioner"]["active"] = payload["mode"]


def on_publish_1883(client, userdata, result):
    print("data published")


def on_disconnect_1883(client, userdata, flags):
    pass


def connect_mqtt_1883():
    global room_number, MQTT_SERVER, MQTT_1_PORT, sensors
    client = mqtt.Client("Client-1883")
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect_1883
    client.on_publish = on_publish_1883
    client.on_message = on_message_1883
    # client.on_disconnect = on_disconnect_1883

    client.connect(MQTT_SERVER, MQTT_1_PORT, 60)
    client.loop_start()

    while room_number == "":
        print(f"WAITING ROOM NUMBER IN THREAD {threading.current_thread().ident}")
        time.sleep(1)

    telemetry_topic = f"hotel/rooms/{room_number}/telemetry/"
    temperature_topic = f"{telemetry_topic}temperature"
    air_conditioner_mode_topic = f"{telemetry_topic}air-mode"
    air_conditioner_level_topic = f"{telemetry_topic}air-level"
    blind_mode_topic = f"{telemetry_topic}blind-mode"
    blind_level_topic = f"{telemetry_topic}blind-level"
    presence_topic = f"{telemetry_topic}presence"
    indoor_mode_topic = f"{telemetry_topic}indoor-mode"
    indoor_level_topic = f"{telemetry_topic}indoor-level"
    outdoor_mode_topic = f"{telemetry_topic}outdoor-mode"
    outdoor_level_topic = f"{telemetry_topic}outdoor-level"
    current_temperature = 0

    while True:
        if sensors["temperature"]["temperature"] != current_temperature:
            client.publish(temperature_topic, payload=str(sensors["temperature"]["temperature"]), qos=0, retain=False)
            print(f'Published {sensors["temperature"]["temperature"]} in {temperature_topic}')
            current_temperature = sensors["temperature"]["temperature"]

        client.publish(air_conditioner_mode_topic, payload=str(sensors["air_conditioner"]["active"]), qos=0, retain=False)
        print(f'Published {sensors["air_conditioner"]["active"]} in {air_conditioner_mode_topic}')
        client.publish(air_conditioner_level_topic, payload=str(sensors["air_conditioner"]["level"]), qos=0, retain=False)
        print(f'Published {sensors["air_conditioner"]["level"]} in {air_conditioner_level_topic}')

        client.publish(presence_topic, payload=str(sensors["presence"]["detected"]), qos=0, retain=False)
        print(f'Published {sensors["presence"]["detected"]} in {presence_topic}')

        client.publish(indoor_mode_topic, payload=str(sensors["indoor_light"]["active"]), qos=0, retain=False)
        print(f'Published {sensors["indoor_light"]["active"]} in {indoor_mode_topic}')
        client.publish(indoor_level_topic, payload=str(sensors["indoor_light"]["level"]), qos=0, retain=False)
        print(f'Published {sensors["indoor_light"]["level"]} in {indoor_level_topic}')

        client.publish(outdoor_mode_topic, payload=str(sensors["outside_light"]["active"]), qos=0, retain=False)
        print(f'Published {sensors["outside_light"]["active"]} in {outdoor_mode_topic}')
        client.publish(outdoor_level_topic, payload=str(sensors["outside_light"]["level"]), qos=0, retain=False)
        print(f'Published {sensors["outside_light"]["level"]} in {outdoor_level_topic}')

        client.publish(blind_mode_topic, payload=str(sensors["blind"]["is_open"]), qos=0, retain=False)
        print(f'Published {sensors["blind"]["is_open"]} in {blind_mode_topic}')
        client.publish(blind_level_topic, payload=str(sensors["blind"]["level"]), qos=0, retain=False)
        print(f'Published {sensors["blind"]["level"]} in {blind_level_topic}')

        time.sleep(1)

    client.loop_stop()


def on_connect_1884(client, userdata, flags, rc):
    global room_number
    print("on_connect_1884\n")

    physical_room_config_topic = f"hotel/rooms/{room_number}/config"
    client.subscribe(physical_room_config_topic)
    print(f"Subscribed to, {physical_room_config_topic}")

    raspberry_telemetry_topic = f"hotel/rooms/{room_number}/telemetry/+"
    client.subscribe(raspberry_telemetry_topic)
    print(f"Subscribed to, {raspberry_telemetry_topic}")


def on_message_1884(client, userdata, msg):
    global sensors, room_number, connect_raspberry
    print(f"Message received in MQTT-1884 {msg.topic} with message {msg.payload.decode()}")
    topic = msg.topic.split('/')
    if "temperature" in topic:
        print(f"Received temperature {msg.payload.decode()}")
        sensors["temperature"]["temperature"] = int(msg.payload.decode())
    elif "config" in topic:
        connect_raspberry = True
        room_number = msg.payload.decode()


def on_publish_1884(client, userdata, result):
    print("data published")


def on_disconnect_1884(client, userdata, flags):
    pass


def connect_mqtt_1884():
    global room_number, MQTT_SERVER, MQTT_2_PORT, sensors, connect_raspberry
    client = mqtt.Client("Client-1884")
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect_1884
    client.on_publish = on_publish_1884
    client.on_message = on_message_1884
    # client.on_disconnect = on_disconnect_1884

    while room_number == "":
        print(f"WAITING ROOM NUMBER IN THREAD {threading.current_thread().ident}")
        time.sleep(1)

    client.connect(MQTT_SERVER, MQTT_2_PORT, 60)
    client.loop_start()

    # if digital twin must send commands even if the raspberry Pi is not connected, don't do this loop
    # while not connect_raspberry:
    #     print(f"WAITING PHYSICAL ROOM NUMBER IN THREAD {threading.current_thread().ident}")
    #     time.sleep(1)

    air_conditioner_command_topic = f"hotel/rooms/{room_number}/command/air-conditioner"
    blind_topic = f"hotel/rooms/{room_number}/command/blind"
    indoor_topic = f"hotel/rooms/{room_number}/command/indoor"
    outdoor_topic = f"hotel/rooms/{room_number}/command/outdoor"

    current_air_conditioner_mode = 0
    current_blind_mode = 0
    current_indoor_mode = 0
    current_outdoor_mode = 0

    while True:
        if sensors["air_conditioner"]["active"] != current_air_conditioner_mode:
            client.publish(air_conditioner_command_topic,
                           payload=json.dumps({"mode": sensors["air_conditioner"]["active"]}), qos=0, retain=False)
            print(f'Published {sensors["air_conditioner"]["active"]} in {air_conditioner_command_topic}')
            current_air_conditioner_mode = sensors["air_conditioner"]["active"]

        if sensors["blind"]["is_open"] != current_blind_mode:
            client.publish(blind_topic,
                           payload=json.dumps({"mode": sensors["blind"]["is_open"]}), qos=0, retain=False)
            print(f'Published {sensors["blind"]["is_open"]} in {blind_topic}')
            current_blind_mode = sensors["blind"]["is_open"]

        if sensors["indoor_light"]["active"] != current_indoor_mode:
            client.publish(indoor_topic,
                           payload=json.dumps({"mode": sensors["indoor_light"]["active"]}), qos=0, retain=False)
            print(f'Published {sensors["indoor_light"]["active"]} in {indoor_topic}')
            current_indoor_mode = sensors["indoor_light"]["active"]

        if sensors["outside_light"]["active"] != current_outdoor_mode:
            client.publish(outdoor_topic,
                           payload=json.dumps({"mode": sensors["outside_light"]["active"]}), qos=0, retain=False)
            print(f'Published {sensors["outside_light"]["active"]} in {outdoor_topic}')
            current_outdoor_mode = sensors["outside_light"]["active"]
        time.sleep(1)

    client.loop_stop()


def randomize_sensors():
    global sensors, connect_raspberry
    if not connect_raspberry:
        sensors["indoor_light"]["active"] = random.randint(0, 1)
        sensors["indoor_light"]["level"] = random.randint(0, 100)

        sensors["outside_light"]["active"] = random.randint(0, 1)
        sensors["outside_light"]["level"] = random.randint(0, 100)

        sensors["blind"]["is_open"] = random.randint(0, 1)
        sensors["blind"]["level"] = random.randint(0, 180)

        sensors["air_conditioner"]["active"] = random.randint(0, 2)
        sensors["air_conditioner"]["level"] = random.randint(0, 100)

        sensors["presence"]["active"] = True if random.randint(0, 1) == 1 else False
        sensors["presence"]["detected"] = random.randint(0, 1)

        sensors["temperature"]["active"] = True if random.randint(0, 1) == 1 else False
        sensors["temperature"]["temperature"] = random.randint(0, 40)

        print("Set randomized sensors")
        pprint.pprint(sensors)
        threading.Timer(RANDOMIZE_SENSORS_INTERVAL, randomize_sensors).start()


if __name__ == "__main__":
    RANDOMIZE_SENSORS_INTERVAL = 30
    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_1_PORT = int(os.getenv("MQTT_1_SERVER_PORT"))
    MQTT_2_PORT = int(os.getenv("MQTT_2_SERVER_PORT"))

    connect_raspberry = False
    room_number = ""
    container_id = get_host_name()
    CONTAINER_CONFIG_TOPIC = f"hotel/rooms/{container_id}/config"

    sensors = {
        "indoor_light": {
            "active": random.randint(0, 1),
            "level": random.randint(0, 100)
        },
        "outside_light": {
            "active": random.randint(0, 1),
            "level": random.randint(0, 100)
        },
        "blind": {
            "is_open": random.randint(0, 1),
            "level": random.randint(0, 180)
        },
        "air_conditioner": {
            "active": random.randint(0, 2),
            "level": random.randint(0, 100),
        },
        "presence": {
            "active": True if random.randint(0, 1) == 1 else False,
            "detected": random.randint(0, 1)
        },
        "temperature": {
            "active": True if random.randint(0, 1) == 1 else False,
            "temperature": random.randint(0, 40)
        }
    }

    randomize_sensors()
    mqtt_1883_thread = threading.Thread(target=connect_mqtt_1883, daemon=True)
    mqtt_1884_thread = threading.Thread(target=connect_mqtt_1884, daemon=True)

    mqtt_1883_thread.start()
    mqtt_1884_thread.start()
