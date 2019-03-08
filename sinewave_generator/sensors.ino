const int luxPin = A0;  
const int tempPin = A1;
const int humidAirPin = A2;
const int analogOutPin = 13; // Analog output pin that the LED is attached to

int luxValue = 0;
int tempValue = 0;
int humidAirValue = 0;
float humidAir = 0;
int temp = 0;

void setup() {
  // initialize serial communications at 9600 bps:
  Serial.begin(9600);
}

void loop() {

  // Lecture des valeurs
  luxValue = analogRead(luxPin);
  tempValue = analogRead(tempPin);
  humidAirValue = analogRead(humidAirPin);
  
  // mapping des valeurs dans leurs unités respectives.
  temp = map(tempValue, 0, 1023, -20, 80);
  humidAir = map_humidite(humidAirValue, temp);
  

  // Affichage des valeurs
  Serial.print("Lumiere ambiante = ");
  Serial.print(luxValue);
  
  Serial.print("   Température ambiante =");
  Serial.print(tempValue);
  Serial.print(" soit = ");
  Serial.print(temp);
  Serial.print(" *C");
  
  Serial.print("   Humidité air = ");
  Serial.print(humidAir);
  Serial.print("% \n");
  
  delay(500);
}

float map_humidite(int humidite, int temp) {
  float r_cap = ((float)humidite/1023*5)*56000/(5-((float)humidite/1023*5));
  float res;
  if (temp < 5) {
    res = 155-7.87*log(r_cap);
  } else if (temp >= 5 && temp < 10) {
    res = 149-7.59*log(r_cap);
  } else if (temp >= 10 && temp < 15) {
    res = 149-7.74*log(r_cap);
  } else if (temp >= 15 && temp < 20) {
    res = 148-7.75*log(r_cap);
  } else if (temp >= 20 && temp < 25) {
    res = 149-8*log(r_cap);
  } else if (temp >= 25 && temp < 30) {
    res = 148-8.16*log(r_cap);
  } else if (temp >= 30 && temp < 35) {
    res = 148-8.26*log(r_cap);
  } else if (temp >= 35 && temp < 40) {
    res = 148-8.41*log(r_cap);
  } else if (temp >= 40 && temp < 45) {
    res = 149-8.68*log(r_cap);
  } else if (temp >= 45 && temp < 50) {
    res = 149-8.77*log(r_cap);
  } else if (temp >= 50) {
    res = 147-8.79*log(r_cap);
  }
  return res;
}
