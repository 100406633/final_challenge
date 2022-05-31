import random
import json
import time
import datetime
import threading
import Adafruit_DHT
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from openpyxl import load_workbook


def change_servo_pos(pos):
    global servo_pwm
    print(f"change_servo_pos: {pos}")
    servo_pwm.ChangeDutyCycle(2 + (pos/18))
    time.sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)


def setup():
    global pwm, servo_pwm, pwm_indoor, pwm_outdoor
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(motor_pin_a, GPIO.OUT)
    pwm = GPIO.PWM(motor_pin_a, 100)
    pwm.start(0)

    GPIO.setup(servo_pin, GPIO.OUT)
    servo_pwm = GPIO.PWM(servo_pin, 50)
    servo_pwm.start(0)

    GPIO.setup(motor_pin_a, GPIO.OUT)
    GPIO.setup(motor_pin_b, GPIO.OUT)
    GPIO.setup(motor_pin_energy, GPIO.OUT)

    GPIO.setup(red_pin, GPIO.OUT)
    GPIO.setup(green_pin, GPIO.OUT)
    GPIO.setup(blue_pin, GPIO.OUT)
    GPIO.setup(indoor_light_pin, GPIO.OUT)
    GPIO.setup(outdoor_light_pin, GPIO.OUT)

    pwm_indoor = GPIO.PWM(indoor_light_pin, 100)
    pwm_outdoor = GPIO.PWM(outdoor_light_pin, 100)
    pwm_outdoor.start(0)
    pwm_indoor.start(0)

    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=button_pressed_callback, bouncetime=200)

    GPIO.output(motor_pin_b, GPIO.LOW)
    GPIO.output(motor_pin_energy, GPIO.HIGH)


def button_pressed_callback(channel):
    global sensors
    sem_presence.acquire()
    sensors["presence"]["detected"] = int(not sensors["presence"]["detected"])
    print(f'presence changed to {sensors["presence"]["detected"]}\n')
    sem_presence.release()


def led():
    global sensors, air_conditioner_op_mode
    while not kill:
        sem_presence.acquire()
        if air_conditioner_op_mode == "local" and not sensors["presence"]["detected"]:
            sem_presence.release()
            GPIO.output(red_pin, GPIO.LOW)
            GPIO.output(green_pin, GPIO.LOW)
            GPIO.output(blue_pin, GPIO.LOW)
            time.sleep(1)
            continue

        sem_presence.release()

        sem_color.acquire()
        global color
        if color == "blue":
            GPIO.output(red_pin, GPIO.LOW)
            GPIO.output(green_pin, GPIO.LOW)
            GPIO.output(blue_pin, GPIO.HIGH)
            time.sleep(1)
        elif color == "green":
            GPIO.output(red_pin, GPIO.LOW)
            GPIO.output(green_pin, GPIO.HIGH)
            GPIO.output(blue_pin, GPIO.LOW)
            time.sleep(1)

        elif color == "red":
            GPIO.output(red_pin, GPIO.HIGH)
            GPIO.output(green_pin, GPIO.LOW)
            GPIO.output(blue_pin, GPIO.LOW)
            time.sleep(1)
        sem_color.release()


