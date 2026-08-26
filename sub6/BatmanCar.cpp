int temp = A3;
int templed = 4;
int tempp;
int echo = A2;
int trig = 8;
int distannce;
int g =7;
int b = 12;
int r = 2;
int buzz = 3;
int m1In3 = 5;
int m2In4 = 6;
int currentServoAngle;


unsigned long currentTime;
unsigned long ClastBuzzerToggle = 0;
unsigned long lastBuzzerToggle = 0;
//unsigned long lastLCDUpdate = 0;

//const long lcdInterval = 50;
const long buzzerInterval = 500;
const long CbuzzerInterval = 250;

bool buzzerState = false;

#include <Servo.h>
Servo myServo;
int seconds = 0;
#include <Adafruit_LiquidCrystal.h>
Adafruit_LiquidCrystal lcd(0);

void lcdNotice(int temppp,int distanncee){

    if (distanncee <80){
    if (temppp > 70) {
    digitalWrite(templed, HIGH);
    analogWrite(m1In3, 255);
    lcd.setCursor(0,1);
    lcd.print("Engine Overheat!    ");
  }else{
    digitalWrite(templed, LOW);
    analogWrite(m1In3, 0);
    lcd.setCursor(0,1);
    lcd.print("Danger! Stop!       ");}

    analogWrite(m2In4, 0);
    digitalWrite(r,HIGH);
    digitalWrite(g,LOW);
    digitalWrite(b,LOW);
    if (currentServoAngle != 90) {
    myServo.write(90);
    currentServoAngle = 90;
  }

    }
    else if (distanncee >= 80 && distanncee<= 200){
     if (temppp > 70) {
    digitalWrite(templed, HIGH);
    analogWrite(m1In3, 255);
    lcd.setCursor(0,1);
    lcd.print("Engine Overheat!    ");
  }else{
    digitalWrite(templed, LOW);
    analogWrite(m1In3, 0);
    lcd.setCursor(0,1);
    lcd.print("Caution Ahead       ");}

    analogWrite(m2In4, 150);
    digitalWrite(g,HIGH);
    digitalWrite(r,LOW);
    digitalWrite(b,LOW);
    if (currentServoAngle != 0) {
    myServo.write(0);
    currentServoAngle = 0;
  }

    } else if (distanncee> 200){
     if (temppp > 70) {
    digitalWrite(templed, HIGH);
    analogWrite(m1In3, 255);
    lcd.setCursor(0,1);
    lcd.print("Engine Overheat!    ");
  }else{
    digitalWrite(templed, LOW);
    analogWrite(m1In3, 0);
    lcd.setCursor(0,1);
    lcd.print("Clear Path           ");
}
    analogWrite(m2In4, 255);
    digitalWrite(b,HIGH);
    digitalWrite(r,LOW);
    digitalWrite(g,LOW);
    if (currentServoAngle != 0) {
    myServo.write(0);
    currentServoAngle = 0;
  }
    }

lcd.setCursor(0, 0);
    lcd.print("D: ");
    lcd.print(distanncee);
    lcd.print("cm, T:");
    lcd.print(temppp);
    lcd.print("C          ");}

int Temp(){
  int tempp = analogRead(temp);
  float voltage = tempp * (5.0 / 1023.0); 
  float temperatureC = (voltage - 0.5) * 100 ;  
  return temperatureC;
}

int dis(){
  long duration;
  int distance;
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  duration = pulseIn(echo, HIGH, 30000);
  if (duration == 0) return 400;
  distance = duration * 0.034 / 2;
  return distance;
}

void setup()
{
  pinMode(temp, INPUT);
  pinMode(templed, OUTPUT);
  pinMode(r, OUTPUT);
  pinMode(g, OUTPUT);
  pinMode(b, OUTPUT);
  pinMode(buzz, OUTPUT);
  pinMode(echo, INPUT);
  pinMode(trig, OUTPUT);
  pinMode(m1In3, OUTPUT);
  pinMode(m2In4, OUTPUT);
  myServo.attach(9); 
  lcd.begin(16, 2);
  Serial.begin(9600); 
  myServo.write(0);
}

void loop()
{
  currentTime  = millis();
  distannce = dis();
  tempp = Temp();
  //if (currentTime - lastLCDUpdate >= lcdInterval) {
    //lastLCDUpdate = currentTime;
    lcdNotice(tempp, distannce);
  //}
  
  if (distannce < 80) {
    if (currentTime - ClastBuzzerToggle >= CbuzzerInterval) {
      ClastBuzzerToggle = currentTime;
      buzzerState = !buzzerState;
      if (buzzerState) digitalWrite(buzz, HIGH);
      else {digitalWrite(buzz, LOW);
    buzzerState = false;
    }
    }
  } else if (distannce <= 200) {
    if (currentTime - lastBuzzerToggle >= buzzerInterval) {
      lastBuzzerToggle = currentTime;
      buzzerState = !buzzerState;
      if (buzzerState) digitalWrite(buzz, HIGH);
      else {digitalWrite(buzz, LOW);
    buzzerState = false;
    }
    }
  } else {
    digitalWrite(buzz, LOW);
    buzzerState = false;
  }
  Serial.println(currentTime);
}