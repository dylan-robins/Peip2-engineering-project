// Different states the Arduino can be in
#define WAIT_FOR_CONNECTION 0
#define CONNECTION_ACTIVE   1

// Bytes the Arduino will recognise over serial connection and react to
#define HANDSHAKE_BYTE      0x41
#define CLOSE_BYTE          0x00

//PINS
const int luxPin = A0;
const int tempPin = A1;
const int humidAirPin = A2;
const int analogOutPin = 13; // Analog output pin that the LED is attached to

//ANALOG READED VALUES
int luxValue = 0;
int tempValue = 0;
int humidAirValue = 0;
int humidAir = 0;
int temp = 0;        // value output to the PWM (analog out)


// GLOBAL VARIABLES
float i = 0;       // varible for generating the sine wave
float n = 0.1;     // increment of i per iteration of the loop()
int inByte;        // buffer for reading bytes over serial
int currentState = WAIT_FOR_CONNECTION; // default state

// Gathering values on analog pins and transmitting the collected
// data over serial.
void readDataAndSend() {

  // values reading
  luxValue = analogRead(luxPin);
  tempValue = analogRead(tempPin);
  humidAirValue = analogRead(humidAirPin);

  // mapping values to standard units
  temp = map(tempValue, 0, 1023, -20, 80);
  humidAir = map_humidity(humidAirValue, temp);


  Serial.print("[");

  Serial.print("{\"Lumiere ambiante\":\"luxValue\",\"value\":");
  Serial.print(luxValue, DEC);
  Serial.print("}");

  Serial.print("{\"Temperature ambiante\":\"temp\",\"value\":");
  Serial.print(temp, DEC);
  //Serial.print(" *C");
  Serial.print("}");

  Serial.print("{\"Humidite de l'air\":\"humidAir\",\"value\":");
  Serial.print(humidAir, DEC);
  Serial.print("}");

  Serial.print("{\"Humidite de la terre\":\"luxValue\",\"value\": 42");
  //print humid dirt
  Serial.print("}");

  
  Serial.print("]\n");
  
}

float map_humidity(int humidity, int temp) {
  float r_cap = ((float)humidity * 5 / 1023) * 1200000 / (5 - ((float)humidity * 5 / 1023));
  float res;
  if (temp < 5) {
    res = 155 - 7.87 * log(r_cap);
  } else if (temp >= 5 && temp < 10) {
    res = 149 - 7.59 * log(r_cap);
  } else if (temp >= 10 && temp < 15) {
    res = 149 - 7.74 * log(r_cap);
  } else if (temp >= 15 && temp < 20) {
    res = 148 - 7.75 * log(r_cap);
  } else if (temp >= 20 && temp < 25) {
    res = 149 - 8 * log(r_cap);
  } else if (temp >= 25 && temp < 30) {
    res = 148 - 8.16 * log(r_cap);
  } else if (temp >= 30 && temp < 35) {
    res = 148 - 8.26 * log(r_cap);
  } else if (temp >= 35 && temp < 40) {
    res = 148 - 8.41 * log(r_cap);
  } else if (temp >= 40 && temp < 45) {
    res = 149 - 8.68 * log(r_cap);
  } else if (temp >= 45 && temp < 50) {
    res = 149 - 8.77 * log(r_cap);
  } else if (temp >= 50) {
    res = 147 - 8.79 * log(r_cap);
  }
  return res;
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
    while (Serial.available()) {
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

      // function that read on pins, map and send the data
      readDataAndSend();
      break;
  }
  // Force an interval between loops. We don't need mesurements every ms...
  delay(1000);

}
