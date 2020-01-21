# Presuming it's the IR bricklet, sample code here:
# https://www.tinkerforge.com/en/doc/Software/Bricklets/DistanceIR_Bricklet_Python.html
# There's a nice callback structure and all sorts
# See the "Threshold" example

import time
import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
from enum import Enum
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_distance_ir import BrickletDistanceIR
from tinkerforge.bricklet_distance_ir_v2 import BrickletDistanceIRV2
from tf_device_ids import deviceIdentifiersList
from apscheduler.schedulers.background import BackgroundScheduler
import os
import threading
import logging
import Settings


LOGGER = logging.getLogger('DistanceSensor')
logging.basicConfig(level=logging.INFO)

HOST = os.environ.get("BRICKD_HOST", "127.0.0.1")
PORT = 4223
_TICK_TIME = 1
_DELAY = 20
_DEBOUNCE_TIME = 300 # in ms
_ENTRY_CALLBACK_PERIOD = 200 # in ms
_EXIT_CALLBACK_PERIOD = 200 # in ms

# Observer this, do something when the state changes rather than
# setting random flags everywhere that are impossible to track

class SensorStates(Enum):
    IDLE = 1
    TRIGGERED = 2
    UNTRIGGERED = 3
    WAITING = 4
    RETRIGGERED = 5

class StateMachine(object):
    def __init__(self):
        self._state = SensorStates.IDLE
        self._observers = []

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        for callback in self._observers:
            callback(self._state)

    def bind_to(self, callback):
        self._observers.append(callback)

class StateWatch(object):
    def __init__(self, sm, idle, trigger, stop):
        self.sm = sm
        self.trigger = trigger
        self.stop = stop
        self.idle = idle
        self.sm.bind_to(self.stateUpdated)

    def stateUpdated(self, state):
        LOGGER.info("******************* " + str(state) + " *******************")

        if state == SensorStates.TRIGGERED:
            self.trigger()

        if state == SensorStates.RETRIGGERED:
            pass

        if state == SensorStates.UNTRIGGERED:
            self.stop()
            self.sm.state = SensorStates.IDLE

        if state == SensorStates.IDLE:
            print('Idling, fire off the idleloop request here')
            self.idle()

        if state == SensorStates.WAITING:
            pass

class DistanceSensor:
    def __init__(self, dist):
        self.threshold_distance = dist
        self.ipcon = None
        self.device = None
        self.tfIDs = []
        self.triggered = False
        self.delay_stop = False
        self.deviceIDs = [ i[0] for i in deviceIdentifiersList ]
        self.scheduler = None
        self.counter = _DELAY
        self.distance = 200.0

        # Observer/subject
        # Start the machine in IDLE mode
        self.machine = StateMachine()
        self.state_watcher = StateWatch(self.machine, self.startIdle, self.triggerPlayer, self.stopPlayer)

        if dist:
            self.setThresholdFromSettings()

        if self.threshold_distance:
            self.poll()
            self.machine.state = SensorStates.IDLE
        else:
            LOGGER.info("Test distance sensor created")

    def setThresholdFromSettings(self):
        try:
            d = self.loadSettings()
            self.threshold_distance = d
            LOGGER.info("Threshold set to: " + str(d) + "cm")
        except Exception as e:
            LOGGER.info("ERROR: could not get distance setting from the usb stick, using default value ..." + e)

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

    # Callback function for distance polling
    # Is only called if the distance has changed within _CALLBACK_PERIOD

    # This is essentially where the state transition table is...

    def cb_distance(self, distance):
        LOGGER.info("Distance: " + str(distance/10.0) + " cm")
        d = distance/10.0
        self.distance = d
        if d < self.threshold_distance:
            if self.machine.state == SensorStates.IDLE: self.machine.state = SensorStates.TRIGGERED
            if self.machine.state == SensorStates.UNTRIGGERED: self.machine.state = SensorStates.TRIGGERED
            if self.machine.state == SensorStates.WAITING: self.machine.state = SensorStates.RETRIGGERED
            if self.machine.state == SensorStates.RETRIGGERED:  self.counter = _DELAY
            if self.machine.state == SensorStates.TRIGGERED:  self.counter = _DELAY
        elif d > self.threshold_distance:
            if self.machine.state == SensorStates.TRIGGERED: self.machine.state = SensorStates.WAITING
            if self.machine.state == SensorStates.RETRIGGERED: self.machine.state = SensorStates.WAITING

    def tick(self):
        if self.machine.state == SensorStates.WAITING:
            self.counter -= 1
            LOGGER.info('Sending STOP in: ' + str(self.counter))
            if self.counter <= 0:
               self.machine.state = SensorStates.UNTRIGGERED

    def poll(self):

        self.ipcon = IPConnection() # Create IP connection
        self.ipcon.connect(HOST, PORT) # Connect to brickd
        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)

        # Trigger Enumerate
        self.ipcon.enumerate()
        time.sleep(0.7)

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
                        self.device.set_distance_callback_period(_ENTRY_CALLBACK_PERIOD)
                    elif tf[1] == 2125: # DISTANCE IR BRICKLET V2.0
                        print("Registering %s as active Distance IR sensor 2.0" % tf[0])
                        self.device = BrickletDistanceIRV2(tf[0], self.ipcon) # Create device object
                        # Don't use device before ipcon is connected

                        self.device.register_callback(self.device.CALLBACK_DISTANCE, self.cb_distance)
                        self.device.set_distance_callback_configuration(_ENTRY_CALLBACK_PERIOD, True, "x", 0, 0)

                    self.scheduler = BackgroundScheduler({
                        'apscheduler.executors.processpool': {
                            'type': 'processpool',
                            'max_workers': '1'
                        }}, timezone="Europe/London")
                    self.scheduler.add_job(self.tick, 'interval', seconds=_TICK_TIME, misfire_grace_time=5  , max_instances=1, coalesce=False)
                    self.scheduler.start(paused=False)
                    logging.getLogger('apscheduler').setLevel(logging.CRITICAL)


        print("Polling the TF distance sensor for distance measurement... ")
        print("Threshold distance is set to ", self.threshold_distance, "cm")

        # except Exception as e:
        #     print("ERROR: There is a problem with the Distance Sensor!")
        #     print("Why:", e)
        #     self.__del__()

    def triggerPlayer(self, path="/media/usb/uploads/01_scentroom.mp3", start_position=0, test=False):
        try:
            postFields = { \
                        'trigger' : "start", \
                        'upload_path': str(path), \
                        'start_position': str(start_position), \
                    }

            playerRes = requests.post('http://localhost:' + os.environ.get("PLAYER_PORT", "8080") + '/scentroom-trigger', json=postFields)
            print("INFO: res from start: ", playerRes)
        except Exception as e:
            LOGGER.error("HTTP issue with player trigger")
            LOGGER.error(e)

    def stopPlayer(self, test=False):
        try:
            postFields = { \
                'trigger': "stop" \
            }

            playerRes = requests.post('http://localhost:' + os.environ.get("PLAYER_PORT", "8080") + '/scentroom-trigger', json=postFields)
            print("INFO: res from stop: ", playerRes)
        except Exception as e:
            LOGGER.error("HTTP issue with player stop")
            LOGGER.error(e)

    def startIdle(self):
        LOGGER.info("dummy idle loop started...")

    def __del__(self):
        try:
            self.ipcon.disconnect()
        except Exception as e:
            logging.error("Cannot destroy the Tinkerforge IP connection gracefully...")
            print("Why: ", e)
            logging.error("It's likely there was no connection to begin with!")
        self.device = None
