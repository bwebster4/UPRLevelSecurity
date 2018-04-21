// ================================================================
// ===                  LIBRARIES                               ===
// ================================================================

#include <DynamixelSerial1.h>
#include <Servo.h>
#include "I2Cdev.h"
//#include <string.h>
#include "MPU6050_6Axis_MotionApps20.h"
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    #include "Wire.h"
#endif

// ================================================================
// ===                  GLOBAL VARIABLES                        ===
// ================================================================

//motors and wheel
Servo wheels;
Servo esc;
double maxSpeedOffset = 45; // maximum speed magnitude, in servo 'degrees'
double maxWheelOffset = 85; // maximum wheel turn magnitude, in servo 'degrees'
#define FORWARD 'w'
#define BACKWARD 's'
#define FORWARDLEFT 'a'
#define FORWARDRIGHT 'd'
#define BACKLEFT 'z'
#define BACKRIGHT 'c'
#define STOP ' '
#define KILL 'k'


//basic parameters
bool arrived = false;
float turnAngle;
String turnDir;
bool remoteControl = false;
bool killFlag = false;
//~~~
float currentAngle;
String centeredStatus = "10";
float startupAngle;

//UltraSonic sensors & smart Servo
const int trigPin = 4;
const int echoPin = 5;
int distance[13];
long duration[13];
bool empty[13];
int dis;
long dur;
int currentDis;

/*MPU SHIT*/
MPU6050 mpu;
#define OUTPUT_READABLE_EULER
#define OUTPUT_READABLE_YAWPITCHROLL

#define INTERRUPT_PIN 2  // use pin 2 on Arduino Uno & most boards
#define LED_PIN 13 // (Arduino is 13, Teensy is 11, Teensy++ is 6)
bool blinkState = false;

// MPU control/status vars
bool dmpReady = false;  // set true if DMP init was successful
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer

// orientation/motion vars
Quaternion q;           // [w, x, y, z]         quaternion container
VectorInt16 aa;         // [x, y, z]            accel sensor measurements
VectorInt16 aaReal;     // [x, y, z]            gravity-free accel sensor measurements
VectorInt16 aaWorld;    // [x, y, z]            world-frame accel sensor measurements
VectorFloat gravity;    // [x, y, z]            gravity vector
float euler[3];         // [psi, theta, phi]    Euler angle container
float ypr[3];           // [yaw, pitch, roll]   yaw/pitch/roll container and gravity vector
int count =0;

volatile bool mpuInterrupt = false;     // indicates whether MPU interrupt pin has gone high


// ================================================================
// ===                  SERVO & ULTRSONICS                      ===
// ================================================================

/* Convert degree value to radians */
double degToRad(double degrees){
  return (degrees * 71) / 4068;
}

/* Convert radian value to degrees */
double radToDeg(double radians){
  return (radians * 4068) / 71;
}

float servoScan(){
  //Serial.println("Object detected");
  int pos = 204.8;
  for(int i = 0; i < 13; i++){
    Dynamixel.move(1, pos);
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    // Sets the trigPin on HIGH state for 10 micro seconds
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    // Reads the echoPin, returns the sound wave travel time in microseconds
    duration[i] = pulseIn(echoPin, HIGH);
    // Calculating the distance 
    distance[i] = duration[i]*0.034/2;
    //Serial.print("Distance " + String(i) + ": " + String(distance[i]) + "\n");
    if(distance[i] > 150){
      empty[i] = true;
    }
    else{
      empty[i] = false;
    }
    pos += 51.2;
    delay(200);
  }

  int closestSpot = 100;
  for(int j = 0; j < 13; j++){
    if(empty[j] == true && abs(7-j) < abs(7-closestSpot)){
      closestSpot = j;
    }
  }
  
  int deltaAngle;
  if(closestSpot != 100){
    deltaAngle = (closestSpot-7)*15;
  }
  else{
    deltaAngle = 0;
  }

  if(deltaAngle < 0){
    turnDir = "l";
  }
  else{
    turnDir = "r";
  }
  
  if((currentAngle + deltaAngle) > 180 && currentAngle > 0){
    turnAngle = -360 + deltaAngle + currentAngle;
  }
  else if((currentAngle + deltaAngle) < -180 && currentAngle < 0){
    turnAngle = 360 + deltaAngle + currentAngle;
  }
  else{
    turnAngle = deltaAngle + currentAngle;
  }
  
  if(204.8+51.2*closestSpot > 512){
    pos = 512 + 3*51.2; 
  }
  else if(204.8+51.2*closestSpot < 512){
    pos = 512 - 3*51.2;
  }
  else{
    pos = 512;
  }
  
  Dynamixel.move(1,pos);
  //Serial.println("calling avoidObject now with turnAngle == " + String(turnAngle) + "Current Angle is: " + String(currentAngle));
  avoidObject(turnAngle);
  return turnAngle;
}

