#ifndef BALANCE_H
#define BALANCE_H

#include <Arduino.h>
#include <Wire.h>
#include <MPU6050.h>

/**
 * @enum FallDirection
 * @brief Represents the direction of a fall detected by the IMU.
 */
enum FallDirection {
    NO_FALL,
    FALL_FORWARD,
    FALL_BACKWARD,
    FALL_LEFT,
    FALL_RIGHT,
    UNKNOWN_FALL
};

/**
 * @class Balance
 * @brief Interfaces with the MPU6050 6-axis IMU to calculate orientation, detect falls, and assess terrain.
 * 
 * Uses a complementary filter for noise-resilient Roll and Pitch estimation, and integrates z-axis gyro
 * velocities to calculate Yaw. Also computes a Z-acceleration variance as a metric for terrain roughness.
 */
class Balance {
public:
    Balance();
    
    /**
     * @brief Establishes communication with the MPU6050 and runs self-test.
     * @return True if connected successfully, false otherwise.
     */
    bool begin();
    
    /**
     * @brief Periodic update function. Reads raw sensors and updates orientation estimates.
     * @return True if IMU remains connected, false if communication failed.
     */
    bool update();
    
    // --- Orientation Accessors ---
    float getRoll() const { return _roll; }
    float getPitch() const { return _pitch; }
    float getYaw() const { return _yaw; }
    float getGyroZ() const { return _gyroZ; }
    float getAccelX() const { return _accX; }
    
    /**
     * @brief Returns the statistical variance of the Z acceleration.
     * Higher values indicate a rougher surface (terrain).
     */
    float getTerrainRoughness() const { return _roughness; }
    
    void resetYaw() { _yaw = 0; }
    bool isOnline() const { return _online; }
    
    // --- Safety and Health checks ---
    bool isStanding() const;
    FallDirection checkFall();

private:
    MPU6050 _mpu;
    bool _online = false;
    
    // Raw raw readings
    int16_t _ax, _ay, _az;
    int16_t _gx, _gy, _gz;
    
    // Converted physical values (G's and degrees/sec)
    float _accX, _accY, _accZ;
    float _gyroX, _gyroY, _gyroZ;
    
    // Filtered orientations
    float _roll, _pitch, _yaw;
    float _roughness;
    uint32_t _lastUpdate;
    
    // Moving variance window for terrain roughness
    static const int WINDOW_SIZE = 10;
    float _accHistory[WINDOW_SIZE];
    int _historyIdx = 0;
    
    const float _gravity = 16384.0; 
    const float _fallThreshold = 1000.0;
};

#endif // BALANCE_H
