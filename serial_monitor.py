#!venv/bin/python

from serial import Serial
from time import sleep
import json
import sqlite3
from datetime import datetime

db = sqlite3.connect("tmp.sqlite3")
dbcursor = db.cursor()
dbcursor.executescript('''
    CREATE TABLE IF NOT EXISTS readings(date TIMESTAMP, sensor TEXT, value REAL);
    CREATE TABLE IF NOT EXISTS scales(sensor TEXT, min REAL, max REAL, UNIQUE(sensor));
''')

device = Serial(port="/dev/ttyACM0", baudrate=96000)

# perform handshake
raw_byte = device.read()
while raw_byte != b"\x41":
    sleep(1)
    raw_byte = device.read()
device.write(b"\x41")

try:
    while True:
        # read data if available
        if device.in_waiting:
            raw_line = device.readline()
            # Convert the line to an array
            try:
                new_points = json.loads(raw_line)
            except json.decoder.JSONDecodeError:
                print("invalid line received")
                continue
            for point in new_points:
                dbcursor.execute('''
                    INSERT INTO readings(date, sensor, value) VALUES(?,?,?)
                ''', (datetime.now().isoformat(), point["stream"], point["value"]))
                dbcursor.execute('''
                    REPLACE INTO scales(sensor, min, max) VALUES(?, ?, ?);
                ''', (point["stream"], point["scale"][0], point["scale"][1]))
                print(point)
            db.commit()
            print("___")
except:
    device.write(b"\x00")
    sleep(1)
    device.close()
    db.close()
    raise