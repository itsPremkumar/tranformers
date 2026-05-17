#include "Balance.h"

Balance::Balance() : _roll(0), _pitch(0), _yaw(0), _roughness(0), _lastUpdate(0) {
    for (int i = 0; i < WINDOW_SIZE; i++) _accHistory[i] = 0;
}

bool Balance::begin() {
    _mpu.initialize();
    _lastUpdate = millis();
    return _mpu.testConnection();
}

bool Balance::update() {
    _mpu.getMotion6(&_ax, &_ay, &_az, &_gx, &_gy, &_gz);
    
    uint32_t now = millis();
    float dt = (now - _lastUpdate) / 1000.0f;
    _lastUpdate = now;

    _accX = _ax / 16384.0;
    _accY = _ay / 16384.0;
    _accZ = _az / 16384.0;
    
    // Terrain Roughness (Variance of AccZ)
    _accHistory[_historyIdx] = _accZ;
    _historyIdx = (_historyIdx + 1) % WINDOW_SIZE;
    
    float mean = 0;
    for(int i=0; i<WINDOW_SIZE; i++) mean += _accHistory[i];
    mean /= WINDOW_SIZE;
    
    float variance = 0;
    for(int i=0; i<WINDOW_SIZE; i++) variance += pow(_accHistory[i] - mean, 2);
    _roughness = variance / WINDOW_SIZE;

    _gyroX = _gx / 131.0;
    _gyroY = _gy / 131.0;
    _gyroZ = _gz / 131.0;
    
    // Complementary Filter for Roll and Pitch
    float rollAcc = atan2(_accY, _accZ) * 180.0 / PI;
    float pitchAcc = atan2(-_accX, sqrt(_accY * _accY + _accZ * _accZ)) * 180.0 / PI;
    
    _roll = 0.98 * (_roll + _gyroX * dt) + 0.02 * rollAcc;
    _pitch = 0.98 * (_pitch + _gyroY * dt) + 0.02 * pitchAcc;
    
    // Integrate Gyro for Yaw (relative)
    if (abs(_gyroZ) > 0.5) { // Deadzone to reduce drift
        _yaw += _gyroZ * dt;
    }
    return _mpu.testConnection();
}

bool Balance::isStanding() const {
    return _az > (_gravity * 0.8);
}

FallDirection Balance::checkFall() {
    if (isStanding()) {
        return NO_FALL;
    }
    
    if (_az < _gravity * 0.8) {
        if (_ax > _fallThreshold) {
            return FALL_BACKWARD;
        } else if (_ax < -_fallThreshold) {
            return FALL_FORWARD;
        } else if (_ay > _fallThreshold) {
            return FALL_RIGHT;
        } else if (_ay < -_fallThreshold) {
            return FALL_LEFT;
        } else {
            return UNKNOWN_FALL;
        }
    }
    
    return NO_FALL;
}
