#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <Arduino.h>

class MotorControl {
public:
    MotorControl(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4, uint8_t ena, uint8_t enb);
    void begin();
    
    void setSpeed(int speed);
    void moveForward(int correction = 0);
    void moveBackward(int correction = 0);
    void turnLeft();      // Default (Zero Turn)
    void turnRight();     // Default (Zero Turn)
    void turnLeftZero();  // Both wheels opposite
    void turnRightZero(); // Both wheels opposite
    void turnLeftPivot();  // Forward Pivot
    void turnRightPivot(); // Forward Pivot
    void turnLeftPivotBack();  // Backward Pivot
    void turnRightPivotBack(); // Backward Pivot
    void stop();

private:
    uint8_t _in1, _in2, _in3, _in4, _ena, _enb;
    int _speed;
    
    // PWM configuration
    const int _freq = 1000;
    const int _resolution = 8;
    const int _enaChannel = 0;
    const int _enbChannel = 1;
    
    void applySpeed();
};

#endif
