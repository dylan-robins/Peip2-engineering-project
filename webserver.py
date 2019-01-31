#!/usr/bin/env python
import logging
from sys import stderr, exit
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from serial import Serial
from queue import Queue
from threading import Thread, Event
from time import time, sleep

# import arduino listener classes
from listener import Listener, Dummy_Listener

# initialize loggers
logging.basicConfig(stream=stderr, level=logging.DEBUG) # Our log
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # Flask log
logging.getLogger('socketio').setLevel(logging.ERROR)  # socketio logs
logging.getLogger('engineio').setLevel(logging.ERROR)

# initialize Flask
app = Flask(__name__)
app.logger.disable = True
socketio = SocketIO(app)

data_transfer_thread = Thread()
# make a stucture to keep track of if there's a client connected
thread_stop_event = {"timestamp": 0, "event":Event()}

# Create a queue for sharing data between listener and server
q = Queue()

class Data_transferer(Thread):
    def __init__(self, q, namespace):
        self.delay = 1
        self.queue = q
        self.namespace = namespace
        super(Data_transferer, self).__init__()

    def main_loop(self):
        logging.info("Sending data to clients...")
        # continue sending data until stop event is set
        while not thread_stop_event["event"].isSet():
            if (time() - thread_stop_event["timestamp"]) > 30:
                # if client hasn't sent a keepalive in the last 30s, consider
                # that client is disconnected and close the thread
                thread_stop_event["event"].set()
                logging.info('Client disconnected: transfer stopped.')
            else:
                # get data from the queue and send it
                while not q.empty():
                    msg = self.queue.get()
                    socketio.emit("point", msg, broadcast=True, namespace=self.namespace)
                sleep(self.delay)

    def run(self):
        self.main_loop()


@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect', namespace='/data')
def connect():
    # get access to thread used for transferring data to client
    global data_transfer_thread
    # get access to global queue
    global q

    # reset stop event
    global thread_stop_event
    thread_stop_event["timestamp"] = time()
    thread_stop_event["event"].clear()

    logging.info('Client connected')

    #Start the data transfer thread
    if not data_transfer_thread.isAlive():
        logging.debug("Starting Thread")
        data_transfer_thread = Data_transferer(q, namespace='/data')
        data_transfer_thread.start()

@socketio.on('keepalive', namespace='/data')
def keepalive():
    thread_stop_event["timestamp"] = time()


if __name__ == '__main__':
    # initialize listener
    # serial_listener = Listener(q, "/dev/ttyACM0", 9600)
    serial_listener = Dummy_Listener(q)
    serial_listener.start()

    socketio.run(app)

    logging.info("Shutting down...")
    serial_listener.stop()
    thread_stop_event["event"].set()
