#ifndef BALANCE_H
#define BALANCE_H

#include <Arduino.h>
#include <Wire.h>
#include <MPU6050.h>

enum FallDirection {
    NO_FALL,
    FALL_FORWARD,
    FALL_BACKWARD,
    FALL_LEFT,
    FALL_RIGHT,
    UNKNOWN_FALL
};

class Balance {
public:
    Balance();
    bool begin();
    
    void update();
    
    float getRoll() const { return _roll; }
    float getPitch() const { return _pitch; }
    float getYaw() const { return _yaw; }
    float getGyroZ() const { return _gyroZ; }
    void resetYaw() { _yaw = 0; }
    
    bool isStanding() const;
    FallDirection checkFall();

private:
    MPU6050 _mpu;
    
    int16_t _ax, _ay, _az;
    int16_t _gx, _gy, _gz;
    
    float _accX, _accY, _accZ;
    float _gyroX, _gyroY, _gyroZ;
    
    float _roll, _pitch, _yaw;
    uint32_t _lastUpdate;
    
    const float _gravity = 16384.0; 
    const float _fallThreshold = 1000.0;
};

#endif
