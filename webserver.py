#!venv/bin/python
import logging
from sys import stderr, exit
from flask import Flask, render_template, url_for, copy_current_request_context, Response, request, jsonify
from serial import Serial
from queue import Queue
from time import time, sleep
from datetime import datetime, timedelta
import sqlite3
import json

# import arduino listener classes
from listener import Listener, Dummy_Listener

# initialize loggers
logging.basicConfig(stream=stderr, level=logging.INFO) # Our log
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # Flask log

    # initialize Flask
app = Flask(__name__)

app.logger.disable = True
# Create a queue for sharing data between listener and server
q = Queue()

# initialize listener
# serial_listener = Listener(q, "/dev/ttyACM0", 9600)
serial_listener = Dummy_Listener(q)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream', methods=['GET', 'POST'])
def stream():
    def eventStream():
        '''
        Fetches all new points from queue and pushes them to client via an event stream
        '''
        while True:
            logging.debug("Building response...")
            # get new points
            to_send = []
            while not q.empty():
                logging.debug("Adding point to queue...")
                point = q.get()
                to_send.append(point)
            # build data string
            if len(to_send) > 0:
                logging.debug(str(to_send))
                yield 'data: {}\n\n'.format(json.dumps(to_send))
            sleep(1)

    if request.method == "POST":
        serial_listener.set_realtime(False)
        name = request.form["name"]
        # connect to database
        db = sqlite3.connect('file:db.sqlite3?mode=ro', uri=True, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        dbcursor = db.cursor()
        if name == "day":
            logging.debug("Sending points from last day...")
            yesterday = datetime.now()-timedelta(days=1)
            requested = [
                {
                    "timestamp" : point[0],
                    "stream" : point[1],
                    "value" : point[2]
                } for point in dbcursor.execute('''SELECT datetime(date), sensor, value FROM readings WHERE date > datetime(?)''', (yesterday,))
            ]
        db.close()
        return jsonify(requested)
    else:
        # get access to global queue
        global q
        serial_listener.set_realtime(True)
        return Response(eventStream(), mimetype="text/event-stream")


if __name__ == '__main__':
    serial_listener.start()

    app.run()

    logging.info("Shutting down...")
    serial_listener.stop()
