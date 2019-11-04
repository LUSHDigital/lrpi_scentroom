
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

# Local
from DistanceSensor import DistanceSensor
from Relay import Relay
from LightingEvent import LightingEvent

app = Flask(__name__, static_folder='build/static', template_folder="build")
logging.basicConfig(level=logging.DEBUG)

# Need cors to resolve cors conflict
cors = CORS(app)

# Restrict file types saved to dircd 
ALLOWED_EXTENSIONS = set(['mp3', 'mp4', 'json'])

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


# Serve React app @ https://github.com/LUSHDigital/lrpi_scentroom_ui
@app.route('/')
def serve():
    return send_from_directory('build/', 'index.html')


# Handles POST request of file
@app.route('/uploadfile', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            #No file part
            return jsonify({'response': 404, 'audio_saved': False, 'description': 'No file found', 'path': request.url})

        #Gets file from form data
        file = request.files['file']
        realname_file = "audio_realname.json"

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

            #TODO add real filename to a text file in uploads
            with open(os.path.join(uploads_dir, realname_file), 'w') as f:
                f.write(json.dumps({'realname' : file.filename}, indent=2))

            return jsonify({'response': 200, 'audio_saved': True, 'description': 'Audio Saved', 'path': request.url})
        else:
            return jsonify({'response': 500, 'audio_saved': False, 'description': 'File type not allowed - accepted types are mp3, mp4, JSON', 'path': request.url})
    
    return jsonify({'response': 500, 'audio_saved': False, 'description': 'Could not save audio file', 'path': request.url})



# Handles POST request of colour value
@app.route('/uploadcol', methods=['POST'])
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


#Function appends col hex values to .srt file type
def lightingEvent(col_hex_val):
    scentroom_event = LightingEvent(col_hex_val)
    return scentroom_event.to_srt(str(uploads_dir))


#Function to test dummy distance sensor activation
@app.route('/start-test', methods=['POST'])
def start_test():
    if request.method == 'POST': 
        if request.POST.get('state',''):
            startPlayer()
            return jsonify({'response': 200, 'start_test': True, 'description': 'Start track and lighting event', 'path': request.url})
    
    return jsonify({'response': 500, 'start_test': False, 'description': 'Could not trigger start-test', 'path': request.url})


#Function to test dummy distance sensor deactivation
@app.route('/end-test', methods=['POST'])
def end_test():
    if request.method == 'POST': 
        if request.POST.get('state',''):
            stopPlayer()
            return jsonify({'response': 200, 'end_test': True, 'description': 'Stop track and lighting event', 'path': request.url})
    
    return jsonify({'response': 500, 'end_test': False, 'description': 'Could not trigger end-test', 'path': request.url})


#Function to start audio player
def startPlayer(self, path="/media/usb/uploads/01_scentroom.mp3", start_position=0):
    postFields = { \
        'trigger' : "start", \
        'upload_path': str(path), \
        'start_position': str(start_position), \
    }
    playerRes = requests.post('http://localhost:' + os.environ.get("PLAYER_PORT", "80") + '/scentroom-trigger', json=postFields)
    print("INFO: res from start: ", playerRes)


#Function to stop audio player
def stopPlayer(self):
    postFields = { \
        'trigger': "stop" \
    }
    playerRes = requests.post('http://localhost:' + os.environ.get("PLAYER_PORT", "80") + '/scentroom-trigger', json=postFields)
    print("INFO: res from stop: ", playerRes)


@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'response':404, 'description': 'Page Not Found' + str(e)})


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'response':500, 'description': 'Internal Server Error' + str(e)})        

if __name__ == '__main__':
    logger("Welcome to the Scentroom! Scentroom is a working title...")
    logger("Uploads directory is: " + uploads_dir)
    distance_sensor = DistanceSensor(30)
    app.run(port=os.environ.get("PORT", "5000"), host='0.0.0.0')

