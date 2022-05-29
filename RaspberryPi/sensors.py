import random
import json
import time
import datetime
import threading
import Adafruit_DHT
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from openpyxl import load_workbook


def angle_to_duty(angle):
    return angle/18 + 2


def change_servo_pos(pos):
    global pwm, servo_pwm
    if pos == 0:
        servo_pwm.ChangeDutyCycle(12.4)
    elif pos == 180:
        servo_pwm.ChangeDutyCycle(2.6)
    else:
        duty = angle_to_duty(pos)
        servo_pwm.ChangeDutyCycle(duty)


def setup():
    global pwm, servo_pwm
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

    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=button_pressed_callback, bouncetime=200)

    GPIO.output(motor_pin_b, GPIO.LOW)
    GPIO.output(motor_pin_energy, GPIO.HIGH)


def button_pressed_callback(channel):
    global sensors
    sensors["presence"]["detected"] = not sensors["presence"]["detected"]
    print(f'changed to {sensors["presence"]["detected"]}\n')


def led():
    global sensors
    GPIO.output(outdoor_light_pin, GPIO.HIGH)
    GPIO.output(indoor_light_pin, GPIO.HIGH)
    while not kill:
        if not sensors["presence"]["detected"]:
            GPIO.output(red_pin, GPIO.LOW)
            GPIO.output(green_pin, GPIO.LOW)
            GPIO.output(blue_pin, GPIO.LOW)
            time.sleep(1)
            continue

        sem.acquire()
        global color
        if color == "blue":
            #print("led blue")
            GPIO.output(red_pin, GPIO.LOW)
            GPIO.output(green_pin, GPIO.LOW)
            GPIO.output(blue_pin, GPIO.HIGH)
            time.sleep(1)
        elif color == "green":
            #print("led green")
            GPIO.output(red_pin, GPIO.LOW)
            GPIO.output(green_pin, GPIO.HIGH)
            GPIO.output(blue_pin, GPIO.LOW)
            time.sleep(1)

        elif color == "red":
            #print("led red")
            GPIO.output(red_pin, GPIO.HIGH)
            GPIO.output(green_pin, GPIO.LOW)
            GPIO.output(blue_pin, GPIO.LOW)
            time.sleep(1)
        sem.release()


def motor():
    global pwm, servo_pwm, color, sensors
    color = "green"
    while not kill:
        if not sensors["presence"]["detected"]:
            pwm.ChangeDutyCycle(0)
            time.sleep(1)
            continue

        temperature = sensors["temperature"]["temperature"]
        if temperature:
            upper_bound = 24
            lower_bound = 21
            if temperature and lower_bound < temperature < upper_bound:
                pwm.ChangeDutyCycle(0)
                sem.acquire()
                color = "green"
                sem.release()
            elif temperature:
                if temperature < lower_bound:
                    cycle = abs(lower_bound-temperature) * 10
                    if cycle > 100:
                        cycle = 100
                    #print(f"red {cycle=}")
                    sem.acquire()
                    color = "red"
                    sem.release()
                    pwm.ChangeDutyCycle(cycle)
                elif temperature > upper_bound:
                    cycle = abs(temperature - upper_bound) * 10
                    if cycle > 100:
                        cycle = 100
                    #print(f"blue {cycle=}")
                    sem.acquire()
                    color = "blue"
                    sem.release()
                    pwm.ChangeDutyCycle(cycle)


def weather_sensor():
    global sensors
    wb = load_workbook('/home/pi/Desktop/weather.xlsx')
    sheet = wb['Sheet1']
    current_hum = 0
    current_temp = 0
    while not kill:
        if not sensors["presence"]["detected"]:
            time.sleep(1)
            continue

        today = datetime.date.today()
        now = datetime.datetime.now().time()
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, dht_pin)
        if humidity and temperature:
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


def blind():
    while not kill:
        angle = random.randint(0, 180)
        print(f"{angle=}")
        change_servo_pos(angle)
        time.sleep(1)