void avoidObject(float turnAngle){
  delay(1000);
  if(!checkAngle(turnAngle)){
    turnRobot();
  }
  esc.write(90);
  wheels.write(90);
  Dynamixel.move(1, 512);
  delay(500);
//  for(int i = 0; i < 50; i++){
//    if(Serial.available()){  
////      Serial.println("Incoming message received");
//      getParameters();
//      return;
//    }
//    if(servoRun() < 75){
//      5(90);
//      return;
//    }
//    else{
//      esc.write(70);
//      delay(40);
//    }
//  }
  esc.write(90);
  //Serial.println("object avoided");
  sendDeltaAngle();
  getParameters();
}

int servoRun(){
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    // Sets the trigPin on HIGH state for 10 micro seconds
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    // Reads the echoPin, returns the sound wave travel time in microseconds
    dur = pulseIn(echoPin, HIGH);
    // Calculating the distance 
    dis = dur*0.034/2;
//    Serial.print("Distance: " + String(dis) + "\n");
    return dis;
}



// ================================================================
// ===                     GAUGE READING                        ===
// ================================================================

void lookForGauge()
{
  centeredStatus = "10";
  float i = 204.8;
  String savedStatus;
  while((centeredStatus != "-1")&&(centeredStatus != "0")&&(centeredStatus != "1")){
    // finds gauge 
      Dynamixel.move(2, i);
//      while(!(Serial.available())){}
//      centeredStatus = Serial.parseInt();
//      Serial.println(centeredStatus);
      //Handshake
      while(!Serial.available()){};
      centeredStatus = Serial.readString();
      while(centeredStatus != "Proceed"){
        savedStatus = centeredStatus;
        //Serial.println(centeredStatus);
        //if(Serial.available()){
        centeredStatus = Serial.readString();//}
      }
      for(int i = 0; i < 10; i++ ){
        //Serial.println("Proceed");
      }
      centeredStatus = savedStatus;
      //Handshake done
      i+=51.2;
      delay(100);
      if(i >= 870){
        i = 204.8;
      }
  }
  
  
  int startPos = Dynamixel.readPosition(2);
  int j = 10; ////Turn amount
  while(centeredStatus != "0"){
    Dynamixel.move(2, startPos+j*(centeredStatus.toInt()));
//    while(!(Serial.available())){}
//    centeredStatus = Serial.parseInt();
//    Serial.println(centeredStatus);

    //Handshake
    while(!Serial.available()){};
    centeredStatus = Serial.readString();
    while(centeredStatus != "Proceed"){
      savedStatus = centeredStatus;
      //Serial.println(centeredStatus);
      //if(Serial.available()){
      centeredStatus = Serial.readString();//}
    }
    for(int i = 0; i < 10; i++ ){
      //Serial.println("Proceed");
      
    }

    
    
    centeredStatus = savedStatus;
    //Handshake done

    j += 10;
    delay(500);
  }
  
  Dynamixel.move(2, 512);

  int deltaAngle = (Dynamixel.readPosition(2)-512)/3.41;
  if(deltaAngle > 0){
    turnDir = "r";
    calculateTurnAngle(turnDir, deltaAngle);
  }
  else if(deltaAngle < 0){
    turnDir = "l";
    calculateTurnAngle(turnDir, -deltaAngle);
  }
  else{
    turnDir = "f";
    calculateTurnAngle(turnDir, 0);
  }
  
  while(!checkAngle(turnAngle)){
    if(Serial.available()){  
      getParameters();
      return;
    }
    
    
    if(servoRun() < 40){
      esc.write(90);
      wheels.write(90); //not uploaded
      while(!Serial.available()){
        //Serial.println("Detect");
        delay(200);
      }
    
        getParameters();
        return;
       }
    
    if(turnDir == "l" || turnDir ==  "L"){
      Dynamixel.move(1,358.4);
      wheels.write(135);
      esc.write(75);
      delay(200);
    }
    else if(turnDir == "r" || turnDir ==  "R"){
      Dynamixel.move(1,665.6);
      wheels.write(45);
      esc.write(75);
      delay(200);
    }
    else{
      esc.write(90);
      //Serial.println("error");
    }
  }
  
  while(servoRun() > 40){
      Dynamixel.move(1,512);
      Dynamixel.move(2,512);
      wheels.write(90);
      delay(200);
  }
  
  esc.write(90);
  while(!Serial.available()){
    //Serial.println("Detect");
    delay(200);
  }
  getParameters();
}


