# Arduino sensor web interface

## TODO list

+ Set a limit to how many points are displayed on the x-axis of each graph  
+ Save points to SQL database on server  
+ On client connect, send last 10 (?) minutes of data.  
+ Add buttons to switch graphs from realtime to historical (last hour, last day, last week, last month...)  

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

To view the webpage in your browser, open http://0.0.0.0/5000 in your web
browser.

## Usage

### Serial protocol

The protocol used for this package is a simple handshake-based json interface.
The Arduino probes for a listener by sending `0x41` bytes at regular intervals,
waiting to receive the same byte in response. Once this handshake established,
the Arduino periodically sends sensor data formatted as a line of JSON, as
follows:  
```
[{"stream":"aStreamName","value":42},{"stream":"anotherStreamName","value":420}]
```

Each line is an array of points, and each point is an object containing a stream
name and a value. Each point gets attributed a timestamp on reception by the
listener. The connection is terminated when the Arduino receives a `0x00` byte,
which makes it return to the probing state.

These bytes can be easily changed: in `listener.py` they are defined as default
values for the Listener class. You can simply create your instance with
different values:  
```python
class listener (threading.Thread):
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
```
Similarly, in the Arduino sketch these constants are defined as macros at the
top of the file:  
```c
#define HANDSHAKE_BYTE      0x41
#define REQUEST_BYTE        0x42
#define CLOSE_BYTE          0x00
```

## Authors

* Dylan Robins - https://github.com/dylan-robins

## License

This project is licensed under the GNU GPLv3 - see the [LICENSE](LICENSE) file
for details
