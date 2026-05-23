#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <Arduino.h>
#include "Config.h"
#include <ESP32Servo.h>

/**
 * @class MotorControl
 * @brief Industrial-grade DC Motor Controller for dual-channel drive systems.
 * 
 * Manages raw GPIO pin directions, PWM speed control, and smooth acceleration/deceleration
 * ramping to protect gears and batteries from high inrush currents.
 */
class MotorControl {
public:
    /**
     * @brief Constructor for the dual motor driver.
     * @param in1 Left motor forward pin
     * @param in2 Left motor backward pin
     * @param in3 Right motor forward pin
     * @param in4 Right motor backward pin
     * @param ena Left motor PWM enable pin
     * @param enb Right motor PWM enable pin
     */
    MotorControl(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4, uint8_t ena, uint8_t enb);
    
    /**
     * @brief Initializes GPIOs and PWM channels.
     */
    void begin();
    
    /**
     * @brief Periodic update function for speed ramping and low-pass filtering.
     * Should be called in the main execution loop (approx. 100Hz).
     */
    void update();

    // --- Direct Velocity Targets ---
    void setTargetSpeeds(int left, int right);
    void setSpeed(int speed);
    void stop();
    void emergencyBrake();
    void setAccelerationLimit(int limit) { _accelLimit = limit; }

    // --- High-level Directional Presets ---
    void moveForward(int correction = 0);
    void moveBackward(int correction = 0);
    void turnLeft();      
    void turnRight();     
    void turnLeftZero();  
    void turnRightZero(); 
    void turnLeftPivot();  
    void turnRightPivot(); 
    void turnLeftPivotBack();  
    void turnRightPivotBack(); 

    // --- Telemetry & Diagnostics ---
    int getSpeed() const { return _speed; }
    int getAccelerationLimit() const { return _accelLimit; }
    int getTargetLeftSpeed() const { return _targetLeft; }
    int getTargetRightSpeed() const { return _targetRight; }
    float getCurrentLeftSpeed() const { return _currentLeft; }
    float getCurrentRightSpeed() const { return _currentRight; }

private:
    // GPIO Pins
    uint8_t _in1, _in2, _in3, _in4, _ena, _enb;
    
    // Speed State Variables
    int _speed;
    int _targetLeft = 0;
    int _targetRight = 0;
    float _currentLeft = 0;
    float _currentRight = 0;
    float _filteredLeft = 0;
    float _filteredRight = 0;
    int _accelLimit;
    
    unsigned long _lastUpdateTime = 0;
    
    // PWM configuration
    const int _freq = 1000;
    const int _resolution = 8;
    const int _enaChannel = 0;
    const int _enbChannel = 1;
    
    Servo _steerServo;
    
    void applyHardwareSpeeds(int leftSpeed, int rightSpeed);
};

#endif // MOTOR_CONTROL_H