// ================================================================
// ===                      WHEEL/MOTORS                        ===
// ================================================================

void calibrateESC(){
    esc.write(180); // full backwards
    delay(1000);
    esc.write(0); // full forwards
    delay(1000);
    esc.write(90); // neutral
    delay(1000);
    esc.write(90); // reset the ESC to neutral (non-moving) value
    Serial.write("Calibrated \n");
}

void straightRobot(){
  
  wheels.write(90);
  Dynamixel.move(1, 512);
  Dynamixel.move(2, 512);
  while(checkAngle(turnAngle)){
    if(Serial.available()){  
//      Serial.println("Incoming message received");
      getParameters();
      return;
    }
    if(servoRun() < 75){
      esc.write(90);
      return; 
    }
    else{
      //Serial.println("Im goin straight");
      esc.write(70);
      delay(200);
    }
  }
}



void turnRobot(){
  while(!(checkAngle(turnAngle))){
    if(Serial.available()){  
//      Serial.println("Incoming message received");
      getParameters();
      return;
    }
    if(servoRun() < 75){
      esc.write(90);
      return;
    }
    if(turnDir == "l" || turnDir ==  "L"){
      Dynamixel.move(1,358.4);
      wheels.write(135);
      esc.write(70);
      delay(200);
    }
    else if(turnDir == "r" || turnDir ==  "R"){
      Dynamixel.move(1,665.6);
      wheels.write(45);
      esc.write(70);
      delay(200);
    }
    else{
      //Serial.println("In the else section");
      float delta;
      if((currentAngle - turnAngle) < -180 && turnAngle > 0){
        delta = currentAngle + 360 - turnAngle;
      }
      else if((currentAngle - turnAngle) > 180 && turnAngle < 0){
        delta = currentAngle - 360 - turnAngle;
      }
      else{
        delta = currentAngle - turnAngle;
      }
      if(delta > 0){
        turnDir = "l";
      }
      else{
        turnDir = "r";
      }
  
    }
  }
}


void calculateTurnAngle(String turnDir, float deltaAngle){
  if(turnDir == "r" || turnDir == "R"){
      if((currentAngle + deltaAngle) > 180 && currentAngle > 0){
        turnAngle = -360 + deltaAngle + currentAngle;
      }
      else{
       turnAngle = currentAngle + deltaAngle;
      }
    }
    else if(turnDir == "l" || turnDir == "L"){
      if((currentAngle - deltaAngle) < -180 && currentAngle < 0){
        turnAngle = 360 - deltaAngle + currentAngle;
      }
      else{
        turnAngle = currentAngle - deltaAngle;
      }
      
    }
    else{
       turnAngle = currentAngle;
    }
}
// ================================================================
// ===                      MPU                                 ===
// ================================================================


void dmpDataReady() {
    mpuInterrupt = true;
}


void callibrateMPU(){
  for(int i = 0; i < 8000; i++){
    if(i%1000 == 0){
      Serial.println(i);
    }
    if (!dmpReady) return;

    // wait for MPU interrupt or extra packet(s) available
    while (!mpuInterrupt && fifoCount < packetSize) {
    }

    // reset interrupt flag and get INT_STATUS byte
    mpuInterrupt = false;
    mpuIntStatus = mpu.getIntStatus();

    // get current FIFO count
    fifoCount = mpu.getFIFOCount();

    // check for overflow (this should never happen unless our code is too inefficient)
    if ((mpuIntStatus & 0x10) || fifoCount == 1024) {
        // reset so we can continue cleanly
        mpu.resetFIFO();

    // otherwise, check for DMP data ready interrupt (this should happen frequently)
    } else if (mpuIntStatus & 0x02) {
        // wait for correct available data length, should be a VERY short wait
        while (fifoCount < packetSize){ 
          fifoCount = mpu.getFIFOCount();
        }

        // read a packet from FIFO
        mpu.getFIFOBytes(fifoBuffer, packetSize);
        fifoCount -= packetSize;
        mpu.dmpGetQuaternion(&q, fifoBuffer);
        mpu.dmpGetEuler(euler, &q);
        currentAngle = euler[0] *180/M_PI;
        
    }
  }
}


