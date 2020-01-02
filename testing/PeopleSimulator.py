import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
from time import sleep
import random

_TEST_PLAYER_URL = 'http://192.168.0.56:8080'
_TEST_SCENTROOM_URL = 'http://192.168.0.56'

PLAYER_DIRECT = False
SCENTROOM_DIRECT = True

def triggerPlayer(path="/media/usb/uploads/01_scentroom.mp3", start_position=0, test=False):
    postFields = { \
                'trigger' : "start", \
                'upload_path': str(path), \
                'start_position': str(start_position), \
            }

    playerRes = requests.post(_TEST_PLAYER_URL + '/scentroom-trigger', json=postFields)
    print("INFO: res from start: ", playerRes)

def stopPlayer(test=False):
    postFields = { \
                'trigger': "stop" \
            }

    playerRes = requests.post(_TEST_PLAYER_URL + '/scentroom-trigger', json=postFields)
    print("INFO: res from stop: ", playerRes)

def startThroughScent():
    requests.get(_TEST_SCENTROOM_URL + '/test-start')

def stopThroughScent():
    requests.get(_TEST_SCENTROOM_URL + '/test-kill')


while True:
    if PLAYER_DIRECT:
        triggerPlayer()
    elif SCENTROOM_DIRECT:
        startThroughScent()
    sleep(random.uniform(0, 2))
    if PLAYER_DIRECT:
        stopPlayer()
    elif SCENTROOM_DIRECT:
        stopThroughScent()
    sleep(random.uniform(0, 0.5))

