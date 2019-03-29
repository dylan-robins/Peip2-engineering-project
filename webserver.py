#!venv/bin/python
import logging
from sys import stderr, exit
from flask import Flask, render_template, url_for, copy_current_request_context, Response, request, jsonify, abort
from serial import Serial
from queue import Queue
from time import time, sleep
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import sqlite3
import json

########## CONSTANTS ##########
DBNAME = "test_data.sqlite3"
###############################

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
# serial_listener = Listener(q, "/dev/ttyACM0", 9600, db_name=DBNAME)
serial_listener = Dummy_Listener(q, db_name=DBNAME)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream', methods=['GET', 'POST'])
def stream():
    def eventStream():
        '''
        Fetches all new points from queue and pushes them to client via an event stream
        '''
        first_send = True
        while True:
            logging.debug("Building response...")
            # get new points
            to_send = []
            if (first_send):
                # connect to database
                db = sqlite3.connect(
                    'file:'+DBNAME+'?mode=ro',
                    uri=True
                )
                dbcursor = db.cursor()
                to_send = [
                    {
                        "timestamp" : point[0],
                        "stream" : point[1],
                        "value" : point[2]
                    } for point in dbcursor.execute('''
                        SELECT * FROM (
                        SELECT * FROM readings ORDER BY date DESC LIMIT 50)
                        ORDER BY date ASC;
                    ''')
                ]
                db.close()
                first_send = False

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
        # connect to database
        db = sqlite3.connect(
            'file:'+DBNAME+'?mode=ro',
            uri=True,
            detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES
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
        requested = [
            {
                "timestamp" : point[0],
                "stream" : point[1],
                "value" : point[2]
            } for point in dbcursor.execute('''
                SELECT datetime(date), sensor, value
                FROM readings
                WHERE date > datetime(?)
                GROUP BY strftime('%s', DATE(date) || ' ' || TIME(date)) / (?), sensor;
            ''', (requested_date, interval))
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
