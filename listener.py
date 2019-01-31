#!/usr/bin/env python
import logging
from math import floor, sin, cos
from time import time, sleep
from json import loads as json_loads
from sys import argv, stderr
from threading import Thread
from queue import Queue
from serial import Serial


class Listener(Thread):
    def __init__(
        self,
        queue,
        port,
        baudrate,
        handshake_byte=b"\x41",
        resquest_byte=b"\x42",
        close_byte=b"\x00",
        interval=1,
    ):
        Thread.__init__(self)
        self.queue = queue
        self.device = Serial(port=port, baudrate=baudrate)
        self.handshake_byte = handshake_byte
        self.resquest_byte = resquest_byte
        self.close_byte = close_byte
        self.interval = interval  # seconds between mesurement
        self.stop_flag = False

    def run(self):
        logging.info("Listener started")

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
                new_points = json_loads(raw_line)

                # add each new point to the queue
                for point in new_points:
                    logging.debug("Point added to queue")
                    self.queue.put({
                        "stream": point["stream"],
                        "timestamp": floor(time()),
                        "value": point["value"]
                    })

            # wait before requesting another mesurement
            sleep(self.interval)

    def stop(self):
        logging.info("Listener stopping")
        self.stop_flag = True
        self.device.write(self.close_byte)  # Arduino will return to wait state
        self.device.flush()
        self.device.close()


class Dummy_Listener(Thread):
    def __init__(self, queue, interval=1):
        Thread.__init__(self)
        self.queue = queue
        self.interval = interval  # seconds between mesurement
        self.stop_flag = False

    def run(self):
        logging.info("Dummy listener started")

        i = 0
        # MAIN LOOP: generate dummy points
        while not self.stop_flag:
            self.queue.put({"stream": "sine wave", "timestamp": floor(time()), "value": sin(i)})
            self.queue.put({"stream": "cosine wave", "timestamp": floor(time()), "value": cos(i)})
            i += 0.6
            sleep(1)

    def stop(self):
        logging.info("Listener stopping")
        self.stop_flag = True


def test_listener(device="/dev/ttyACM0", baudrate=9600):
    # set up logger
    logging.basicConfig(stream=stderr, level=logging.INFO)

    # create a queue to get values back from listener thread
    q = Queue()

    # create and launch listener thread
    main_listener = Listener(q, device, baudrate)
    main_listener.start()
    try:
        # set a limit to how long we want the listener to run
        i = 0
        while i < 10:
            # read all points given my listener
            while not q.empty():
                print(q.get())
            # wait a bit
            sleep(2)
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
            sleep(2)
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
