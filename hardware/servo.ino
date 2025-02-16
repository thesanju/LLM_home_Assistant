#include <Servo.h>

Servo myservo;
String inputString = "";
boolean stringComplete = false;

void setup() {
  Serial.begin(9600);
  myservo.attach(9);  // Servo on pin 9
  inputString.reserve(200);
  
  // Move to starting position
  myservo.write(90);
}

void loop() {
  // When a complete command is received
  if (stringComplete) {
    int angle = inputString.toInt();
    
    // Validate angle range
    if (angle >= 0 && angle <= 180) {
      myservo.write(angle);
    }
    
    // Clear the string for next command
    inputString = "";
    stringComplete = false;
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    
    // If newline, set flag
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}