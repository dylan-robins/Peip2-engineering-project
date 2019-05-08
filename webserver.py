#!venv/bin/python
import logging
from sys import stderr, exit
from flask import Flask, render_template, url_for, copy_current_request_context, Response, request, jsonify, abort, stream_with_context
from serial import Serial
from queue import Queue
from time import time, sleep
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sqlite3
import json

# import arduino listener classes
from listener import Listener, Dummy_Listener
# import arduino finder function
from find_arduino import find_arduino

########## CONSTANTS ##########
DBNAME = "test_data.sqlite3"
###############################

# initialize loggers
logging.basicConfig(stream=stderr, level=logging.INFO) # Our log
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # Flask log

# initialize Flask
app = Flask(__name__)
app.logger.disable = True

# Create a queue for sharing data between listener and server
q = Queue()

# find arduino's port
try:
    arduino_port = find_arduino()
except IOError:
    logging.info("No Arduinos found: initialising dummy listener...")
    serial_listener = Dummy_Listener(q, db_name=DBNAME)
else:
    logging.info("Connecting to {}...".format(arduino_port))
    serial_listener = Listener(q, arduino_port, 9600, db_name=DBNAME)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream', methods=['GET', 'POST'])
def stream():
    def eventStream():
        '''
        Fetches all new points from queue and pushes them to client via an event stream
        '''
        # get access to global queue
        global q
        first_send = True
        to_send = {
            "data": [],
            "scales": []
        }
        try:
            while True:
                logging.debug("Building response...")
                # get new points
                if (first_send):
                    logging.info("EventStream opened")
                    # connect to database
                    db = sqlite3.connect(
                        'file:'+DBNAME+'?mode=ro',
                        uri=True,
                        timeout=10
                    )
                    dbcursor = db.cursor()

                    # Get last 50 points for each sensor in the db + their scales
                    # Build data structure with scales
                    to_send["scales"] = [
                        {
                            "stream": row[0],
                            "min" : row[1],
                            "max" : row[2]
                        } for row in dbcursor.execute('SELECT sensor, min, max FROM scales')
                    ]
                    # Get points from db and add them to the structure
                    for stream in to_send["scales"]:
                        to_send["data"].extend([
                            {
                                "timestamp" : point[0],
                                "stream" : point[1],
                                "value" : point[2]
                            } for point in dbcursor.execute('''
                                SELECT * FROM (
                                    SELECT date, sensor, value
                                    FROM readings
                                    WHERE sensor == ?
                                    ORDER BY date DESC LIMIT 50
                                ) ORDER BY date ASC;
                            ''', (stream["stream"],))
                    ])
                    db.close()
                    first_send = False
                    serial_listener.set_realtime(True)

                # Send points + new stuff in the queue
                while not q.empty():
                    logging.debug("Adding point to queue...")
                    point = q.get()
                    to_send["data"].append(point)
                    # build data string
                if len(to_send) > 0:
                    logging.debug(str(to_send))
                    yield 'data: {}\n\n'.format(json.dumps(to_send))
                    to_send["data"] = []
                sleep(2)
        except GeneratorExit:
            serial_listener.set_realtime(False)
            logging.info("EventStream closed.")


    if request.method == "POST":
        # connect to database
        db = sqlite3.connect(
            'file:'+DBNAME+'?mode=ro',
            uri=True
        )
        dbcursor = db.cursor()
        name = request.form["name"]
        # Calculate resquested date and averaging interval needed to get 50 points throughout the time slot
        if name == "day":
            logging.debug("Sending points from last day...")
            requested_date = datetime.now()-timedelta(days=1)
            interval=1728 # (1 day = 86400 seconds) / 50 points = 1728 seconds
        elif name == "week":
            logging.debug("Sending points from last week...")
            requested_date = datetime.now()-timedelta(days=7)
            interval=12096 # (1 week = 12096 seconds) / 50 points = 12096 seconds
        elif name == "month":
            logging.debug("Sending points from last month...")
            requested_date = datetime.now()+relativedelta(months=-1)
            interval=52560 # (1 month = 2.628e+6 seconds) / 50 points = 52560 seconds
        elif name == "year":
            logging.debug("Sending points from last year...")
            requested_date = datetime.now()+relativedelta(years=-1)
            interval=630800 # (1 year = 3.154e+7 seconds) / 50 points = 630800 seconds
        else:
            abort(400)
        # Get requested points from database and return them
        requested = {
            "data": [
                {
                    "timestamp" : point[0],
                    "stream" : point[1],
                    "value" : point[2]
                } for point in dbcursor.execute('''
                    SELECT date, sensor, avg(value)
                    FROM readings
                    WHERE date > ?
                    GROUP BY strftime("%s", date)/?, sensor;
                ''', (requested_date, interval))
            ],
            "scales": [
                {
                    "stream": row[0],
                    "min" : row[1],
                    "max" : row[2]
                } for row in dbcursor.execute('SELECT sensor, min, max FROM scales')
            ]
        }
        db.close()
        return jsonify(requested)
    else:
        return Response(eventStream(), mimetype="text/event-stream")


if __name__ == '__main__':
    serial_listener.start()

    app.run()

    logging.info("Shutting down...")
    serial_listener.stop()
