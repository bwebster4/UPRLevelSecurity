#include <Servo.h>

Servo wheels;
double maxSpeedOffset = 45;
double maxWheelOffset = 85;


void setup() {
  wheels.attach(9);
  Serial.begin(9600);
}

/* Convert degree value to radians */
double degToRad(double degrees){
  return (degrees * 71) / 4068;
}

/* Convert radian value to degrees */
double radToDeg(double radians){
  return (radians * 4068) / 71;
}

/*
Check KEYBOARD value of incoming byte, convert to command for servo
*/
void raspiToServo(int cmd){
  if(cmd == '1'){
    Serial.write("Straight");
    wheels.write(90);
  }
  else if(cmd == '2'){
   Serial.write("Left");
   wheels.write(135);
  }
  else if(cmd == '3'){
   Serial.write("Right"); 
   wheels.write(45);
  }
  else if(cmd == '4'){
    Serial.write("Back");
    wheels.write(90);  
  }
  
  
}
//HEY JUAN LOOK IT'S THE FUCKING MAIN LOOP BITCH 


void loop() {
  int incomingByte;
  if(Serial.available() > 0) {
    // read the incoming byte:
    incomingByte = Serial.read();
    raspiToServo(incomingByte);
    // echo
    Serial.write(incomingByte); 
    Serial.write('\n');
  }
}
/*
for (int i =0; i < 360; i++){
    double rad = degToRad(i);
    double speedOffset = sin(rad) * maxSpeedOffset;
    double wheelOffset = sin(rad) * maxWheelOffset;
    wheels.write(90 + wheelOffset);
    delay(50);
  }
  */
