// Different states the Arduino can be in
#define WAIT_FOR_CONNECTION 0
#define CONNECTION_ACTIVE 1

// Bytes the Arduino will recognise over serial connection and react to
#define HANDSHAKE_BYTE 0x41
#define CLOSE_BYTE 0x00

//PINS
#define LUX_PIN A0       // input: photodiode
#define TEMP_PIN A1      // input: temperature sensor
#define AIR_HUMID_PIN A2 // input: air humidity sensor
#define GND_HUMID_PIN A4 // input: ground conductivity sensor
#define LED_PIN 13       // output: Analog output pin that the LED is attached to
#define PUMP_PIN 2       // output: water pump

//ANALOG READ VALUES
int lux_val_raw = 0;
int air_temp_raw = 0;
int air_humid_raw = 0;
int ground_humid_raw = 0;
char lux_val = 0;
int air_humid = 0;
char gnd_humid = 0;
int air_temp = 0; // value output to the PWM (analog out)
int inByte; // buffer for reading bytes over serial
int currentState = WAIT_FOR_CONNECTION; // default state

// WATERING TIMERS
#define TIME_BETWEEN_SQUIRTS 60000 // 60000 ms = 1 min
#define SQUIRT_DURATION 1000           // 1000 ms = 1 sec
unsigned long previousWatering; // time when we last turned on the pump
bool wateringStatus=0; // Are we pumping water right now?


// Gathers values on analog pins and transmitting the collected
// data over serial.
void readDataAndSend() {
  // Take mesurments
  lux_val_raw = analogRead(LUX_PIN);
  air_temp_raw = analogRead(TEMP_PIN);
  air_humid_raw = analogRead(AIR_HUMID_PIN);
  ground_humid_raw  = analogRead(GND_HUMID_PIN);

  // mapping values to standard units
  lux_val = constrain(map(lux_val_raw, 0, 1023, 0, 100), 0, 100);
  air_temp = constrain(map(air_temp_raw, 0, 1023, -20, 80), -20, 80);
  air_humid = constrain(map_air_humidity(air_humid_raw, air_temp), 0, 100);
  gnd_humid = constrain(map(ground_humid_raw, 150, 800, 0, 10), 0, 10);

  // Print readings to serial output
  Serial.print(F("["));
  delay(5);

  Serial.print(F("{\"stream\":\"Luminosite ambiante\", \"value\":"));
  delay(5);
  Serial.print(lux_val, DEC);
  delay(5);
  Serial.print(F(", \"scale\":[0,100]},"));
  delay(5);

  Serial.print(F("{\"stream\":\"Temperature ambiante\", \"value\":"));
  delay(5);
  Serial.print(air_temp, DEC);
  delay(5);
  Serial.print(F(", \"scale\":[-20,80]},"));
  delay(5);

  Serial.print(F("{\"stream\":\"Humidite ambiante\", \"value\":"));
  delay(5);
  Serial.print(air_humid, DEC);
  delay(5);
  Serial.print(F(", \"scale\":[0,100]},"));
  delay(5);

  Serial.print(F("{\"stream\":\"Humidite du sol\", \"value\":"));
  delay(5);
  Serial.print(gnd_humid, DEC);
  delay(5);
  Serial.print(F(", \"scale\":[0,10]}"));
  delay(5);
  
  Serial.print(F("]\n"));
  
}

// Maps the air humidity sensor value to something usable
float map_air_humidity(int humidity, int air_temp) {
  float r_cap = ((float)humidity * 5 / 1023) * 1200000 / (5 - ((float)humidity * 5 / 1023));
  float res = 0;
  if (air_temp < 5) {
    res = 155 - 7.87 * log(r_cap);
  } else if (air_temp >= 5 && air_temp < 10) {
    res = 149 - 7.59 * log(r_cap);
  } else if (air_temp >= 10 && air_temp < 15) {
    res = 149 - 7.74 * log(r_cap);
  } else if (air_temp >= 15 && air_temp < 20) {
    res = 148 - 7.75 * log(r_cap);
  } else if (air_temp >= 20 && air_temp < 25) {
    res = 149 - 8 * log(r_cap);
  } else if (air_temp >= 25 && air_temp < 30) {
    res = 148 - 8.16 * log(r_cap);
  } else if (air_temp >= 30 && air_temp < 35) {
    res = 148 - 8.26 * log(r_cap);
  } else if (air_temp >= 35 && air_temp < 40) {
    res = 148 - 8.41 * log(r_cap);
  } else if (air_temp >= 40 && air_temp < 45) {
    res = 149 - 8.68 * log(r_cap);
  } else if (air_temp >= 45 && air_temp < 50) {
    res = 149 - 8.77 * log(r_cap);
  } else if (air_temp >= 50) {
    res = 147 - 8.79 * log(r_cap);
  }
  return res;
}


// Check if the plant needs watering, and if it does, then turn on the pump.
// If we're in the process of watering the plant and have been doing it long
// enough, then stop.
// Otherwise do nothing.
void considerWater() {
  long timeSinceWatering = millis() - previousWatering;
  // replace true by soil humidity check
  if (timeSinceWatering > TIME_BETWEEN_SQUIRTS && !wateringStatus && gnd_humid<4) {
    wateringStatus = true;
    digitalWrite(PUMP_PIN, HIGH);
    previousWatering = millis();
  }
  else if (wateringStatus && timeSinceWatering > SQUIRT_DURATION) {
    wateringStatus = false;
    digitalWrite(PUMP_PIN, LOW);
  }
  
}


// Transmits HANDSHAKE_BYTEs over serial, waiting to receive one back.
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
  return WAIT_FOR_CONNECTION;
}


// SETUP FUNCTION
// Runs once at boot
void setup() {
  // Setup pin modes
  pinMode(LUX_PIN, INPUT);
  pinMode(TEMP_PIN, INPUT);
  pinMode(AIR_HUMID_PIN, INPUT);
  pinMode(GND_HUMID_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  // Initialize serial connection
  Serial.begin(9600);

  // Assume we just watered the plant so that the arduino doesn't
  // squirt water everytime it boots up
  previousWatering = millis();
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
  considerWater();
  // Force an interval between loops. We don't need mesurements every ms...
  delay(1000);

}
