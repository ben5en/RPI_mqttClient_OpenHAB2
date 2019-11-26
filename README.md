# RPI_mqttClient_OpenHAB2
Script for temperature reading and WS2812b handling via MQTT in an openHAB2 environment

This is the software running on an RPI 3 Model A+ I am using for a OpenHAB2 Raspberry Pi Touch Display
![hackaday.io](https://cdn.hackaday.io/images/9138331574329417291.JPG)

Here are the steps I did to get this up an running:
1. flashed a new raspbian buster on SD
2. configured WIFI & SSH before the first start like done here: https://learn.adafruit.com/raspberry-pi-zero-creation/text-file-editing
3. pluged in the SD card and powered up the RPI
4. looked up for e.g. the router for the IP of the RPI
5. connected via SSH
6. changed the standard password https://www.raspberrypi.org/documentation/linux/usage/users.md
7. run:
  sudo apt-get update
  sudo apt-get full upgrade
8. installed remote desktop protocol:
  sudo apt install xrdp
9. made local settings (timezone etc.) via RDP
10. installed Adafruit blinka like, but with root support (sudo): https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi
11. installed Adafruit BMP280 lib like: https://learn.adafruit.com/adafruit-bmp280-barometric-pressure-plus-temperature-sensor-breakout/circuitpython-test
12. installed Adafruit Neopixels like: https://learn.adafruit.com/adafruit-neopixel-uberguide/python-circuitpython
13. installed paho-mqtt:
  sudo pip3 install paho-mqtt

14. enabled script to run with autostart (edit rc.local)