def destroy():
    GPIO.cleanup()


def on_connect(client, userdata, flags, rc):
    global room_number
    print("Digital Twin connected with code:", rc)
    client.publish(CONFIG_TOPIC, payload=room_number, qos=0, retain=False)
    print("Sent room number", room_number, "to topic", CONFIG_TOPIC)


def on_message(client, userdata, msg):
    print(f"Message received in MQTT 1884 {msg.topic} with message {msg.payload.decode()}")
    topic = msg.topic.split('/')
    if "config" in topic:
        global is_connected
        is_connected = True
    elif "command" in topic:
        if topic[-1] == "air-conditioner":
            global sensors
            print("Received AC command")
            payload = json.loads(msg.payload)
            sensors["air_conditioner"]["level"] = payload["mode"]

        if topic[-1] == "indoor":
            global sensors
            print("Received indoor command")
            payload = json.loads(msg.payload)
            sensors["indoor_light"]["level"] = payload["mode"]

        if topic[-1] == "outdoor":
            global sensors
            print("Received outdoor command")
            payload = json.loads(msg.payload)
            sensors["outside_light"]["level"] = payload["mode"]


def on_publish(client, userdata, result):
    print("data published")


def connect_mqtt():
    global MQTT_SERVER, MQTT_PORT
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)


if __name__ == "__main__":
    MQTT_SERVER = "34.141.18.88"
    MQTT_PORT = 1884
    is_connected = False

    room_number = "Room1"
    CONFIG_TOPIC = f"hotel/rooms/{room_number}/config"
    TELEMETRY_TOPIC = f"hotel/rooms/{room_number}/telemetry/"
    TEMPERATURE_TOPIC = f"{TELEMETRY_TOPIC}temperature"
    AIR_CONDITIONER_TOPIC = f"{TELEMETRY_TOPIC}air_conditioner"
    BLIND_TOPIC = f"{TELEMETRY_TOPIC}blind"
    PRESENCE_TOPIC = f"{TELEMETRY_TOPIC}presence"
    INDOOR_TOPIC = f"{TELEMETRY_TOPIC}indoor"
    OUTDOOR_TOPIC = f"{TELEMETRY_TOPIC}outdoor"
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
            "level": random.randint(0, 180)
        },
        "air_conditioner": {
            "active": random.randint(0, 2),
            "level": random.randint(10, 30),
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
    sem = threading.Semaphore(2)

    client = mqtt.Client()
    connect_mqtt()
    client.loop_start()
    client.publish(CONFIG_TOPIC, payload=room_number, qos=0, retain=False)
    print(f"Sent room number {room_number}, to topic {CONFIG_TOPIC}")

    setup()
    try:
        while True:
            motor_thread = threading.Thread(target=motor)
            rgb_thread = threading.Thread(target=led)
            sensor_thread = threading.Thread(target=weather_sensor)
            blind_thread = threading.Thread(target=blind)

            motor_thread.start()
            rgb_thread.start()
            sensor_thread.start()
            blind_thread.start()

            while not kill:
                client.publish(PRESENCE_TOPIC,payload=str(sensors["presence"]["detected"]),qos=0, retain=False)
                print(f'Published Presence {sensors["presence"]["detected"]}')

                client.publish(TEMPERATURE_TOPIC, payload=str(sensors["temperature"]["temperature"]),qos=0, retain=False)
                print(f'Published Temperature {sensors["temperature"]["temperature"]}')

                client.publish(AIR_CONDITIONER_TOPIC, payload=str(sensors["air_conditioner"]["level"]), qos=0, retain=False)
                print(f'Published AC {sensors["air_conditioner"]["level"]}')

                time.sleep(5)

            motor_thread.join()
            rgb_thread.join()
            sensor_thread.join()
            blind_thread.join()

    except KeyboardInterrupt as ex:
        print(f"{ex}\n")
        kill = True
        destroy()
    client.loop_stop()
