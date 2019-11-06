# Presuming it's the IR bricklet, sample code here:
# https://www.tinkerforge.com/en/doc/Software/Bricklets/DistanceIR_Bricklet_Python.html
# There's a nice callback structure and all sorts
# See the "Threshold" example

import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_distance_ir import BrickletDistanceIR
from tf_device_ids import deviceIdentifiersList
import os
from time import sleep

HOST = os.environ.get("BRICKD_HOST", "127.0.0.1")
PORT = 4223
_DEBOUNCE_TIME = 500 # in ms

def logger(message):
    print("DISTANCE SENSOR: " + str(message))

class DistanceSensor:
    def __init__(self, dist):
        self.threshold_distance = dist
        self.ipcon = None
        self.device = None
        self.tfIDs = []
        self.deviceIDs = [i[0] for i in deviceIdentifiersList]
        if self.threshold_distance:
            self.poll()
        else: 
            logger("Test distance sensor created")

    def getIdentifier(self, ID): 
        deviceType = ""
        for t in range(len(self.deviceIDs)):
            if ID[1]==deviceIdentifiersList[t][0]:
                deviceType = deviceIdentifiersList[t][1]
        return(deviceType)

     # Tinkerforge sensors enumeration
    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version,
                    device_identifier, enumeration_type):
        self.tfIDs.append([uid, device_identifier])

    def startCallbackSet(self):
        self.device.register_callback(self.device.CALLBACK_DISTANCE_REACHED, self.cb_distance_reached)
        self.device.set_distance_callback_threshold("<", self.threshold_distance*10, 0)

    def stopCallbackSet(self):
        self.device.register_callback(self.device.CALLBACK_DISTANCE_REACHED, self.cb_distance_surpassed)
        self.device.set_distance_callback_threshold(">", self.threshold_distance*10, 0)

    def poll(self):
        try:

            self.ipcon = IPConnection() # Create IP connection
            self.ipcon.connect(HOST, PORT) # Connect to brickd
            self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)

            # Trigger Enumerate
            self.ipcon.enumerate()

            sleep(2)

            for tf in self.tfIDs:
                if len(tf[0])<=3: # if the device UID is 3 characters it is a bricklet
                    if tf[1] in self.deviceIDs:
                        print(tf[0],tf[1], self.getIdentifier(tf))
                        if tf[1] == 25: # DISTANCE IR BRICKLET
                            print("Registering %s as active Distance IR sensor 1.2" % tf[0])
                            self.device = BrickletDistanceIR(tf[0], self.ipcon) # Create device object
                            # Don't use device before ipcon is connected

                            # Get threshold callbacks with a debounce time of 10 seconds (10000ms)
                            self.device.set_debounce_period(_DEBOUNCE_TIME)
                            self.startCallbackSet()

            

            print("Polling the TF distance sensor for distance measurement... ")
            print("Threshold distance is set to ", self.threshold_distance, "cm")

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
        try:
            self.ipcon.disconnect()
        except Exception as e:
            logger("Cannot destroy the Tinkerforge IP connection gracefully...")
            print("Why: ", e)
            logger("It's likely there was no connection to begin with!")
            logger("Distance sensor ")
        self.device = None
    