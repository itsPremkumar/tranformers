#include "MotorControl.h"

MotorControl::MotorControl(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4, uint8_t ena, uint8_t enb) {
    _in1 = in1;
    _in2 = in2;
    _in3 = in3;
    _in4 = in4;
    _ena = ena;
    _enb = enb;
    _speed = 180;
}

void MotorControl::begin() {
    pinMode(_in1, OUTPUT);
    pinMode(_in2, OUTPUT);
    pinMode(_in3, OUTPUT);
    pinMode(_in4, OUTPUT);
    
    ledcSetup(_enaChannel, _freq, _resolution);
    ledcSetup(_enbChannel, _freq, _resolution);
    
    ledcAttachPin(_ena, _enaChannel);
    ledcAttachPin(_enb, _enbChannel);
    
    stop();
}

void MotorControl::setSpeed(int speed) {
    _speed = constrain(speed, 0, 255);
}

void MotorControl::applySpeed() {
    if (_speed == 0) {
        stop();
        return;
    }
    ledcWrite(_enaChannel, _speed);
    ledcWrite(_enbChannel, _speed);
}

void MotorControl::stop() {
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, LOW);
    digitalWrite(_in3, LOW);
    digitalWrite(_in4, LOW);
    
    ledcWrite(_enaChannel, 0);
    ledcWrite(_enbChannel, 0);
}

void MotorControl::moveForward(int correction) {
    digitalWrite(_in1, HIGH);
    digitalWrite(_in2, LOW);
    digitalWrite(_in3, HIGH);
    digitalWrite(_in4, LOW);
    
    int speedA = constrain(_speed - correction, 0, 255);
    int speedB = constrain(_speed + correction, 0, 255);
    ledcWrite(_enaChannel, speedA);
    ledcWrite(_enbChannel, speedB);
}

void MotorControl::moveBackward(int correction) {
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, HIGH);
    digitalWrite(_in3, LOW);
    digitalWrite(_in4, HIGH);
    
    int speedA = constrain(_speed - correction, 0, 255);
    int speedB = constrain(_speed + correction, 0, 255);
    ledcWrite(_enaChannel, speedA);
    ledcWrite(_enbChannel, speedB);
}

void MotorControl::turnRight() {
    turnRightZero();
}

void MotorControl::turnLeft() {
    turnLeftZero();
}

void MotorControl::turnRightZero() {
    // Left Forward, Right Backward
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, HIGH);
    digitalWrite(_in3, HIGH);
    digitalWrite(_in4, LOW);
    applySpeed();
}

void MotorControl::turnLeftZero() {
    // Left Backward, Right Forward
    digitalWrite(_in1, HIGH);
    digitalWrite(_in2, LOW);
    digitalWrite(_in3, LOW);
    digitalWrite(_in4, HIGH);
    applySpeed();
}

void MotorControl::turnRightPivot() {
    // Left Forward, Right Stopped
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, LOW);
    digitalWrite(_in3, HIGH);
    digitalWrite(_in4, LOW);
    applySpeed();
}

void MotorControl::turnLeftPivot() {
    // Left Stopped, Right Forward
    digitalWrite(_in1, HIGH);
    digitalWrite(_in2, LOW);
    digitalWrite(_in3, LOW);
    digitalWrite(_in4, LOW);
    applySpeed();
}

void MotorControl::turnRightPivotBack() {
    // Left Backward, Right Stopped
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, LOW);
    digitalWrite(_in3, LOW);
    digitalWrite(_in4, HIGH);
    applySpeed();
}

void MotorControl::turnLeftPivotBack() {
    // Left Stopped, Right Backward
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, HIGH);
    digitalWrite(_in3, LOW);
    digitalWrite(_in4, LOW);
    applySpeed();
}

void MotorControl::applySmoothSpeeds(int left, int right) {
    // Left Motor Direction
    if (left >= 0) {
        digitalWrite(_in1, HIGH);
        digitalWrite(_in2, LOW);
    } else {
        digitalWrite(_in1, LOW);
        digitalWrite(_in2, HIGH);
    }
    
    // Right Motor Direction
    if (right >= 0) {
        digitalWrite(_in3, HIGH);
        digitalWrite(_in4, LOW);
    } else {
        digitalWrite(_in3, LOW);
        digitalWrite(_in4, HIGH);
    }
    
    ledcWrite(_enaChannel, constrain(abs(left), 0, 255));
    ledcWrite(_enbChannel, constrain(abs(right), 0, 255));
}
