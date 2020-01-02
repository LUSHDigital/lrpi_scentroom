
import sys
sys.path.append('drivers')
sys.path.append('events')

# Vendors
from flask import Flask,abort,render_template,request,redirect,url_for, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug import secure_filename
import os
import json
import logging
import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
from apscheduler.schedulers.background import BackgroundScheduler

# Local
from DistanceSensor import DistanceSensor
from LightingEvent import LightingEvent
import Settings

# cli = sys.modules['flask.cli']
# cli.show_server_banner = lambda *x: None

app = Flask(__name__, static_folder='build/static', template_folder="build")
logging.basicConfig(level=logging.DEBUG)

scheduler = BackgroundScheduler({
    'apscheduler.executors.processpool': {
        'type': 'processpool',
        'max_workers': '1'
    }}, timezone="Europe/London")

scheduler.start(paused=False)

distance_sensor = None

# Need cors to resolve cors conflict
cors = CORS(app)

# Restrict file types saved to uploads directory
ALLOWED_EXTENSIONS = set(['mp3', 'mp4', 'json'])
_FALLBACK_THRESHOLD_DISTANCE = 145
_JSON_INDENT = 2
_CONTENT_FILENAME = "content.json"

# Create upload directory to save files to
uploads_dir = os.path.join('/media/usb/', 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

def logger(message):
    app.logger.info("INFO: " + message)
    sys.stdout.flush()

def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower()

def get_name(filename):
    return filename.rsplit('.', 1)[0].lower()

# Checks filename extension type
def allowed_file(filename):
	return '.' in filename and get_extension(filename) in ALLOWED_EXTENSIONS

#Function appends col hex values to .srt file type
def lightingEvent(col_hex_val):
    scentroom_event = LightingEvent(col_hex_val)
    scentroom_event.to_json_file()
    scentroom_event.to_idle_mp3(uploads_dir)
    scentroom_event.to_idle_srt(str(uploads_dir))
    return scentroom_event.to_srt(str(uploads_dir))


# Serve React app @ https://github.com/LUSHDigital/lrpi_scentroom_ui
@app.route('/')
def serve():
    return send_from_directory('build/', 'index.html')


# Handles POST request of file
@app.route('/upload-file', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            #No file part
            return jsonify({'response': 404, 'audio_saved': False, 'description': 'No file found', 'path': request.url})

        #Gets file from form data
        file = request.files['file']

        if file.filename == '':
            #No file selected for uploading
            return jsonify({'response': 500, 'audio_saved': False, 'description': 'No file selected', 'path': request.url})

        if file and allowed_file(file.filename):
            #Generate secure file name
            filename = secure_filename("01_scentroom." + get_extension(file.filename))
            print("Saving file as... ", filename)
            #Save file to dir
            file.save(os.path.join(uploads_dir, filename))
            #File successfully uploaded

            with open(os.path.join(uploads_dir, _CONTENT_FILENAME), 'r+') as f:
                content = json.load(f)
                content['real_audio_name'] = file.filename # <--- add `id` value.
                f.seek(0)        # <--- should reset file position to the beginning.
                json.dump(content, f, indent=_JSON_INDENT)
                f.truncate()     # remove remaining part

            return jsonify({'response': 200, 'audio_saved': True, 'description': 'Audio Saved', 'path': request.url})
        else:
            return jsonify({'response': 500, 'audio_saved': False, 'description': 'File type not allowed - accepted types are mp3, JSON', 'path': request.url})

    return jsonify({'response': 500, 'audio_saved': False, 'description': 'Could not save audio file', 'path': request.url})



# Handles POST request of colour value
@app.route('/upload-colour', methods=['POST'])
def upload_col():
    if request.method == 'POST':

        #Get col value from form data
        colour = request.form.get('colour')

        if colour is not None:
            if lightingEvent(colour):
                return jsonify({'response' : 200, 'col_saved': True, 'description': 'Colour saved', 'path': request.url})
        else:
            return jsonify({'response': 500, 'col_saved': False, 'description': 'Colour value non type', 'path': request.url})

    return jsonify({'response': 500, 'col_saved': False, 'description': 'Colour upload failed', 'path': request.url})


# Handles POST request of colour value
@app.route('/test-start', methods=['GET'])
def testStart():
    if request.method == 'GET':
        # test_distance_sensor = DistanceSensor(None, scheduler)
        # test_distance_sensor.triggerPlayer(test=True)
        distance_sensor.triggerPlayer(test=True)
        return jsonify({'response': 200, 'message': 'Test started!'})

    return jsonify({'response': 500, 'error': 'Something went wrong when trying to START the test'})

@app.route('/test-kill', methods=['GET'])
def testKill():
    if request.method == 'GET':
        # test_distance_sensor = DistanceSensor(None, scheduler)
        # test_distance_sensor.stopPlayer(test=True)
        distance_sensor.stopPlayer(test=True)
        return jsonify({'response': 200, 'message': 'Test ended!'})

    return jsonify({'response': 500, 'error': 'Something went wrong when trying to KILL the test'})


@app.route('/status', methods=['GET'])
def status():
    if request.method == 'GET':

        health = "healthy"
        settings = Settings.get_json_settings()

        with open(os.path.join(uploads_dir, _CONTENT_FILENAME), 'r') as f:
            content = json.load(f)
            color = content['color_hex']
            real_audio_name = content['real_audio_name']

        # Error handling here...

        return jsonify({'status': health, 'response': 200, 'color': color, 'track_name': real_audio_name, 'hostname': settings['host_name'] })

    return jsonify({'response': 500, 'error': 'Cannot get status. Please use GET'})

# Courtesy of:
# https://stackoverflow.com/questions/24750137/restarting-host-from-docker-container
@app.route('/reboot', methods=['GET'])
def reboot():
    if request.method == 'GET':
        logging.warning("Reboot has been called! There will be no response from this call!")
        try:
            os.system("echo b > /sysrq")
        except Exception as e:
            return jsonify({'response': 500, 'error': 'Something went wrong with reboot. It could be time for a hard reset...'})

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'response':404, 'description': 'Page Not Found' + str(e)})

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'response':500, 'description': 'Internal Server Error' + str(e)})

if __name__ == '__main__':
    logger("Welcome to the Scentroom!")
    logger("Uploads directory is: " + uploads_dir)

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        distance_sensor = DistanceSensor(_FALLBACK_THRESHOLD_DISTANCE, scheduler)

    # create content.json file if it doesn't exist
    content_filename = os.path.join(uploads_dir,_CONTENT_FILENAME)
    if not os.path.exists(content_filename):
        f = open(content_filename, "w")
        f.write("{\n\"real_audio_name\": \"\",\n\"color_hex\": \"#0000ff\"\n}\n")
        f.close()

    # disabling flask reloader as it triggers apscheduler events twice
    # https://stackoverflow.com/questions/14874782/apscheduler-in-flask-executes-twice
    app.run(use_reloader=False, debug=True, port=os.environ.get("PORT", "5000"), host='0.0.0.0')
