# Presuming it's the IR bricklet, sample code here:
# https://www.tinkerforge.com/en/doc/Software/Bricklets/DistanceIR_Bricklet_Python.html
# There's a nice callback structure and all sorts
# See the "Threshold" example

from Relay import Relay
import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_distance_ir import BrickletDistanceIR
import os

HOST = "localhost"
PORT = 4223
UID = "EuD" # Change XYZ to the UID of your Distance IR Bricklet
_DISTANCE_THRESHOLD = 30 # in cm
_DEBOUNCE_TIME = 4000 # in ms

class DistanceSensor:
    def __init__(self, dist):
        self.threshold_distance = dist
        self.relay = Relay()
        self.ipcon = None
        self.device = None
        self.poll()

    def startCallbackSet(self):
        self.device.register_callback(self.device.CALLBACK_DISTANCE_REACHED, self.cb_distance_reached)
        self.device.set_distance_callback_threshold("<", _DISTANCE_THRESHOLD*10, 0)

    def stopCallbackSet(self):
        self.device.register_callback(self.device.CALLBACK_DISTANCE_REACHED, self.cb_distance_surpassed)
        self.device.set_distance_callback_threshold(">", _DISTANCE_THRESHOLD*10, 0)

    def poll(self):
        try:
            self.ipcon = IPConnection() # Create IP connection
            self.device = BrickletDistanceIR(UID, self.ipcon) # Create device object

            self.ipcon.connect(HOST, PORT) # Connect to brickd
            # Don't use device before ipcon is connected

            # Get threshold callbacks with a debounce time of 10 seconds (10000ms)
            self.device.set_debounce_period(_DEBOUNCE_TIME)
            self.startCallbackSet()

            print("Polling the TF distance sensor for distance measurement... ")
            print("Threshold distance is set to ", _DISTANCE_THRESHOLD, "cm")

        except Exception as e:
            print("ERROR: There is a problem with the Distance Sensor!")
            print("Why:", e)
            self.__del__()

    # Callback function for distance reached callback
    def cb_distance_reached(self, distance):
        print("INFO: TRIGGER -> STARTING PLAYER")
        print("Distance: " + str(distance/10.0) + " cm")
        self.stopCallbackSet()
        self.triggerPlayer()

    def cb_distance_surpassed(self, distance):
        print("INFO: TRIGGER -> STOPPING PLAYER")
        print("Distance: " + str(distance/10.0) + " cm")
        self.startCallbackSet()
        self.stopPlayer()

    def triggerPlayer(self, path="/media/usb/uploads/01_scentroom.mp3", start_position=0):
        postFields = { \
                    'trigger' : "start", \
                    'upload_path': str(path), \
                    'start_position': str(start_position), \
                }

        playerRes = requests.post('http://localhost:' + os.environ.get("PLAYER_PORT", "80") + '/scentroom-trigger', json=postFields)
        print("INFO: res from start: ", playerRes)

    def stopPlayer(self):
        postFields = { \
                    'trigger': "stop" \
                }

        playerRes = requests.post('http://localhost:' + os.environ.get("PLAYER_PORT", "80") + '/scentroom-trigger', json=postFields)
        print("INFO: res from stop: ", playerRes)

    def __del__(self):
        self.ipcon.disconnect()
        self.device = None
    