bool checkAngle(float turnAngle){
//  Serial.println("checkAngle is hit");
  mpu.resetFIFO();
// if programming failed, don't try to do anything
    if (!dmpReady){ 
      Serial.println("SOMETHING'S WRONG");
      return;
    }

    // wait for MPU interrupt or extra packet(s) available
    while (!mpuInterrupt && fifoCount < packetSize) {
//        Serial.println("you're stuck");
      }

    // reset interrupt flag and get INT_STATUS byte
    mpuInterrupt = false;
    mpuIntStatus = mpu.getIntStatus();

    // get current FIFO count
    fifoCount = mpu.getFIFOCount();

    // check for overflow (this should never happen unless our code is too inefficient)
    if ((mpuIntStatus & 0x10) || fifoCount == 1024) {
        // reset so we can continue cleanly
        mpu.resetFIFO();
        Serial.println("FIFO overflow!");

    // otherwise, check for DMP data ready interrupt (this should happen frequently)
    } else if (mpuIntStatus & 0x02) {
        // wait for correct available data length, should be a VERY short wait
        count =0;
        while (fifoCount < packetSize){ 
          fifoCount = mpu.getFIFOCount();
//          Serial.println("Stuck");
          count++;
          if(count>100){
            mpu.resetFIFO();
          }
        }

        // read a packet from FIFO
        mpu.getFIFOBytes(fifoBuffer, packetSize);
        
        // track FIFO count here in case there is > 1 packet available
        // (this lets us immediately read more without waiting for an interrupt)
        fifoCount -= packetSize;

        #ifdef OUTPUT_READABLE_EULER
            
            
            // display Euler angles in degrees
            mpu.dmpGetQuaternion(&q, fifoBuffer);
            mpu.dmpGetEuler(euler, &q);
            currentAngle = euler[0] *180/M_PI;
            
            if((currentAngle > turnAngle + 5) || (currentAngle < turnAngle - 5) ){ 
              Serial.println("<TUR," + String(currentAngle,2) + "," + String(turnAngle,2)+  ">");
              //Serial.println("Current Angle : " + String(currentAngle));
              //Serial.println("Goal angle = " + String(turnAngle) + " and current angle = " + String((euler[0] * 180/M_PI))); 
            }
            else{
                //Serial.println("You're going the right direction!");
                return true;
            }
        #endif

        // blink LED to indicate activity
        blinkState = !blinkState;
        digitalWrite(LED_PIN, blinkState);
//        Serial.println("First false");
        return false;
    }
//  Serial.println("Second false");
  return false;
}

// ================================================================
// ===                      Parameters                          ===
// ================================================================
void sendDeltaAngle(){
  String receivedDelta;
  String sentDeltaAngle;
  if((currentAngle - startupAngle) < -180 && startupAngle > 0){
    sentDeltaAngle = currentAngle + 360 - startupAngle;
  }
  else if((currentAngle - startupAngle) > 180 && startupAngle < 0){
    sentDeltaAngle = currentAngle - 360 - startupAngle;
  }
  else{
    sentDeltaAngle = currentAngle - startupAngle;
  }
  String OK = " ";
  while(OK!= "<OK>"){
    String stringAngle = String(sentDeltaAngle);
    if(stringAngle.length() > 6){
      stringAngle = stringAngle.substring(0,6);
    }
    while(stringAngle.length() < 6){
      stringAngle.concat("0");
    }
    
    Serial.println("<OBJ," + stringAngle + ">");
    while(!Serial.available()){};
    OK = Serial.readString();
  }
  return;
}