def motor():
    global pwm, color, sensors, air_conditioner_op_mode
    color = "green"
    while not kill:
        if air_conditioner_op_mode == "web":
            sem_air_conditioner.acquire()
            if sensors["air_conditioner"]["active"] == 0:
                pwm.ChangeDutyCycle(0)
                sensors["air_conditioner"]["level"] = 0
                sem_color.acquire()
                color = "green"
                sem_color.release()
            elif sensors["air_conditioner"]["active"] == 1:
                pwm.ChangeDutyCycle(100)
                sensors["air_conditioner"]["level"] = 100
                sem_color.acquire()
                color = "red"
                sem_color.release()
            elif sensors["air_conditioner"]["active"] == 2:
                pwm.ChangeDutyCycle(100)
                sensors["air_conditioner"]["level"] = 100
                sem_color.acquire()
                color = "blue"
                sem_color.release()
                
            sem_air_conditioner.release()
        else:
            sem_presence.acquire()
            if not sensors["presence"]["detected"]:
                sem_presence.release()

                pwm.ChangeDutyCycle(0)
                sem_color.acquire()
                color = "green"
                sem_color.release()

                sem_air_conditioner.acquire()
                sensors["air_conditioner"]["active"] = 0
                sem_air_conditioner.release()
                sensors["air_conditioner"]["level"] = 0
                time.sleep(1)
                continue

            sem_presence.release()

            temperature = sensors["temperature"]["temperature"]
            if temperature:
                upper_bound = 24
                lower_bound = 21
                if lower_bound < temperature < upper_bound:
                    pwm.ChangeDutyCycle(0)
                    sem_color.acquire()
                    color = "green"
                    sem_color.release()

                    sem_air_conditioner.acquire()
                    sensors["air_conditioner"]["active"] = 0
                    sem_air_conditioner.release()
                    sensors["air_conditioner"]["level"] = 0

                if temperature < lower_bound:
                    cycle = abs(lower_bound-temperature) * 10
                    if cycle > 100:
                        cycle = 100
                    sem_color.acquire()
                    color = "red"
                    sem_color.release()
                    pwm.ChangeDutyCycle(cycle)

                    sem_air_conditioner.acquire()
                    sensors["air_conditioner"]["active"] = 1
                    sem_air_conditioner.release()
                    sensors["air_conditioner"]["level"] = cycle
                elif temperature > upper_bound:
                    cycle = abs(temperature - upper_bound) * 10
                    if cycle > 100:
                        cycle = 100
                    sem_color.acquire()
                    color = "blue"
                    sem_color.release()
                    pwm.ChangeDutyCycle(cycle)

                    sem_air_conditioner.acquire()
                    sensors["air_conditioner"]["active"] = 2
                    sem_air_conditioner.release()
                    sensors["air_conditioner"]["level"] = cycle


def weather_sensor():
    global sensors
    wb = load_workbook('/home/pi/Desktop/weather.xlsx')
    sheet = wb['Sheet1']
    current_hum = 0
    current_temp = 0
    while not kill:
        sem_presence.acquire()
        if not sensors["presence"]["detected"]:
            sem_presence.release()
            time.sleep(1)
            continue
        sem_presence.release()

        today = datetime.date.today()
        now = datetime.datetime.now().time()
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, dht_pin)
        if humidity and temperature:
            temperature = int(temperature)
            dif_humidity = abs(current_hum - humidity)
            dif_temperature = abs(current_temp - temperature)
            if dif_humidity > 0.1 and dif_temperature > 0.1:
                row = (today, now, temperature, "961.9", humidity)
                sheet.append(row)
                wb.save('/home/pi/Desktop/weather.xlsx')
                print("Temp = {0: 0.1f}C Humidity = {1: 0.1f} %".format(temperature, humidity))
                current_hum = humidity
                current_temp = temperature
                sensors["temperature"]["temperature"] = temperature
        time.sleep(1)


def destroy():
    global outdoor_light_pin, indoor_light_pin, servo_pwm, pwm
    pwm.stop()
    servo_pwm.stop()
    GPIO.output(indoor_light_pin, GPIO.LOW)
    GPIO.output(outdoor_light_pin, GPIO.LOW)
    GPIO.cleanup()


def on_connect(client, userdata, flags, rc):
    global room_number, command_topic, CONFIG_TOPIC
    print("Digital Twin connected with code:", rc)
    client.publish(CONFIG_TOPIC, payload=room_number, qos=0, retain=False)
    print("Sent room number", room_number, "to topic", CONFIG_TOPIC)

    client.subscribe(command_topic)
    print(f"Subscribed to, {command_topic}")


