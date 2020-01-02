import os
import json

_SETTINGS = None
SETTINGS_PATH = "/media/usb/settings.json"


def get_settings():

    global _SETTINGS

    if _SETTINGS is None:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH) as f:
                _SETTINGS = get_combined_settings()

    return _SETTINGS



def get_combined_settings():

    """
    In order of precedence:
    json
    envar
    default
    """

    json_settings = get_json_settings()
    env_settings = get_evn_settings()

    combined = env_settings.copy()

    for k in env_settings.keys():
        if json_settings.get(k):
            combined[k] = json_settings[k]

    print("***********  SETTINGS  ***********")
    print(json.dumps(combined, indent=4))

    return combined


def get_json_settings():

    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH) as f:
            return json.loads(f.read())
    return None


def get_evn_settings():

    settings = {}
    settings["name"] = os.environ.get("NAME", "?")
    settings["hostname"] = os.environ.get("HOSTNAME", "?")
    settings["debug"] = os.environ.get("DEBUG") == "true"
    settings["dmx_brightness"] = os.environ.get("DMX_BRIGHTNESS", "254")
    settings["detection_distance"] = int(os.environ.get("DETECTION_DISTANCE", "150"))
    return settings