void getParameters(){
  esc.write(90);
  wheels.write(90);
  Dynamixel.move(1,512);
  Dynamixel.move(2,512);
  String parameters;
  int i1,i2,i3,i4;
  while(!(Serial.available())){
    //Serial.println("Waiting for Parameters");
    delay(200);
    }
    int OK = 0;
    int bracket1;
    while(OK!=2){
      parameters = Serial.readString();
      //Serial.println(parameters);
      if(parameters.indexOf("<") > -1){
        bracket1 = parameters.indexOf("<");
        OK++;
      }
      if(parameters.lastIndexOf(">")>-1){
        OK++;
      }
      else{
        OK = 0;
      }
    }
    delay(100);
    Serial.println("<OK>");
    i1 = parameters.indexOf(',');
    i2 = parameters.indexOf(',', i1 + 1);
    i3 = parameters.indexOf(',', i2 + 1);
    i4 = parameters.indexOf(',', i3 + 1);
//  String parameters = Serial.readString();
//  while(parameters != "Proceed"){
//    i1 = parameters.indexOf(',');
//    i2 = parameters.indexOf(',', i1 + 1);
//    i3 = parameters.indexOf(',', i2 + 1);
//    i4 = parameters.indexOf(',', i3 + 1);
//    savedPar = parameters;
//    Serial.println(parameters);
////    if(Serial.available()){ parameters = Serial.readString();}//Do this if testing with just Computer
//    parameters = Serial.readString();
//    
//  }
//    
//  for(int i = 0; i < 10; i++ ){
//        Serial.println("Proceed");
//      }
      
  //parameters = savedPar;

   //set kill flag
  if((parameters.substring(i4 + 1,i4+2) == "1")){
    //Serial.println("fully dead");
    killFlag = true;
    kill();
  }
  else{
    //Serial.println("shouldn't be dead");
    killFlag = false;
  }

  //set remote control flag
  if((parameters.substring(i3 + 1, i4) == "1")){
    remoteControl = true;
    remoteControlOperation();
  }
  else{
    remoteControl = false;
  }
  
  //set arrived flag
  if((parameters.substring(bracket1+1, i1) == "1")){
      arrived = true;
      //Serial.println("At Gauge");
      Dynamixel.move(2,200);
      esc.write(90);
      lookForGauge();
  }
  else{
    arrived = false;
  }


  
  //find temp angle 
  float deltaAngle = parameters.substring(i1 + 1, i2).toFloat();

  //Serial.println(currentAngle);
  //Serial.println(deltaAngle);
  
  //find turn direction

  turnDir = parameters.substring(i2 + 1, i3);

  

  //set turn angle
 
  calculateTurnAngle(turnDir, deltaAngle);

  //Serial.println(turnAngle);



  //Serial.println(String(arrived));
  //Serial.println(deltaAngle);
  //Serial.println(turnDir);
  //Serial.println(String(remoteControl));
  //Serial.println(String(killFlag));
  return;
}

void kill(){
  //Serial.println("kill");
  esc.write(90);
  wheels.write(90);
  Dynamixel.move(1, 512);
  Dynamixel.move(2, 512);
  while(!Serial.available()){}
  getParameters();
}

