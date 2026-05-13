#ifndef SERVO_CONTROL_H
#define SERVO_CONTROL_H

#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>
#include "Balance.h"

class ServoControl {
public:
    ServoControl(uint8_t addr = 0x40);
    void begin();
    
    void moveServoSmooth(int channel, int targetAngle, int speedDelay = 10);
    void moveGroup(int channels[], int targets[], int count);
    
    void standPosition();
    void walkForward();
    void transformToCar();
    void pushMotion();
    void kickMotion();
    void recoverFromFall(FallDirection dir);

private:
    Adafruit_PWMServoDriver _pwm;
    
    static const int NUM_SERVOS = 16;
    static const int SERVOMIN = 100;
    static const int SERVOMAX = 500;
    
    int _servoPos[NUM_SERVOS];
    
    int angleToPulse(int angle);
};

#endif
