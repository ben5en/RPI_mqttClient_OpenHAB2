#!/usr/bin/env python3
# ----------------------------------------------------------------------
# Info:
#
# MIT License
#
# Copyright (c) 2019 Benjamin Prescher
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
# target: Raspberry Pi (worked on RPI 3 Model A+)
# This: https://github.com/sumnerboy12/mqtt-gpio-monitor helped me a lot!
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------
import time
import sys
import os
import logging
import signal

# import for mqtt support:
import paho.mqtt.client as mqtt

# imports for bmp280 sensor on the SPI bus and the WS2812b LEDs:
import board
import digitalio # For use with SPI (CS pin)
import busio
import adafruit_bmp280
import neopixel

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# MQTT configuration:
# MQTT_USERNAME = xxx
# MQTT_PASSWORD = xxx
MQTT_PUBLISH_INTERVAL_SEC = 30
MQTT_HOST_IP = "YOUR_HOST_IP_HERE"
MQTT_PORT = 1883 # change this if needed
MQTT_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
MQTT_QOS = 2 # https://www.eclipse.org/paho/files/mqttdoc/MQTTClient/html/qos.html
MQTT_RETAIN = False
MQTT_TOPIC = "YOUR_TOPIC_HERE"
MQTT_TOPIC_IN = MQTT_TOPIC + "/WS2812b"
MQTT_TOPIC_OUT = MQTT_TOPIC + "/temperature"

# NEOPIXELS configuration:
PIXELS_NUM = 14 # type the number of LEDs in the strap
PIXELS_OUT = board.D18 # you should use D18 on a RPI

# BMP280 configuration:
BMP280_CS = board.D6 # change this corresponding your board

# ----------------------------------------------------------------------
# Initialize logging
# ----------------------------------------------------------------------
# Script name (without extension) used for config/logfile names:
APPNAME = os.path.splitext(os.path.basename(__file__))[0]
LOGFILE = os.getenv('LOGFILE', APPNAME + '.log')
LOGFORMAT = '%(asctime)-15s %(levelname)-5s %(message)s'

logging.basicConfig(filename=LOGFILE, level=logging.INFO, format=LOGFORMAT)

logging.info("STARTING " + APPNAME)
logging.info("INFO MODE")

# ----------------------------------------------------------------------
# Initialize sigterm-signal
# ----------------------------------------------------------------------
def on_signal(signum, frame):
    logging.info("Exit program on signal")
    pixels.fill((0,0,0)) # turn off LEDs
    pixels.show()
    mqttc.loop_stop()
    mqttc.disconnect()
    sys.exit(0)
    
# ----------------------------------------------------------------------
# Initialize MQTT
# ----------------------------------------------------------------------
# MQTT on_connect callback:
def on_connect(client, userdata, flags, rc):
    """
    Handle connections (or failures) to the broker.
    This is called after the client has received a CONNACK message
    from the broker in response to calling connect().
    The parameter rc is an integer giving the return code:
    0: Success
    1: Refused . unacceptable protocol version
    2: Refused . identifier rejected
    3: Refused . server unavailable
    4: Refused . bad user name or password (MQTT v3.1 broker only)
    5: Refused . not authorised (MQTT v3.1 broker only)
    
    if everything is fine, subsribe to our incomming topic(s)
    """
    if rc == 0:
        logging.info("Connected to %s:%s" % (MQTT_HOST_IP, MQTT_PORT))
        mqttc.subscribe(MQTT_TOPIC_IN, qos=MQTT_QOS)      
    elif rc == 1:
        logging.info("Connection refused - unacceptable protocol version")
    elif rc == 2:
        logging.info("Connection refused - identifier rejected")
    elif rc == 3:
        logging.info("Connection refused - server unavailable")
    elif rc == 4:
        logging.info("Connection refused - bad user name or password")
    elif rc == 5:
        logging.info("Connection refused - not authorised")
    else:
        logging.warning("Connection failed - result code %d" % (rc))

# ----------------------------------------------------------------------
# MQTT on_disconnect callback:
def on_disconnect(client, userdata, rc):
    # Handle disconnections from the broker:
    if rc == 0:
        logging.info("Clean disconnection from broker")
    else:
        logging.info("Broker connection lost. Retrying in 10s...")
        time.sleep(10)

# ----------------------------------------------------------------------
# MQTT on_message callback:
def on_message(client, userdata, message):
    # Handle incoming message:
    if message.topic == MQTT_TOPIC_IN:
        rgb = message.payload.decode("utf-8").split(",")
        pixels.fill((int(rgb[0]), int(rgb[1]), int(rgb[2])))
        pixels.show()
        
# ----------------------------------------------------------------------
# Create the MQTT client and add the callbacks:
mqttc = mqtt.Client(MQTT_CLIENT_ID, clean_session = True)
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.on_message = on_message

# Set the login details:
# mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# ----------------------------------------------------------------------
# "Main" start...
# ----------------------------------------------------------------------
# Initialize signal in
signal.signal(signal.SIGINT,  on_signal)
signal.signal(signal.SIGTERM, on_signal)

# Initialize the WS2812b LED strip:
pixels = neopixel.NeoPixel(board.D18, PIXELS_NUM)
pixels.fill((0,0,0)) # turn of LEDs at program start
pixels.show()

# Initialize the BMP280 sensor:
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
bmp_cs = digitalio.DigitalInOut(BMP280_CS)
bmp280 = adafruit_bmp280.Adafruit_BMP280_SPI(spi, bmp_cs)

time.sleep(30) # give the system some time to start-up...

# Attempt to connect
try:
    mqttc.connect(MQTT_HOST_IP, MQTT_PORT, 60)
except Exception as e:
    logging.error("Error connecting to %s:%d: %s" % (MQTT_HOST_IP, MQTT_PORT, str(e)))
    sys.exit(2)

# Let the mqtt connection run "forever"
mqttc.loop_start()

try:
    while True:
        # read temperature, round by two and transform to string:
        tempStr = str(round(bmp280.temperature, 2))
        # publish intermittently:
        mqttc.publish(MQTT_TOPIC_OUT, payload = tempStr, qos = MQTT_QOS, retain = MQTT_RETAIN)
        time.sleep(MQTT_PUBLISH_INTERVAL_SEC)
    
except KeyboardInterrupt:
    logging.info("Exit program on KeyboardISR")
    pixels.fill((0,0,0)) # turn off LEDs
    pixels.show()
    mqttc.loop_stop()
    mqttc.disconnect()
    sys.exit(0)
    
