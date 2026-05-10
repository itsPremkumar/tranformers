#include "Balance.h"

Balance::Balance() : _roll(0), _pitch(0) {}

bool Balance::begin() {
    _mpu.initialize();
    return _mpu.testConnection();
}

void Balance::update() {
    _mpu.getMotion6(&_ax, &_ay, &_az, &_gx, &_gy, &_gz);
    
    _accX = _ax / 16384.0;
    _accY = _ay / 16384.0;
    _accZ = _az / 16384.0;
    
    _gyroX = _gx / 131.0;
    _gyroY = _gy / 131.0;
    _gyroZ = _gz / 131.0;
    
    _roll  = atan2(_accY, _accZ) * 180.0 / PI;
    _pitch = atan2(-_accX, sqrt(_accY * _accY + _accZ * _accZ)) * 180.0 / PI;
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