def on_message(client, userdata, msg):
    global outdoor_light_pin, indoor_light_pin, pwm_outdoor, pwm_indoor
    print(f"Message received in MQTT 1884 {msg.topic} with message {msg.payload.decode()}")
    topic = msg.topic.split('/')
    if "config" in topic:
        global is_connected
        is_connected = True

    elif "command" in topic:
        global sensors, air_conditioner_op_mode
        if topic[-1] == "air-conditioner":
            print("Received AC command")
            payload = json.loads(msg.payload)

            sem_air_conditioner.acquire()
            sensors["air_conditioner"]["active"] = int(payload["mode"])
            sem_air_conditioner.release()
            air_conditioner_op_mode = "web"

        elif topic[-1] == "indoor":
            print("Received indoor command")
            payload = json.loads(msg.payload)
            sensors["indoor_light"]["active"] = int(payload["mode"])
            if sensors["indoor_light"]["active"] == 1:
                pwm_indoor.ChangeDutyCycle(sensors["indoor_light"]["level"])
            else:
                pwm_indoor.ChangeDutyCycle(0)

        elif topic[-1] == "indoor-level":
            print("Received indoor level command")
            payload = json.loads(msg.payload)
            sensors["indoor_light"]["level"] = int(payload["mode"])
            if sensors["indoor_light"]["active"] == 1:
                pwm_indoor.ChangeDutyCycle(sensors["indoor_light"]["level"])

        elif topic[-1] == "outdoor":
            print("Received outdoor command")
            payload = json.loads(msg.payload)
            sensors["outside_light"]["active"] = int(payload["mode"])
            if sensors["outside_light"]["active"] == 1:
                pwm_outdoor.ChangeDutyCycle(sensors["outside_light"]["level"])
            else:
                pwm_outdoor.ChangeDutyCycle(0)

        elif topic[-1] == "outdoor-level":
            print("Received outdoor level command")
            payload = json.loads(msg.payload)
            sensors["outside_light"]["level"] = int(payload["mode"])
            if sensors["outside_light"]["active"] == 1:
                pwm_outdoor.ChangeDutyCycle(sensors["outside_light"]["level"])

        elif topic[-1] == "blind":
            print("Received blind command")
            payload = json.loads(msg.payload)
            sensors["blind"]["is_open"] = int(payload["mode"])
            if sensors["blind"]["is_open"] == 0:
                change_servo_pos(0)
            elif sensors["blind"]["is_open"] == 1:
                change_servo_pos(180)

        elif topic[-1] == "blind-level":
            print("Received blind level command")
            payload = json.loads(msg.payload)
            sensors["blind"]["level"] = int(payload["mode"])
            change_servo_pos(int(payload["mode"]))


def on_publish(client, userdata, result):
    pass


def connect_mqtt():
    global MQTT_SERVER, MQTT_PORT
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message

    client.will_set(last_will_topic, payload="Raspberry has disconnected", qos=0, retain=False)
    client.connect(MQTT_SERVER, MQTT_PORT, 60)


