#include "ObstacleAvoidance.h"

ObstacleAvoidance::ObstacleAvoidance(uint8_t trigPin, uint8_t echoPin, uint8_t panPin, uint8_t tiltPin) {
    _trigPin = trigPin;
    _echoPin = echoPin;
    _panPin = panPin;
    _tiltPin = tiltPin;
}

void ObstacleAvoidance::begin() {
    pinMode(_trigPin, OUTPUT);
    pinMode(_echoPin, INPUT);
    
    _panServo.setPeriodHertz(50);
    _tiltServo.setPeriodHertz(50);
    
    _panServo.attach(_panPin, 500, 2400);
    _tiltServo.attach(_tiltPin, 500, 2400);
    
    _panServo.write(_panCenter);
    _tiltServo.write(_tiltForward);
}

int ObstacleAvoidance::getDistanceOnce() {
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);
    
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trigPin, LOW);
    
    unsigned long duration = pulseIn(_echoPin, HIGH, 30000); // 30ms timeout
    
    if (duration == 0) return 200; // no echo
    
    int distance = (int)(duration * 0.0343 / 2.0);
    if (distance <= 0) distance = 200;
    return distance;
}

int ObstacleAvoidance::readAverageDistance(int samples) {
    long sum = 0;
    int validCount = 0;
    
    for (int i = 0; i < samples; i++) {
        int d = getDistanceOnce();
        sum += d;
        validCount++;
        delay(40);
    }
    
    if (validCount == 0) return 200;
    return sum / validCount;
}

int ObstacleAvoidance::readFrontDistance() {
    _panServo.write(_panCenter);
    _tiltServo.write(_tiltForward);
    delay(250);
    return readAverageDistance();
}

int ObstacleAvoidance::readGroundDistance() {
    _panServo.write(_panCenter);
    _tiltServo.write(_tiltDown);
    delay(300);
    return readAverageDistance();
}

int ObstacleAvoidance::scanLeft() {
    _panServo.write(_panLeft);
    _tiltServo.write(_tiltForward);
    delay(350);
    int d = readAverageDistance();
    _panServo.write(_panCenter);
    delay(150);
    return d;
}

int ObstacleAvoidance::scanRight() {
    _panServo.write(_panRight);
    _tiltServo.write(_tiltForward);
    delay(350);
    int d = readAverageDistance();
    _panServo.write(_panCenter);
    delay(150);
    return d;
}
