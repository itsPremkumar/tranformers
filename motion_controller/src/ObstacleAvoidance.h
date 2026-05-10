#ifndef OBSTACLE_AVOIDANCE_H
#define OBSTACLE_AVOIDANCE_H

#include <Arduino.h>
#include <ESP32Servo.h>

class ObstacleAvoidance {
public:
    ObstacleAvoidance(uint8_t trigPin, uint8_t echoPin, uint8_t panPin, uint8_t tiltPin);
    void begin();
    
    int getDistance();
    int readFrontDistance();
    int readGroundDistance();
    int scanLeft();
    int scanRight();
    
    void setPan(int angle) { _panServo.write(angle); }
    void setTilt(int angle) { _tiltServo.write(angle); }

private:
    uint8_t _trigPin, _echoPin;
    uint8_t _panPin, _tiltPin;
    
    Servo _panServo;
    Servo _tiltServo;
    
    const int _panCenter = 90;
    const int _panLeft = 150;
    const int _panRight = 30;
    
    const int _tiltForward = 90;
    const int _tiltDown = 125;
    
    int getDistanceOnce();
    int readAverageDistance(int samples = 3);
};

#endif
