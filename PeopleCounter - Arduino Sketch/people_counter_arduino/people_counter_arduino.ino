//LED PINS
int detLed = 3;  //detection LED (high when person walks past)
int greenLed = 4;  //entry LED (high when entry is allowed)
int redLed = 5;  //stop LED (high when entry is not allowed)
int yellowLed = 6;  //error LED (high when there is an error)

//ULTRASONIC SENSOR PIN
int echoPin = 12;  //INPUT - receives reply from pulse
int trigPin = 13;  //OUTPUT - sends pulse to calculate distance

int maxRange = 150; //Max range set to 150cm (width of double door)
int minRange = 0;  //Min range set to 0cm (in case person walks close to sensor)
long duration, distance;  //duration is used to calc distance in cm

bool isPerson = false;  //whether a person was detected

void setup() {
  Serial.begin(9600);

  //initialise sensors and leds on setup
  pinMode(redLed, OUTPUT);
  pinMode(greenLed, OUTPUT);
  pinMode(yellowLed, OUTPUT);
  pinMode(detLed, OUTPUT);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  digitalWrite(greenLed, HIGH);

}

void loop() {  
  //Set pulse low
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  //Send 10 microsecond pulse from US sensor
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  //receive duration in seconds from echo
  duration = pulseIn(echoPin, HIGH);

  //calculate distance in cm
  distance = duration/58.2;

  //if ping is outside our range then no person detected, otherwise person detected
  if (distance >= maxRange || distance <= minRange) {
    isPerson = false;
    digitalWrite(detLed, LOW);
  } else {
    isPerson = true;
    digitalWrite(detLed, HIGH);
    Serial.println(distance);
  }

  //wait until next pulse sent
  delay(50);

  //check if RPi has sent a command
  if (Serial.available() > 0) { 
      
    //Check if edge device has sent a code
    int inputVal = Serial.read();
    
    if (inputVal == 'C') {               //RPi command to confirm that person was detected
      Serial.println(isPerson);
    }
    if (inputVal == 'G') {               //RPi command to turn green led on
      digitalWrite(greenLed, HIGH);
      digitalWrite(redLed, LOW);
      digitalWrite(yellowLed, LOW);
    } else if (inputVal == 'S') {       //RPi command to turn red on
      digitalWrite(greenLed, LOW);
      digitalWrite(redLed, HIGH);
      digitalWrite(yellowLed, LOW);
    } else {                            //Error code (yellow LED)
      digitalWrite(greenLed, LOW);
      digitalWrite(redLed, LOW); 
    }
  }
}