if __name__ == "__main__":
    MQTT_SERVER = "34.159.22.233"
    MQTT_PORT = 1884
    is_connected = False

    sensors = {
        "indoor_light": {
            "active": 0,
            "level": random.randint(0, 100)
        },
        "outside_light": {
            "active": 0,
            "level": random.randint(0, 100)
        },
        "blind": {
            "is_open": 1,
            "level": random.randint(0, 180)
        },
        "air_conditioner": {
            "active": random.randint(0, 2),
            "level": random.randint(10, 30)
        },
        "presence": {
            "active": True,
            "detected": 0
        },
        "temperature": {
            "active": True,
            "temperature": random.randint(0, 40)
        }
    }

    room_number = "Room1"
    air_conditioner_op_mode = "local"
    CONFIG_TOPIC = f"hotel/rooms/{room_number}/config"
    telemetry_topic = f"hotel/rooms/{room_number}/telemetry/"

    presence_topic = f"{telemetry_topic}presence"
    temperature_topic = f"{telemetry_topic}temperature"
    air_conditioner_mode_topic = f"{telemetry_topic}air-conditioner-mode"
    air_conditioner_level_topic = f"{telemetry_topic}air-conditioner-level"
    blind_mode_topic = f"{telemetry_topic}blind-mode"
    blind_level_topic = f"{telemetry_topic}blind-level"
    indoor_mode_topic = f"{telemetry_topic}indoor-mode"
    indoor_level_topic = f"{telemetry_topic}indoor-level"
    outdoor_mode_topic = f"{telemetry_topic}outdoor-mode"
    outdoor_level_topic = f"{telemetry_topic}outdoor-level"
    last_will_topic = f"hotel/rooms/{room_number}/telemetry/last-will"

    command_topic = f"hotel/rooms/{room_number}/command/+"
    # pwm = None
    # servo_pwm = None
    motor_pin_a = 24
    motor_pin_b = 23
    motor_pin_energy = 25
    servo_pin = 18

    red_pin = 13
    green_pin = 20
    blue_pin = 12
    button_pin = 16
    indoor_light_pin = 21
    outdoor_light_pin = 5
    dht_pin = 4

    color = ""
    kill = False
    sem_color = threading.Semaphore(2)
    sem_air_conditioner = threading.Semaphore(3)
    sem_presence = threading.Semaphore(5)
    setup()

    client = mqtt.Client()
    connect_mqtt()
    client.loop_start()
    client.publish(CONFIG_TOPIC, payload=room_number, qos=0, retain=False)
    print(f"Sent room number {room_number}, to topic {CONFIG_TOPIC}")

    try:
        while True:
            motor_thread = threading.Thread(target=motor)
            rgb_thread = threading.Thread(target=led)
            sensor_thread = threading.Thread(target=weather_sensor)

            motor_thread.start()
            rgb_thread.start()
            sensor_thread.start()

            while not kill:
                sem_presence.acquire()
                presence = json.dumps({"value": sensors["presence"]["detected"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(presence_topic, payload=presence, qos=0, retain=False)
                print(f'Published Presence {sensors["presence"]["detected"]}')
                sem_presence.release()

                temperature_value = json.dumps(
                    {"value": sensors["temperature"]["temperature"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(temperature_topic, payload=temperature_value, qos=0, retain=False)
                print(f'Published Temperature {sensors["temperature"]["temperature"]}')

                sem_air_conditioner.acquire()
                air_conditioner_mode = json.dumps(
                    {"value": sensors["air_conditioner"]["active"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(air_conditioner_mode_topic, payload=air_conditioner_mode, qos=0, retain=False)
                print(f'Published AC mode{sensors["air_conditioner"]["active"]}')
                sem_air_conditioner.release()

                air_conditioner_level = json.dumps(
                    {"value": sensors["air_conditioner"]["level"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(air_conditioner_level_topic, payload=air_conditioner_level, qos=0, retain=False)
                print(f'Published AC level {sensors["air_conditioner"]["level"]}')

                blind_mode = json.dumps({"value": sensors["blind"]["is_open"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(blind_mode_topic, payload=blind_mode, qos=0, retain=False)
                print(f'Published Blind mode{sensors["blind"]["is_open"]}')

                blind_level = json.dumps({"value": sensors["blind"]["level"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(blind_level_topic, payload=blind_level, qos=0, retain=False)
                print(f'Published Blind level {sensors["blind"]["level"]}')

                indoor_light_mode = json.dumps(
                    {"value": sensors["indoor_light"]["active"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(indoor_mode_topic, payload=indoor_light_mode, qos=0, retain=False)
                print(f'Published Indoor Light mode{sensors["indoor_light"]["active"]}')

                indoor_level = json.dumps({"value": sensors["indoor_light"]["level"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(indoor_level_topic, payload=indoor_level, qos=0, retain=False)
                print(f'Published Indoor Light level {sensors["indoor_light"]["level"]}')

                outdoor_light_mode = json.dumps(
                    {"value": sensors["outside_light"]["active"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(outdoor_mode_topic, payload=outdoor_light_mode, qos=0, retain=False)
                print(f'Published Outdoor Light mode{sensors["outside_light"]["active"]}')

                outdoor_light_level = json.dumps(
                    {"value": sensors["outside_light"]["level"], "timestamp": str(datetime.datetime.utcnow())})
                client.publish(outdoor_level_topic, payload=outdoor_light_level, qos=0, retain=False)
                print(f'Published Outdoor Light level {sensors["outside_light"]["level"]}')
                time.sleep(5)

            motor_thread.join()
            rgb_thread.join()
            sensor_thread.join()

    except KeyboardInterrupt as ex:
        print(f"{ex}\n")
        kill = True
        destroy()
    client.loop_stop()