void remoteControlOperation(){
  //Serial.println("RC");
  char byte = 0;
  while(byte != 'q'){
    Serial.readBytes(&byte, 1);
      int speed = esc.read();

      //Move wheels servo into forward direction ie. write(90), and determine direction of robot currently to allow for turns without coming to full stop

      if(byte == KILL){
        kill();
      }
      
      if(byte == FORWARD && esc.read() < 90){
        wheels.write(90);
        //Serial.print("Forward \n");
        byte = 0;
      }
      
      else if(byte == FORWARD && esc.read() >= 90){
        //Serial.print("Forward \n");
        while(speed > 90){
          speed -= 5;
          esc.write(speed);
          delay(250);
        }
        
        for (int i =0; i < 20; i++){
          double rad = degToRad(i);
          double speedOffset = sin(rad) * maxSpeedOffset;
          double wheelOffset = sin(rad) * maxWheelOffset;
          esc.write(90 - speedOffset);
          
          wheels.write(90);
          delay(50);
        }
        
       byte = 0;
      }

    //Move wheels servo into backward direction ie. write(90), and determine direction of robot currently to allow for turns without coming to full stop
      
    if(byte == BACKWARD && esc.read() > 90){
      wheels.write(90);
      //Serial.print("Backward \n");
      byte = 0;
    }
    
    else if(byte == BACKWARD && esc.read() <= 90){
      //Serial.print("Backward \n");
      while(speed < 90){
          speed += 5;
          esc.write(speed);
          delay(250);
        }

      for (int i =0; i < 25; i++){
        double rad = degToRad(i);
        double speedOffset = sin(rad) * maxSpeedOffset;
        double wheelOffset = sin(rad) * maxWheelOffset;
        esc.write(90 + speedOffset);
        wheels.write(90);
        
        delay(50);
      }
      byte = 0;
    }

  
      //Move wheels servo into left direction ie. write(135), and determine direction of robot currently to allow for turns without coming to full stop
      
    if(byte == FORWARDLEFT && esc.read() < 90){
      wheels.write(135);
      //Serial.print("Forward-Left \n");
      byte = 0;
    }
    
    else if(byte == FORWARDLEFT && esc.read() >= 90){
      //Serial.print("Forward-Left \n");
      while(speed > 90){
        speed -= 5;
        esc.write(speed);
        delay(250);
      }
      
      for (int i =0; i < 20; i++){
        double rad = degToRad(i);
        double speedOffset = sin(rad) * maxSpeedOffset;
        double wheelOffset = sin(rad) * maxWheelOffset;
        esc.write(90 - speedOffset);
        wheels.write(135);
        delay(50);
      }
      
     byte = 0;
      }
        
    //Move wheels servo into right direction ie. write(45), and determine direction of robot currently to allow for turns without coming to full stop
      
      if(byte == FORWARDRIGHT && esc.read() < 90){
        wheels.write(45);
        //Serial.print("Forward-Right \n");
        byte = 0;
      }
      
      else if(byte == FORWARDRIGHT && esc.read() >= 90){
        //Serial.print("Forward-Right \n");
        while(speed > 90){
          speed -= 5;
          esc.write(speed);
          delay(250);
        }
        
        for (int i =0; i < 20; i++){
          double rad = degToRad(i);
          double speedOffset = sin(rad) * maxSpeedOffset;
          double wheelOffset = sin(rad) * maxWheelOffset;
          esc.write(90 - speedOffset);
          wheels.write(45);
          delay(50);
        }
        
       byte = 0;
      }

  //Move wheels servo into left direction ie. write(135), and determine direction of robot currently to allow for turns without coming to full stop
      
      
    if(byte == BACKLEFT && esc.read() > 90){
      wheels.write(135);
      //Serial.print("Backward-Left \n");
      byte = 0;
    }
    
    else if(byte == BACKLEFT && esc.read() <= 90){
      //Serial.print("Backward-Left \n");
      while(speed < 90){
          speed += 5;
          esc.write(speed);
          delay(250);
        }

      for (int i =0; i < 25; i++){
        double rad = degToRad(i);
        double speedOffset = sin(rad) * maxSpeedOffset;
        double wheelOffset = sin(rad) * maxWheelOffset;
        esc.write(90 + speedOffset);
        wheels.write(135);
        delay(50);
      }
      byte = 0;
    }
  
    //Move wheels servo into right direction ie. write(135), and determine direction of robot currently to allow for turns without coming to full stop
      
      
    if(byte == BACKRIGHT && esc.read() > 90){
      wheels.write(45);
      //Serial.print("Backward-Right \n");
      byte = 0;
    }
    
    else if(byte == BACKRIGHT && esc.read() <= 90){
      //Serial.print("Backward-Right \n");
      while(speed < 90){
          speed += 5;
          esc.write(speed);
          delay(250);
        }

      for (int i =0; i < 25; i++){
        double rad = degToRad(i);
        double speedOffset = sin(rad) * maxSpeedOffset;
        double wheelOffset = sin(rad) * maxWheelOffset;
        esc.write(90 + speedOffset);
        wheels.write(45);
        delay(50);
      }
      byte = 0;
    }    

      if(byte == STOP){        
        //Serial.print("Stop \n");
        if(speed < 90){
        while(speed < 90){
          speed += 5;
          esc.write(speed);
          delay(250);
        }
      }
      
      else if(speed > 90){
         while(speed > 90){
          speed -= 5;
          esc.write(speed);
          delay(250);
        }
      }
        esc.write(90);
        byte = 0;
      }
    }
    getParameters();
}


// ================================================================
// ===                      INITIAL SETUP                       ===
// ================================================================

