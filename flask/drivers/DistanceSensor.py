# Presuming it's the IR bricklet, sample code here:
# https://www.tinkerforge.com/en/doc/Software/Bricklets/DistanceIR_Bricklet_Python.html
# There's a nice callback structure and all sorts
# See the "Threshold" example

import time, datetime
import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_distance_ir import BrickletDistanceIR
from tinkerforge.bricklet_distance_ir_v2 import BrickletDistanceIRV2
from tf_device_ids import deviceIdentifiersList
# from apscheduler.schedulers.background import BackgroundScheduler
import os
import threading
import logging
import Settings
import random
import numpy as np

HOST = os.environ.get("BRICKD_HOST", "127.0.0.1")
PORT = 4223
_TICK_TIME = 1
_DELAY = 20
_DEBOUNCE_TIME = 8000 # in ms
_ENTRY_CALLBACK_PERIOD = 200 # in ms
_EXIT_CALLBACK_PERIOD = 200 # in ms
DEBUG = True

def logger(message):
    print("DISTANCE SENSOR: " + str(message))

class DistanceSensor:
    def __init__(self, dist, scheduler):
        self.threshold_distance = dist
        self.ipcon = None
        self.device = None
        self.tfIDs = []
        self.triggered = False
        self.deviceIDs = [ i[0] for i in deviceIdentifiersList ]
        self.scheduler = None
        self.idle_scheduler = None
        self.idle_job = None
        self.counter = _DELAY
        self.distance = 200.0
        # self.dmx = None
        # self.dmxShow = False
        self.scheduler = scheduler

        if dist:
            self.setThresholdFromSettings()

        if self.threshold_distance:
            self.poll()
        else:
            logger("Test distance sensor created")

    def setThresholdFromSettings(self):
        try:
            d = self.loadSettings()
            self.threshold_distance = d
            logger("Threshold set to: " + str(d) + "cm")
        except Exception as e:
            logger("ERROR: could not get distance setting from the usb stick, using default value ..." + e)

    def getIdentifier(self, ID):
        deviceType = ""
        for t in range(len(self.deviceIDs)):
            if ID[1]==deviceIdentifiersList[t][0]:
                deviceType = deviceIdentifiersList[t][1]
        return(deviceType)

    def loadSettings(self):
        settings_json = Settings.get_settings()
        settings_json = settings_json.copy()
        print("Distance threshold in settings: ", settings_json["detection_distance"])
        return int(settings_json["detection_distance"])

     # Tinkerforge sensors enumeration
    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version,
                    device_identifier, enumeration_type):
        self.tfIDs.append([uid, device_identifier])

    def tick(self):
        if DEBUG:
            # print("Triggered: " + str(self.triggered) + " | " + "DMX Show: " + str(self.dmxShow) + " | " + "Distance: " + str(self.distance) + " | " + "Counter: " + str(self.counter))
            print("Triggered: " + str(self.triggered) + " | " + "Distance: " + str(self.distance) + " | " + "Counter: " + str(self.counter))

        if self.triggered:
            self.counter = _DELAY
            # self.dmxShow = False # don't show idle lighting loop

        elif not self.triggered:
            self.counter -= 1
            if self.counter == 0:
                if DEBUG:
                    print("Stopping player")
                self.stopPlayer() # when the countdown has reached 0, stop the player
                # self.freePlayer()
                # self.dmxShow = True # show idle lighting loop
                # self.triggered = False
                self.device.set_distance_callback_configuration(_ENTRY_CALLBACK_PERIOD, True, "x", 0, 0)
            if self.counter < 0:
                self.counter = 0
                # self.dmxShow = True

        # if DEBUG:
        #     print(str(int(time.time()) % 20))
        # if self.dmxShow and ((int(time.time()) % 6)==0):# and not self.triggered:
        #     if DEBUG:
        #         print("Trigger Idle Lighting Loop")
        #     # self.triggerPlayer(path="/media/usb/uploads/idle.mp3", start_position=0, test=True)
        #     # time.sleep(10)
        #     # self.stopPlayer(test=True)
        #     # self.rebootPlayer()
        #     self.idlePlayer()

    def poll(self):
        self.ipcon = IPConnection() # Create IP connection
        self.ipcon.connect(HOST, PORT) # Connect to brickd
        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)

        # Trigger TinkerForge enumerate function
        self.ipcon.enumerate()

        time.sleep(0.7)

        # Autodetect TinkerForge bricklets
        for tf in self.tfIDs:
            if len(tf[0])<=3: # if the device UID is 3 characters it is a bricklet
                if tf[1] in self.deviceIDs:
                    print(tf[0],tf[1], self.getIdentifier(tf))
                    if tf[1] == 25: # DISTANCE IR BRICKLET
                        print("Registering %s as active Distance IR sensor 1.2" % tf[0])
                        self.device = BrickletDistanceIR(tf[0], self.ipcon) # Create device object
                        # Don't use device before ipcon is connected

                        self.device.register_callback(self.device.CALLBACK_DISTANCE, self.cb_distance)

                        # Get threshold callbacks with a debounce time of 10 seconds (10000ms)
                        # self.device.set_debounce_period(_DEBOUNCE_TIME)
                        self.device.set_distance_callback_period(_ENTRY_CALLBACK_PERIOD)
                    elif tf[1] == 2125: # DISTANCE IR BRICKLET V2.0
                        print("Registering %s as active Distance IR sensor 2.0" % tf[0])
                        self.device = BrickletDistanceIRV2(tf[0], self.ipcon) # Create device object
                        # Don't use device before ipcon is connected

                        self.device.register_callback(self.device.CALLBACK_DISTANCE, self.cb_distance_v2)

                        self.device.set_distance_callback_configuration(_ENTRY_CALLBACK_PERIOD, True, "x", 0, 0)


                    # self.scheduler = BackgroundScheduler({
                    #     'apscheduler.executors.processpool': {
                    #         'type': 'processpool',
                    #         'max_workers': '1'
                    #     }}, timezone="Europe/London")
                    self.scheduler.add_job(self.tick, 'interval', seconds=_TICK_TIME, misfire_grace_time=None , max_instances=1, coalesce=True, start_date = datetime.datetime.now()+datetime.timedelta(0,2,0))
                    # self.scheduler.add_job(self.tick, 'cron', second=_TICK_TIME, misfire_grace_time=None , max_instances=1, coalesce=False)
                    # self.scheduler.start(paused=False)

                    logging.getLogger('apscheduler').setLevel(logging.CRITICAL)


        print("Polling the TF distance sensor for distance measurement... ")
        print("Threshold distance is set to ", self.threshold_distance, "cm")

        # except Exception as e:
        #     print("ERROR: There is a problem with the Distance Sensor!")
        #     print("Why:", e)
        #     self.__del__()

    # Callback function for distance polling
    # Is only called if the distance has changed within _CALLBACK_PERIOD

    def cb_distance(self, distance):
        logger("Distance: " + str(distance/10.0) + " cm")
        d = distance/10.0
        t = None
        self.distance = d
        if d <= self.threshold_distance:
            self.triggerPlayer()
            self.device.set_distance_callback_period(_EXIT_CALLBACK_PERIOD)
            self.triggered = True
        elif d > self.threshold_distance:
            self.triggered = False

    def cb_distance_v2(self, distance):
        logger("Distance: " + str(distance/10.0) + " cm")
        d = distance/10.0
        t = None
        self.distance = d
        if d <= self.threshold_distance:
            self.triggerPlayer()
            self.device.set_distance_callback_configuration(_EXIT_CALLBACK_PERIOD, True, "x", 0, 0)
            self.triggered = True
        elif ( d > self.threshold_distance ):
            self.triggered = False

    def triggerPlayer(self, path="/media/usb/uploads/01_scentroom.mp3", start_position=0, test=False):
        try:
            if self.triggered or test:
                postFields = { \
                            'trigger' : "start", \
                            'upload_path': str(path), \
                            'start_position': str(start_position), \
                        }

                playerRes = requests.post('http://localhost:' + os.environ.get("PLAYER_PORT", "80") + '/scentroom-trigger', json=postFields)
                print("INFO: response from start: ", playerRes)
        except Exception as e:
            logging.error("HTTP issue with player trigger")
            print("Why: ", e)

    def stopPlayer(self, test=False):
        try:
            if not self.triggered or test:
                postFields = { \
                            'trigger': "stop" \
                        }

                playerRes = requests.post('http://localhost:' + os.environ.get("PLAYER_PORT", "80") + '/scentroom-trigger', json=postFields)
                print("INFO: response from stop: ", playerRes)
        except Exception as e:
            logging.error("HTTP issue with player stop")
            print("Why: ", e)

    def rebootPlayer(self):
        try:
            if not self.triggered:
                playerRes = requests.get('http://localhost:' + os.environ.get("PLAYER_PORT", "80") + '/scentroom-reboot')
                print("INFO: response from reboot: ", playerRes)
        except Exception as e:
            logging.error("HTTP issue with player reboot")
            print("Why: ", e)

    def idlePlayer(self):
        try:
            if not self.triggered:
                playerRes = requests.get('http://localhost:' + os.environ.get("PLAYER_PORT", "80") + '/scentroom-idle')
                print("INFO: response from idle: ", playerRes)
        except Exception as e:
            logging.error("HTTP issue with player idle")
            print("Why: ", e)

    def __del__(self):
        try:
            self.ipcon.disconnect()
        except Exception as e:
            logger("Cannot destroy the Tinkerforge IP connection gracefully...")
            print("Why: ", e)
            logger("It's likely there was no connection to begin with!")
            logger("Distance sensor ")
        self.device = None
