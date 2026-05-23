#include "HeadControl.h"
#include "Config.h"

HeadControl::HeadControl(uint8_t panPin, uint8_t tiltPin) {
    _panPin = panPin;
    _tiltPin = tiltPin;
}

void HeadControl::begin() {
    _panServo.setPeriodHertz(50);
    _tiltServo.setPeriodHertz(50);
    
    _panServo.attach(_panPin, 500, 2400);
    _tiltServo.attach(_tiltPin, 500, 2400);
    
    _panServo.write(_currentPan);
    _tiltServo.write(_currentTilt);
    
    _targetPan = _currentPan;
    _targetTilt = _currentTilt;
}

void HeadControl::setPan(int angle) {
    _targetPan = constrain(angle, 0, 180);
}

void HeadControl::setTilt(int angle) {
    _targetTilt = constrain(angle, 0, 180);
}

void HeadControl::setTarget(int panAngle, int tiltAngle) {
    setPan(panAngle);
    setTilt(tiltAngle);
}

void HeadControl::reset() {
    setTarget(90, 92); // Center and normal drive tilt
}

void HeadControl::update() {
    unsigned long now = millis();
    if (now - _lastStepTime < SERVO_STEP_DELAY_MS) return;
    _lastStepTime = now;

    // Smooth non-blocking step for Pan
    if (_currentPan != _targetPan) {
        _currentPan += (_targetPan > _currentPan) ? 1 : -1;
        _panServo.write(_currentPan);
    }
    
    // Smooth non-blocking step for Tilt
    if (_currentTilt != _targetTilt) {
        _currentTilt += (_targetTilt > _currentTilt) ? 1 : -1;
        _tiltServo.write(_currentTilt);
    }
}
