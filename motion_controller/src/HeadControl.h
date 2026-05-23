#ifndef HEAD_CONTROL_H
#define HEAD_CONTROL_H

#include <Arduino.h>
#include <ESP32Servo.h>

/**
 * @class HeadControl
 * @brief Decoupled controller for the pan & tilt servo system of the robot's head.
 * 
 * Implements non-blocking, time-sliced angle sweeping to prevent CPU block during head movements.
 */
class HeadControl {
public:
    HeadControl(uint8_t panPin, uint8_t tiltPin);
    void begin();
    
    /**
     * @brief Periodic update function. Handles the time-sliced smooth angle interpolation.
     */
    void update();

    // --- Control Commands ---
    void setPan(int angle);
    void setTilt(int angle);
    void setTarget(int panAngle, int tiltAngle);
    void reset();

    // --- Status Queries ---
    int getPan() const { return _currentPan; }
    int getTilt() const { return _currentTilt; }
    bool isMoving() const { return (_currentPan != _targetPan) || (_currentTilt != _targetTilt); }

private:
    uint8_t _panPin;
    uint8_t _tiltPin;
    
    Servo _panServo;
    Servo _tiltServo;
    
    int _currentPan = 90;
    int _currentTilt = 92;
    int _targetPan = 90;
    int _targetTilt = 92;
    
    unsigned long _lastStepTime = 0;
};

#endif // HEAD_CONTROL_H
