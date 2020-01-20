FROM lushdigital/lushroom-base:latest

RUN [ "cross-build-start" ]

RUN mkdir /opt/code
RUN mkdir -p /media/usb
RUN sudo apt-get update
RUN sudo apt-get install ffmpeg

COPY flask /opt/code/flask
COPY requirements.txt /opt/code/requirements.txt
RUN pip3 install -r /opt/code/requirements.txt
WORKDIR /opt/code/flask

RUN [ "cross-build-end" ]
