
## Lush ScentRoom Flask Server

This flask server is built to statically deliver the [Lush ScentRoom React Audio File/Colour Uploader](https://github.com/LUSHDigital/lrpi_scentroom_ui) App. The flask server runs in a container behind an nginx proxy container which is set-up through docker.

### Building the docker image

To build the docker image, first, ensure you have docker installed - for instructions installing docker refer [here](https://docs.docker.com/install/).

Running the included docker file will install the dependencies of flask itself. 

### Running docker-compose on the Pi

To get the cluster running docker-compose will be used, a docker-compose.yml file is included within the repo which will start the flask and nginx containers.

In terminal navigate to the flask project directory and run: 
    $ docker-compose up -d

You should then see the terminal output to start each image and serve the flask app. 

Once complete load up `http://0.0.0.0:$PORT` to view the running application. 

### Running the standlone docker container on the Pi

See `run-bash.sh`

### Run without docker on the Pi

To run the flask app without nginx and docker the following steps can be taken:

1. Make sure you have the latest build from the [Lush ScentRoom React Audio File/Colour Uploader](https://github.com/LUSHDigital/lrpi_scentroom_ui) App copied into the flaskLushProject directory.

2. Flask needs to be installed on your machine - for instructions installing flask refer [here](https://flask.palletsprojects.com/en/1.1.x/installation/#installation).

3. Once Flask is installed, you need to tell the terminal the application to work with by exporting FLASK_APP environment variable:

    $ export FLASK_APP=FlaskFileUploader.py

4. Then run flask to display the app on your localhost

    $ flask run
    
    This should then result in the flask application running locally on http://127.0.0.1:5000/


