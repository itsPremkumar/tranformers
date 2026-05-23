#include "MotorControl.h"
#include "Config.h"

MotorControl::MotorControl(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4, uint8_t ena, uint8_t enb) {
    _in1 = in1;
    _in2 = in2;
    _in3 = in3;
    _in4 = in4;
    _ena = ena;
    _enb = enb;
    _speed = SPEED_NORMAL;
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

void MotorControl::setTargetSpeeds(int left, int right) {
    _targetLeft = left;
    _targetRight = right;
}

void MotorControl::stop() {
    _targetLeft = 0;
    _targetRight = 0;
    _currentLeft = 0;
    _currentRight = 0;
    _filteredLeft = 0;
    _filteredRight = 0;
    
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, LOW);
    digitalWrite(_in3, LOW);
    digitalWrite(_in4, LOW);
    
    ledcWrite(_enaChannel, 0);
    ledcWrite(_enbChannel, 0);
}

void MotorControl::emergencyBrake() {
    _targetLeft = 0;
    _targetRight = 0;
    _currentLeft = 0;
    _currentRight = 0;
    _filteredLeft = 0;
    _filteredRight = 0;
    
    digitalWrite(_in1, HIGH);
    digitalWrite(_in2, HIGH);
    digitalWrite(_in3, HIGH);
    digitalWrite(_in4, HIGH);
    
    ledcWrite(_enaChannel, 255);
    ledcWrite(_enbChannel, 255);
}

void MotorControl::update() {
    unsigned long now = millis();
    if (now - _lastUpdateTime < 10) return; // Update at ~100Hz
    _lastUpdateTime = now;

    // 1. Acceleration Ramping (The "Feel")
    float leftDiff = _targetLeft - _currentLeft;
    float rightDiff = _targetRight - _currentRight;

    if (abs(leftDiff) > 1.0f) {
        _currentLeft += constrain(leftDiff, (float)-_accelLimit, (float)_accelLimit);
    } else {
        _currentLeft = _targetLeft;
    }

    if (abs(rightDiff) > 1.0f) {
        _currentRight += constrain(rightDiff, (float)-_accelLimit, (float)_accelLimit);
    } else {
        _currentRight = _targetRight;
    }

    // 2. Low-Pass Filter (The "Smoothness")
    _filteredLeft = (_filteredLeft * (1.0f - SMOOTHING_ALPHA)) + (_currentLeft * SMOOTHING_ALPHA);
    _filteredRight = (_filteredRight * (1.0f - SMOOTHING_ALPHA)) + (_currentRight * SMOOTHING_ALPHA);

    applyHardwareSpeeds((int)_filteredLeft, (int)_filteredRight);
}

void MotorControl::applyHardwareSpeeds(int leftSpeed, int rightSpeed) {
    // Left Motor Direction
    if (leftSpeed >= 0) {
        digitalWrite(_in1, HIGH);
        digitalWrite(_in2, LOW);
    } else {
        digitalWrite(_in1, LOW);
        digitalWrite(_in2, HIGH);
    }
    
    // Right Motor Direction
    if (rightSpeed >= 0) {
        digitalWrite(_in3, HIGH);
        digitalWrite(_in4, LOW);
    } else {
        digitalWrite(_in3, LOW);
        digitalWrite(_in4, HIGH);
    }
    
    ledcWrite(_enaChannel, constrain(abs(leftSpeed), 0, 255));
    ledcWrite(_enbChannel, constrain(abs(rightSpeed), 0, 255));
}

void MotorControl::moveForward(int correction) {
    int speedL = constrain(_speed - correction, 0, 255);
    int speedR = constrain(_speed + correction, 0, 255);
    setTargetSpeeds(speedL, speedR);
}

void MotorControl::moveBackward(int correction) {
    int speedL = constrain(_speed - correction, 0, 255);
    int speedR = constrain(_speed + correction, 0, 255);
    setTargetSpeeds(-speedL, -speedR);
}

void MotorControl::turnRight() {
    turnRightZero();
}

void MotorControl::turnLeft() {
    turnLeftZero();
}

void MotorControl::turnRightZero() {
    // Left Forward, Right Backward
    setTargetSpeeds(_speed, -_speed);
}

void MotorControl::turnLeftZero() {
    // Left Backward, Right Forward
    setTargetSpeeds(-_speed, _speed);
}

void MotorControl::turnRightPivot() {
    // Left Forward, Right Stopped
    setTargetSpeeds(_speed, 0);
}

void MotorControl::turnLeftPivot() {
    // Left Stopped, Right Forward
    setTargetSpeeds(0, _speed);
}

void MotorControl::turnRightPivotBack() {
    // Left Backward, Right Stopped
    setTargetSpeeds(-_speed, 0);
}

void MotorControl::turnLeftPivotBack() {
    // Left Stopped, Right Backward
    setTargetSpeeds(0, -_speed);
}