void setup() {

  /*~~~~~~~~~~~~~`MPU SETUP~~~~~~~~~~~~~~~~~~~~~~~~~*/
    // join I2C bus (I2Cdev library doesn't do this automatically)
    #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
        Wire.begin();
        Wire.setClock(400000); // 400kHz I2C clock. Comment this line if having compilation difficulties
    #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
        Fastwire::setup(400, true);
    #endif

    // initialize serial communication
    // (115200 chosen because it is required for Teapot Demo output, but it's
    // really up to you depending on your project)
    Serial.begin(115200);
    while (!Serial); // wait for Leonardo enumeration, others continue immediately


    /*~~~~~~~~~~~Tell raspi that arduino is connected~~~~~~~~*/
    Serial.println("ARDUINO");

    
    // initialize device
    Serial.println(F("Initializing I2C devices..."));
    mpu.initialize();
    pinMode(INTERRUPT_PIN, INPUT);

    // verify connection
    Serial.println(F("Testing device connections..."));
    Serial.println(mpu.testConnection() ? F("MPU6050 connection successful") : F("MPU6050 connection failed"));

    // wait for ready
    Serial.println(F("\nSend any character to begin DMP programming and demo: "));
//    while (Serial.available() && Serial.read()); // empty buffer
//    while (!Serial.available());                 // wait for data
//    while (Serial.available() && Serial.read()); // empty buffer again

    // load and configure the DMP
    Serial.println(F("Initializing DMP..."));
    devStatus = mpu.dmpInitialize();

    // supply your own gyro offsets here, scaled for min sensitivity
    mpu.setXGyroOffset(220);
    mpu.setYGyroOffset(76);
    mpu.setZGyroOffset(-85);
    mpu.setZAccelOffset(1788); // 1688 factory default for my test chip

    // make sure it worked (returns 0 if so)
    if (devStatus == 0) {
        // turn on the DMP, now that it's ready
        Serial.println(F("Enabling DMP..."));
        mpu.setDMPEnabled(true);

        // enable Arduino interrupt detection
        Serial.println(F("Enabling interrupt detection (Arduino external interrupt 0)..."));
        attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), dmpDataReady, RISING);
        mpuIntStatus = mpu.getIntStatus();

        // set our DMP Ready flag so the main loop() function knows it's okay to use it
        Serial.println(F("DMP ready! Waiting for first interrupt..."));
        dmpReady = true;

        // get expected DMP packet size for later comparison
        packetSize = mpu.dmpGetFIFOPacketSize();
    } else {
        // ERROR!
        // 1 = initial memory load failed
        // 2 = DMP configuration updates failed
        // (if it's going to break, usually the code will be 1)
        Serial.print(F("DMP Initialization failed (code "));
        Serial.print(devStatus);
        Serial.println(F(")"));
    }

    // configure LED for output
    pinMode(LED_PIN, OUTPUT);

    Serial.println("Calibrating the MPU6050, please wait a minute...");
    callibrateMPU();

    
    /*~~~~~~~~~~~~~~~~~~Wheel and Motors setup~~~~~~~~~~~~~~~~*/

    wheels.attach(8);
    esc.attach(9);
    Serial.println("Calibrating Robot");
    calibrateESC();

    
    /*~~~~~~~~~~~~~~~~~Servo and UltraSonic Setup~~~~~~~~~~~~~~~~~*/

    pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
    pinMode(echoPin, INPUT); // Sets the echoPin as an Input
    Dynamixel.begin(1000000, 3); //3=data control
    Dynamixel.move(1,512);            
    Dynamixel.move(2,512);

    /*~~~~~~~~~~~~~~~~~Setup Global Initial Angle~~~~~~~~~~~~~~~~~*/
    
    startupAngle = currentAngle;
    
    /*~~~~~~~~~~~~~~~~~Parameters~~~~~~~~~~~~~~~~~*/

    getParameters();
}

// ================================================================
// ===                    MAIN PROGRAM LOOP                     ===
// ================================================================

void loop() {
  if(Serial.available()){  
    getParameters();
  }
  if(servoRun() < 50){
    esc.write(90);
    turnAngle = servoScan();
    delay(3000);
  }
  if(!(checkAngle(turnAngle))){
    turnRobot();
  }
  else{
    straightRobot();
  }
}
