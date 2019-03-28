
#define voltageFlipPin1 6
#define voltageFlipPin2 5
#define sensorPin 4

int flipTimer = 200;

void setup(){
  Serial.begin(9600);
  pinMode(voltageFlipPin1, OUTPUT);
  pinMode(voltageFlipPin2, OUTPUT);
  pinMode(sensorPin, INPUT);
       
}


void setSensorPolarity(boolean flip){
  if(flip){
    digitalWrite(voltageFlipPin1, HIGH);
    digitalWrite(voltageFlipPin2, LOW);
  }else{
    digitalWrite(voltageFlipPin1, LOW);
    digitalWrite(voltageFlipPin2, HIGH);
  }
}


void loop(){
  
  //
  setSensorPolarity(true);
  delay(flipTimer);
  int val1 = analogRead(sensorPin);
  delay(flipTimer);  
  setSensorPolarity(false);
  delay(flipTimer);
  // invert the reading
  int val2 = 1023 - analogRead(sensorPin);
  //
  reportLevels(val1,val2);
    
}


void reportLevels(int val1,int val2){
  
  int avg = (val1 + val2) / 2;
  
  String msg = "avg: ";
  msg += avg;
  Serial.println(msg);

}
