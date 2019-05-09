#!/usr/bin/env python
import logging
from math import floor, sin, cos
from time import sleep
from datetime import datetime, timedelta
import json
from sys import argv, stderr
from threading import Thread
from queue import Queue
from serial import Serial
import sqlite3

class Listener(Thread):
    def __init__(
        self,
        queue,
        port,
        baudrate,
        db_name,
        handshake_byte=b"\x41",
        close_byte=b"\x00",
        interval=1
    ):
        Thread.__init__(self)
        self.queue = queue
        self.device = Serial(port=port, baudrate=baudrate)
        self.handshake_byte = handshake_byte
        self.close_byte = close_byte
        self.interval = interval  # seconds between mesurement
        self.stop_flag = False
        self.realtime = False
        self.db_name = db_name

    def run(self):
        logging.info("Listener started")

        # Connect to the SQLite database and initialize (if necessary) a table
        db = sqlite3.connect(self.db_name)
        dbcursor = db.cursor()
        dbcursor.executescript('''
            CREATE TABLE IF NOT EXISTS readings(date TIMESTAMP, sensor TEXT, value REAL);
            CREATE TABLE IF NOT EXISTS scales(sensor TEXT, min REAL, max REAL, UNIQUE(sensor));
        ''')

        # wait for Arduino to be ready
        raw_byte = self.device.read()
        while raw_byte != self.handshake_byte:
            sleep(1)
            raw_byte = self.device.read()
        # complete handshake
        self.device.write(self.handshake_byte)
        logging.info("Handshake completed")

        # MAIN LOOP: request points
        while not self.stop_flag:
            # Check if data is available to read
            if self.device.in_waiting:
                # read data
                raw_line = self.device.readline()
                logging.debug("Line received")

                # Convert the line to an array
                try:
                    new_points = json.loads(raw_line)
                except json.decoder.JSONDecodeError:
                    logging.warning("Invalid line received!")
                    logging.warning("<{}> is not valid.".format(raw_line))
                    continue

                # add each new point to the sql db and the queue
                for point in new_points:
                    try:
                        dbcursor.execute('''
                            INSERT INTO readings(date, sensor, value) VALUES(?,?,?)
                        ''', (datetime.now().isoformat(), point["stream"], point["value"]))
                        dbcursor.execute('''
                            REPLACE INTO scales(sensor, min, max) VALUES(?, ?, ?);
                        ''', (point["stream"], point["scale"][0], point["scale"][1]))

                        if self.realtime:
                            # add each new point to the queue
                            logging.debug("Point added to queue")
                            self.queue.put({
                                "stream": point["stream"],
                                "timestamp": datetime.now().isoformat(),
                                "value": point["value"]
                            })
                    except KeyError:
                        logging.warning("Malformed line received!")
                        logging.warning("<{}> is not valid.".format(point))
                        continue
                db.commit()
        db.close()

    def stop(self):
        logging.info("Listener stopping")
        self.stop_flag = True
        self.device.write(self.close_byte)  # Arduino will return to wait state
        sleep(1)
        self.device.close()

    def set_realtime(self, rt):
        self.realtime = rt
        logging.info("Toggling realtime to " + str(self.realtime))


class Dummy_Listener(Thread):
    def __init__(self, queue, db_name="db.sqlite3", interval=1):
        Thread.__init__(self)
        self.queue = queue
        self.db_name = db_name
        self.interval = interval  # seconds between mesurement
        self.stop_flag = False
        self.realtime = False

    def run(self):
        logging.info("Dummy listener started")

        # Connect to the SQLite database and initialize (if necessary) a table
        db = sqlite3.connect(self.db_name)
        dbcursor = db.cursor()
        dbcursor.executescript('''
            CREATE TABLE IF NOT EXISTS readings(date TIMESTAMP, sensor TEXT, value REAL);
            CREATE TABLE IF NOT EXISTS scales(sensor TEXT, min REAL, max REAL);
        ''')

        dbcursor.execute('''
            REPLACE INTO scales(sensor, min, max) VALUES(?, ?, ?);
        ''', ("sine wave", -1, 1))
        dbcursor.execute('''
            REPLACE INTO scales(sensor, min, max) VALUES(?, ?, ?);
        ''', ("cosine wave", -100, 120))


        i = 0
        # MAIN LOOP: generate dummy points
        while not self.stop_flag:
            # add each new point to the sql db and the queue
            new_points = [
                {"stream": "sine wave", "timestamp": datetime.now().isoformat(), "value": sin(i)},
                {"stream": "cosine wave", "timestamp": datetime.now().isoformat(), "value": 100*cos(i)}
            ]
            for point in new_points:
                dbcursor.execute('''
                    INSERT INTO readings(date, sensor, value) VALUES(?,?,?)
                ''', (datetime.now().isoformat(), point["stream"], point["value"]))
                db.commit()

                if self.realtime:
                    # add each new point to the queue
                    logging.debug("Point added to queue")
                    self.queue.put({
                        "stream": point["stream"],
                        "timestamp": point["timestamp"],
                        "value": point["value"]
                    })
            i += 0.6
            sleep(self.interval)
        db.close()

    def stop(self):
        logging.info("Listener stopping")
        self.stop_flag = True
    
    def set_realtime(self, rt):
        self.realtime = rt
        logging.info("Toggling realtime to " + str(self.realtime))


def test_listener(device="/dev/ttyACM0", baudrate=9600):
    # set up logger
    logging.basicConfig(stream=stderr, level=logging.INFO)

    # create a queue to get values back from listener thread
    q = Queue()

    # create and launch listener thread
    main_listener = Listener(q, device, baudrate, ":memory:")
    main_listener.start()
    try:
        # set a limit to how long we want the listener to run
        i = 0
        while i < 10:
            # read all points given my listener
            while not q.empty():
                print(q.get())
            # wait a bit
            sleep(1)
            i += 1
        # close the device and finish the process
        main_listener.stop()
    except:
        # close the device and finish the process
        main_listener.stop()
        # raise the exception
        raise


def test_dummy_listener():
    # set up logger
    logging.basicConfig(stream=stderr, level=logging.INFO)
    q = Queue()
    try:
        # create and launch listener thread
        main_listener = Dummy_Listener(q)
        main_listener.start()
        # set a limit to how long we want the listener to run
        i = 0
        while i < 10:
            # read all points given my listener
            while not q.empty():
                print(q.get())
            # wait a bit
            sleep(1)
            i += 1
        # close the device and finish the process
        main_listener.stop()
    except:
        # close the device and finish the process
        main_listener.stop()
        # raise the exception
        raise


if __name__ == "__main__":
    if len(argv) > 1 and argv[1] == "dummy":
        test_dummy_listener()
    else:
        test_listener()
