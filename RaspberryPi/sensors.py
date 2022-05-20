import RPi.GPIO as GPIO
import threading
import time
import Adafruit_DHT
import datetime
import os
import paho.mqtt.client as mqtt
import random
from datetime import date
from openpyxl import load_workbook
from time import sleep

MQTT_SERVER = "34.141.108.113"
MQTT_PORT = 1884
room_number = "Room1"
TELEMETRY_TOPIC = f"hotel/physical_rooms/{room_number}/telemetry/"
TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "temperature"
AIR_CONDITIONER_TOPIC = TELEMETRY_TOPIC + "air_conditioner"
BLIND_TOPIC = TELEMETRY_TOPIC + "blind"
CONFIG_TOPIC = f"hotel/physical_rooms/{room_number}/config"

GPIO.setwarnings(False)
Motor1A = 24
Motor1B = 23
Motor1E = 25

GPIO.setmode(GPIO.BCM)
GPIO.setup(Motor1A,GPIO.OUT)
pwm = GPIO.PWM(Motor1A,100)
pwm.start(0)

color = ""
presence = False
kill = False
humidity = 0
temperature = 0

redPin = 13
greenPin = 20
bluePin = 12
button = 16

sem = threading.Semaphore(2)


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(Motor1A,GPIO.OUT)
    GPIO.setup(Motor1B,GPIO.OUT)
    GPIO.setup(Motor1E, GPIO.OUT)

    GPIO.setup(redPin, GPIO.OUT)
    GPIO.setup(greenPin, GPIO.OUT)
    GPIO.setup(bluePin, GPIO.OUT)

    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(button, GPIO.FALLING, callback=button_pressed_callback, bouncetime=200)

    GPIO.output(Motor1B, GPIO.LOW)
    GPIO.output(Motor1E, GPIO.HIGH)


def button_pressed_callback(channel):
    global presence
    presence = not presence
    print(f"changed to {presence}\n")


def led():
    while not kill:
        if not presence:
            GPIO.output(redPin, GPIO.LOW)
            GPIO.output(greenPin, GPIO.LOW)
            GPIO.output(bluePin, GPIO.LOW)
            continue
        sem.acquire()
        if color == "blue":
            print("led blue")
            GPIO.output(redPin, GPIO.LOW)
            GPIO.output(greenPin, GPIO.LOW)
            GPIO.output(bluePin, GPIO.HIGH)
            sleep(1)
        elif color == "green":
            print("led green")
            GPIO.output(redPin, GPIO.LOW)
            GPIO.output(greenPin, GPIO.HIGH)
            GPIO.output(bluePin, GPIO.LOW)
            sleep(1)

        elif color == "red":
            print("led red")
            GPIO.output(redPin, GPIO.HIGH)
            GPIO.output(greenPin, GPIO.LOW)
            GPIO.output(bluePin, GPIO.LOW)
            sleep(1)
        sem.release()


def motor():
    global color
    color = "green"
    while not kill:
        if not presence:
            pwm.ChangeDutyCycle(0)
            continue
        if temperature:
            upper_bound = 24
            lower_bound = 21
            print(temperature)
            if temperature and temperature > lower_bound and temperature < upper_bound:
                pwm.ChangeDutyCycle(0)
                sem.acquire()
                color = "green"
                sem.release()
            elif temperature:
                if temperature < lower_bound:
                    cycle = abs(lower_bound-temperature) * 10
                    if cycle > 100:
                        cycle = 100
                    print(f"red {cycle=}")
                    sem.acquire()
                    color = "red"
                    sem.release()
                    pwm.ChangeDutyCycle(cycle)
                elif temperature > upper_bound:
                    cycle = abs(temperature - upper_bound) * 10
                    if cycle > 100:
                        cycle = 100
                    print(f"blue {cycle=}")
                    sem.acquire()
                    color = "blue"
                    sem.release()
                    pwm.ChangeDutyCycle(cycle)


def weatherSensor():
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 4
    wb = load_workbook('/home/pi/Desktop/weather.xlsx')
    sheet = wb['Sheet1']
    current_hum = 0
    current_temp = 0
    while not kill:
        #if not presence:
            #continue
        global temperature
        today = date.today()
        now = datetime.datetime.now().time()
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        dif_humidity = abs(current_hum - humidity)
        dif_temperature = abs(current_temp - temperature)
        if dif_humidity > 0.1 and dif_temperature > 0.1:
            row = (today, now, temperature, "961.9", humidity)
            sheet.append(row)
            wb.save('/home/pi/Desktop/weather.xlsx')
            print("Temp = {0: 0.1f}C Humidity = {1: 0.1f} %".format(temperature, humidity))
            current_hum = humidity
            current_temp = temperature

        if humidity and temperature:
            print("Temp = {0: 0.1f}C Humidity = {1: 0.1f} %".format(temperature, humidity))
        time.sleep(1)


def destroy():
    GPIO.cleanup()


def on_connect(client, userdata, flags, rc):
    global room_number
    print("Digital Twin connected with code:", rc)
    client.publish(CONFIG_TOPIC, payload=room_number, qos=0, retain=False)
    print("Sent room number", room_number, "to topic", CONFIG_TOPIC)
    # client.subscribe(CONFIG_TOPIC + "/room")
    # print(f"Subscribed to, {CONFIG_TOPIC}/room")


def on_message(client, userdata, msg):
    global room_number
    room_number = msg.payload.decode()
    print("Room number received as:", room_number)


def on_publish(client, userdata, result):
    pass
    print("data published")


def connect_mqtt():
    global MQTT_SERVER, MQTT_PORT
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)


if __name__ == "__main__":
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
            sensor_thread = threading.Thread(target=weatherSensor)
            motor_thread.start()
            rgb_thread.start()
            sensor_thread.start()
            while not kill:
                client.publish(TEMPERATURE_TOPIC, payload=str(temperature), qos=0, retain=False)
                print("Published", str(temperature))
                time.sleep(5)
            motor_thread.join()
            rgb_thread.join()
            sensor_thread.join()

    except KeyboardInterrupt:
        print("KeyboardInterrupt\n")
        kill = True
        destroy()
    client.loop_stop()


