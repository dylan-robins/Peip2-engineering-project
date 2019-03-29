# Arduino sensor web interface

## TODO list

+ Send scales along with points

## Installing

Clone the repository to your hard disk, and then `cd` into the newly created
folder.

### The Arduino code

A sample Arduino sketch is provided (sinewave_generator.ino). It simply
generates a sine wave and outputs it over serial in the expected format for
readings. Useful for debugging only!

Download and install the official Arduino IDE here
https://www.arduino.cc/en/main/software to modify, compile and upload the code
to your Arduino board. Follow the guide
[here](https://www.arduino.cc/en/Guide/HomePage) for more details.

An Arduino running the provided sketch (or any other valid sketch that
communicates in the expected manner with the listener) is **NOT** required to test the
web interface. A dummy listener class is provided to simulate the reception of data.

### The web interface

You’ll need to generate and activate a python3 virtual environment:  
```
$ python3 -m venv ./venv
$ source venv/bin/activate
```

You’ll know that the virtual environment is active when your prompt is prefixed
by `(venv)`. To exit the virtual environment simply type  
```
(venv) $ deactivate
```

Install the required dependencies within your virtual environment:  
```
(venv) $ pip install -r requirements.txt
```

Now you can finally launch the webserver:  
```
(venv) $ ./webserver.py
```

To view the webpage in your browser, open http://0.0.0.0:5000 in your web
browser.

## Usage

### Serial protocol

The protocol used for this package is a simple handshake-based json interface.
The Arduino probes for a listener by sending `0x41` bytes at regular intervals,
waiting to receive the same byte in response. Once this handshake established,
the Arduino periodically sends sensor data formatted as a line of JSON, as
follows:  
```
[
    {"stream":"aStreamName","value":42},
    {"stream":"anotherStreamName","value":420}
]
```

Each line is an array of points, and each point is an object containing a stream
name and a value. Each point gets attributed a timestamp on reception by the
listener. The connection is terminated when the Arduino receives a `0x00` byte,
which makes it return to the probing state.

These bytes can be easily changed: in `listener.py` they are defined as default
values for the Listener class. You can simply create your instance with
different values:  
```python
class Listener(Thread):
    def __init__(
        self,
        queue,
        port,
        baudrate,
        db_name,
        handshake_byte=b"\x41",
        close_byte=b"\x00",
        interval=1, 
        realtime=False
    ):
```
Similarly, in the Arduino sketch these constants are defined as macros at the
top of the file:  
```c
#define HANDSHAKE_BYTE      0x41
#define CLOSE_BYTE          0x00
```

### Web server / client communication

The client can request intervals of data via XHR POST requests or open an event
stream with the server. In the case of an XHR, the server will respond with a
JSON array that contains all the requested points obtained from the SQLite
database. In the case of an event stream, the server sends the client JSON
arrays every time it receives a new point from the listener via the global
queue.

New points aren't always added to the queue: on creation of an event stream,
we set the listener's `realtime` property to `True`, at witch point it starts
adding new points to the queue as well as the SQLite database. This property is
set back to `False` on reception of an XHR requesting historical points.

## Authors

* Dylan Robins - https://github.com/dylan-robins
* Joris Placette - https://github.com/JorisPLA7

## License

This project is licensed under the GNU GPLv3 - see the [LICENSE](LICENSE) file
for details
