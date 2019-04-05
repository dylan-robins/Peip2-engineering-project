#!venv/bin/activate
import serial.tools.list_ports
import logging
from sys import stderr

def find_arduino():
    logging.info("Searching for Arduinos on serial ports...")
    ports = list(serial.tools.list_ports.comports())

    if len(ports) == 0:
        logging.info("No arduinos found!")
        raise IOError
    elif len(ports) == 1:
        our_arduino = 0
    else:
        print("Multiple devices found! Which device do you want to connect to?")
        i = 0
        for p in ports:
            print("    [", i, "] ", p, sep='')
            i += 1
        while True:
            try:
                our_arduino = int(input(">>> "))
            except ValueError:
                print("Sorry, I didn't understand that.")
                continue
            else:
                if (our_arduino < 0) or (len(ports) <= our_arduino):
                    print("Sorry, that device does not exist")
                    continue
                break
    logging.info("Device found on port " + ports[our_arduino][0])
    return ports[our_arduino][0]
if __name__ == "__main__":    
    logging.basicConfig(stream=stderr, level=logging.INFO) # Our log
    my_ino = find_arduino()
    print(my_ino)