// Different states the Arduino can be in
#define WAIT_FOR_CONNECTION 0
#define CONNECTION_ACTIVE   1

// Only useful for looping the sinewave generated in the dummy function
#define TWO_PI 6.283185307179586476925286766559

// Bytes the Arduino will recognise over serial connection and react to
#define HANDSHAKE_BYTE      0x41
#define CLOSE_BYTE          0x00

// GLOBAL VARIABLES
float i = 0;       // varible for generating the sine wave
float n = 0.1;     // increment of i per iteration of the loop()
int inByte;        // buffer for reading bytes over serial
int currentState = WAIT_FOR_CONNECTION; // default state

// DUMMY FUNCTION
// This simulates making a set of mesurements and transmitting the collected
// data over serial.
void mesure_and_send_packet_DUMMY(float i) {
    // print json formatted line to serial output
    Serial.print("[{\"stream\":\"sineWave\",\"value\":"); // point metadata
    delay(10);
    Serial.print(sin(i), DEC);                            // point value
    delay(10);
    Serial.print("}]\n");                                 // end line
}

// Transmits HANDSHAKE_BYTEs over serial, awaiting to receive one back.
// Once received, switches Arduino to CONNECTION_ACTIVE state
int probeForPeer() {
    Serial.write(HANDSHAKE_BYTE);
    delay(100);
    if ((Serial.available()) && (Serial.read() == HANDSHAKE_BYTE)) {
        Serial.flush();
        return CONNECTION_ACTIVE;
    } else {
        return WAIT_FOR_CONNECTION;
    }
}

// Determines what to do with data received over serial connection while in
// CONNECTION_ACTIVE state.
int handleByte() {
    inByte = Serial.read();
    if (inByte == CLOSE_BYTE) {
        // connection closed: empty buffer and return to wait state
        while(Serial.available()) {
            Serial.read();
        }
        Serial.flush();
        return WAIT_FOR_CONNECTION;
    }
    // option to add other commands in else statements
}

// SETUP FUNCTION
// Runs once at boot
void setup() {
    pinMode(13, OUTPUT);
    Serial.begin(9600);
}


// MAIN LOOP
// Core logic flow happens here
void loop() {
    // check for state changes
    switch (currentState) {
        case WAIT_FOR_CONNECTION:
            digitalWrite(13, LOW);
            currentState = probeForPeer();
            break;
        case CONNECTION_ACTIVE:
            digitalWrite(13, HIGH);
            if (Serial.available()) {
                currentState = handleByte();
            }
            // Dummy function that sends a sinewave over serial
            mesure_and_send_packet_DUMMY(i);
        break;
    }
    // Force an interval between loops. We don't need mesurements every ms...
    delay(1000);

    // DUMMY CODE
    // continue sweeping through the sine function we are generating
    i += n;
    if (i > TWO_PI) {
        i = 0;
    }
}
