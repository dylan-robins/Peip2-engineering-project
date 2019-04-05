// Different states the Arduino can be in
#define WAIT_FOR_CONNECTION 0
#define CONNECTION_ACTIVE 1

// Bytes the Arduino will recognise over serial connection and react to
#define HANDSHAKE_BYTE 0x41
#define CLOSE_BYTE 0x00

//PINS
#define LUX_PIN A0
#define TEMP_PIN A1
#define AIR_HUMID_PIN A2
#define LED_PIN 13 // Analog output pin that the LED is attached to
#define GND_HUMID_PIN_IN 4
// Ground humidity sensor sensor need two output pins
// (+5V flips between them to avoid soil electrolysis)
#define GND_HUMID_PIN_OUT1 6
#define GND_HUMID_PIN_OUT2 5
#define FLIPTIMER 200 // How long to wait befor flipping voltage on pins
#define WATER_PUMP 2

//ANALOG READ VALUES
int lux_val_raw = 0;
int air_temp_raw = 0;
int air_humid_raw = 0;
int ground_humid_raw = 0;
int air_humid = 0;
char gnd_humid = 0;
int air_temp = 0; // value output to the PWM (analog out)
int inByte; // buffer for reading bytes over serial
int currentState = WAIT_FOR_CONNECTION; // default state

//Watering timers
unsigned long previousWatering = millis()-1000*60*10+10000; // last watering 10 mins ago minus 10 sec
const long wateringDelay = 5*60000; // 5 min
bool wateringStatus=0;

// Gathers values on analog pins and transmitting the collected
// data over serial.
void readDataAndSend() {
  // Take mesurments
  lux_val_raw = analogRead(LUX_PIN);
  air_temp_raw = analogRead(TEMP_PIN);
  air_humid_raw = analogRead(AIR_HUMID_PIN);
  ground_humid_raw  = read_ground_sensor();

  // mapping values to standard units
  air_temp = map(air_temp_raw, 0, 1023, -20, 80);
  air_humid = map_air_humidity(air_humid_raw, air_temp);
  gnd_humid = map_gnd_humidity(ground_humid_raw);

  Serial.print("[");

  Serial.print("{\"stream\":\"Luminosite ambiante\", \"value\":");
  Serial.print(lux_val_raw, DEC);
  Serial.print(", \"scale\":[0,100]},");

  Serial.print("{\"stream\":\"Temperature ambiante\", \"value\":");
  Serial.print(air_temp, DEC);
  Serial.print(", \"scale\":[-20,80]},");

  Serial.print("{\"stream\":\"Humidite ambiante\", \"value\":");
  Serial.print(air_humid, DEC);
  Serial.print(", \"scale\":[0,100]},");

  Serial.print("{\"stream\":\"Humidite du sol\", \"value\":");
  Serial.print(gnd_humid, DEC);
  Serial.print(", \"scale\":[0,4]}");

  
  Serial.print("]\n"); 
}

void considerWater() {
  unsigned long timeSinceWatering = millis() - previousWatering;
  if (timeSinceWatering > wateringDelay && !wateringStatus && true) { // true have to be replaces by the dryness of water
    wateringStatus = true;
    digitalWrite(WATER_PUMP, HIGH);
    previousWatering = millis();
  }
  else if (wateringStatus && timeSinceWatering > 1*1000) {
    wateringStatus = false;
    digitalWrite(WATER_PUMP, LOW);
  }
  
}

float map_air_humidity(int humidity, int air_temp) {
  float r_cap = ((float)humidity * 5 / 1023) * 1200000 / (5 - ((float)humidity * 5 / 1023));
  float res;
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

char map_gnd_humidity(int ground_humid_raw) {
  if (ground_humid_raw >= 50 && ground_humid_raw < 175) {
    // Sec
    return 0;
  } else if (ground_humid_raw >= 175 && ground_humid_raw < 250) {
    // Moyen
    return 1;
  } else if (ground_humid_raw >= 250 && ground_humid_raw < 260) {
    // Humide
    return 2;  
  }
  return -1; // Y'a un souci quelquepart
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
  return WAIT_FOR_CONNECTION;
}

int read_ground_sensor() {
  // Take 1st reading
  setSensorPolarity(true);
  delay(FLIPTIMER);
  float val1 = analogRead(GND_HUMID_PIN_IN);
  delay(FLIPTIMER);
  
  // Take 2nd reading
  setSensorPolarity(false);
  delay(FLIPTIMER);
  float val2 = 1023 - analogRead(GND_HUMID_PIN_IN);
  return (int) (val1 + val2) / 2;
}

void setSensorPolarity(boolean flip){
  if(flip){
    digitalWrite(GND_HUMID_PIN_OUT1, HIGH);
    digitalWrite(GND_HUMID_PIN_OUT2, LOW);
  }else{
    digitalWrite(GND_HUMID_PIN_OUT1, LOW);
    digitalWrite(GND_HUMID_PIN_OUT2, HIGH);
  }
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
      considerWater();
      break;
  }
  // Force an interval between loops. We don't need mesurements every ms...
  delay(1000);

}
