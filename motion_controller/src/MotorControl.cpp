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
    _accelLimit = ACCEL_LIMIT;
    _speedScale = 1.0f;
}

void MotorControl::begin() {
    #if USE_ACKERMANN_STEERING
    pinMode(_in1, OUTPUT);
    pinMode(_in2, OUTPUT);
    
    ledcSetup(_enaChannel, _freq, _resolution);
    ledcAttachPin(_ena, _enaChannel);
    
    _steerServo.attach(STEER_SERVO_PIN);
    _steerServo.write(STEER_ANGLE_CENTER);
    #else
    pinMode(_in1, OUTPUT);
    pinMode(_in2, OUTPUT);
    pinMode(_in3, OUTPUT);
    pinMode(_in4, OUTPUT);
    
    ledcSetup(_enaChannel, _freq, _resolution);
    ledcSetup(_enbChannel, _freq, _resolution);
    
    ledcAttachPin(_ena, _enaChannel);
    ledcAttachPin(_enb, _enbChannel);
    #endif
    
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
    _speedScale = 1.0f;
    
    #if USE_ACKERMANN_STEERING
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, LOW);
    ledcWrite(_enaChannel, 0);
    _steerServo.write(STEER_ANGLE_CENTER);
    #else
    digitalWrite(_in1, LOW);
    digitalWrite(_in2, LOW);
    digitalWrite(_in3, LOW);
    digitalWrite(_in4, LOW);
    
    ledcWrite(_enaChannel, 0);
    ledcWrite(_enbChannel, 0);
    #endif
}

void MotorControl::emergencyBrake() {
    _targetLeft = 0;
    _targetRight = 0;
    _currentLeft = 0;
    _currentRight = 0;
    _filteredLeft = 0;
    _filteredRight = 0;
    _speedScale = 1.0f;
    
    #if USE_ACKERMANN_STEERING
    digitalWrite(_in1, HIGH);
    digitalWrite(_in2, HIGH);
    ledcWrite(_enaChannel, 255);
    _steerServo.write(STEER_ANGLE_CENTER);
    #else
    digitalWrite(_in1, HIGH);
    digitalWrite(_in2, HIGH);
    digitalWrite(_in3, HIGH);
    digitalWrite(_in4, HIGH);
    
    ledcWrite(_enaChannel, 255);
    ledcWrite(_enbChannel, 255);
    #endif
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
    #if USE_ACKERMANN_STEERING
    // 1. Calculate Throttle (Average of left and right speed targets)
    int throttle = (leftSpeed + rightSpeed) / 2;
    int diff = rightSpeed - leftSpeed;

    // Apply proportional speed scaling
    throttle = (int)(throttle * _speedScale);

    // 2. Calculate Steering Angle
    int steerAngle = STEER_ANGLE_CENTER;
    if (diff != 0) {
        // Map differential speed difference to steering servo range.
        // Max differential difference is [-510, 510].
        // If diff > 0 (left speed < right speed), turn left (STEER_ANGLE_MAX_LEFT).
        // If diff < 0 (left speed > right speed), turn right (STEER_ANGLE_MAX_RIGHT).
        steerAngle = map(diff, -510, 510, STEER_ANGLE_MAX_RIGHT, STEER_ANGLE_MAX_LEFT);
    }
    
    // Constrain steering angle to the physical bounds defined in Config.h
    int minAngle = min(STEER_ANGLE_MAX_LEFT, STEER_ANGLE_MAX_RIGHT);
    int maxAngle = max(STEER_ANGLE_MAX_LEFT, STEER_ANGLE_MAX_RIGHT);
    steerAngle = constrain(steerAngle, minAngle, maxAngle);
    
    // Safety fallback: if throttle is zero but a turn is requested,
    // apply a small forward throttle so the vehicle can turn dynamically.
    if (throttle == 0 && diff != 0) {
        throttle = abs(diff) / 2;
        // Make sure safety scale is still applied to fallback throttle
        throttle = (int)(throttle * _speedScale);
    }

    // 3. Write target angle to steering servo
    _steerServo.write(steerAngle);

    // 4. Drive Throttle Motor (using Motor A pins IN1/IN2)
    if (throttle >= 0) {
        digitalWrite(_in1, HIGH);
        digitalWrite(_in2, LOW);
    } else {
        digitalWrite(_in1, LOW);
        digitalWrite(_in2, HIGH);
    }
    ledcWrite(_enaChannel, constrain(abs(throttle), 0, 255));
    
    #else
    // Apply proportional speed scaling to differential drive
    int scaledLeft = (int)(leftSpeed * _speedScale);
    int scaledRight = (int)(rightSpeed * _speedScale);

    // Left Motor Direction
    if (scaledLeft >= 0) {
        digitalWrite(_in1, HIGH);
        digitalWrite(_in2, LOW);
    } else {
        digitalWrite(_in1, LOW);
        digitalWrite(_in2, HIGH);
    }
    
    // Right Motor Direction
    if (scaledRight >= 0) {
        digitalWrite(_in3, HIGH);
        digitalWrite(_in4, LOW);
    } else {
        digitalWrite(_in3, LOW);
        digitalWrite(_in4, HIGH);
    }
    
    ledcWrite(_enaChannel, constrain(abs(scaledLeft), 0, 255));
    ledcWrite(_enbChannel, constrain(abs(scaledRight), 0, 255));
    #endif
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
