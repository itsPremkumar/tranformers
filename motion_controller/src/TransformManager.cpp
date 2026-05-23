#include "TransformManager.h"

TransformManager::TransformManager(ServoControl& servos) : _servos(servos) {}

void TransformManager::begin() {
    stopTransition();
}

void TransformManager::transformToCar() {
    if (_currentState != TRANSITION_TO_CAR) {
        Serial.println("[TRANSFORM] Starting transformation to Car Mode...");
        _currentState = TRANSITION_TO_CAR;
        _step = 0;
        _lastStepTime = millis();
        // Start Step 0: Fold legs
        _servos.moveServoSmooth(2, 30);
        _servos.moveServoSmooth(3, 30);
    }
}

void TransformManager::transformToCrawler() {
    if (_currentState != TRANSITION_TO_CRAWLER) {
        Serial.println("[TRANSFORM] Starting transformation to Crawler Mode...");
        _currentState = TRANSITION_TO_CRAWLER;
        _step = 0;
        _lastStepTime = millis();
        // Start Step 0: Spread hips
        _servos.moveServoSmooth(0, 160);
        _servos.moveServoSmooth(1, 20);
    }
}

void TransformManager::recoverFromFall(FallDirection dir) {
    if (dir == NO_FALL) return;
    
    Serial.println("[TRANSFORM] Fall recovery transition triggered...");
    
    if (dir == FALL_FORWARD) {
        _currentState = TRANSITION_RECOVER_FORWARD;
        _step = 0;
        _lastStepTime = millis();
        _servos.moveServoSmooth(4, 160); // Right arm forward
        _servos.moveServoSmooth(5, 20);  // Left arm forward
    } else if (dir == FALL_BACKWARD) {
        _currentState = TRANSITION_RECOVER_BACKWARD;
        _step = 0;
        _lastStepTime = millis();
        _servos.moveServoSmooth(0, 150); // Hips forward
        _servos.moveServoSmooth(1, 30);
    } else {
        _currentState = TRANSITION_RECOVER_SHAKE;
        _step = 0;
        _shakeIteration = 0;
        _lastStepTime = millis();
        _servos.moveServoSmooth(4, 40);
        _servos.moveServoSmooth(5, 140);
    }
}

void TransformManager::stopTransition() {
    _currentState = TRANSITION_NONE;
    _step = 0;
    _shakeIteration = 0;
}

void TransformManager::update() {
    if (_currentState != TRANSITION_NONE) {
        processTransitionStep();
    }
}

void TransformManager::processTransitionStep() {
    unsigned long now = millis();
    
    switch (_currentState) {
        case TRANSITION_TO_CAR: {
            if (_step == 0 && now - _lastStepTime >= 300) {
                _servos.moveServoSmooth(4, 20); // Fold arms
                _servos.moveServoSmooth(5, 160);
                _step = 1;
                _lastStepTime = now;
            } else if (_step == 1 && now - _lastStepTime >= 300) {
                _servos.moveServoSmooth(6, 150); // Rotate body
                _servos.moveServoSmooth(7, 30);
                _step = 2;
                _lastStepTime = now;
            } else if (_step == 2 && now - _lastStepTime >= 300) {
                _servos.moveServoSmooth(8, 0);   // Final lock
                _servos.moveServoSmooth(9, 180);
                _currentState = TRANSITION_NONE; // Complete
                Serial.println("[TRANSFORM] Car Shape Transition Complete.");
            }
            break;
        }
        case TRANSITION_TO_CRAWLER: {
            if (_step == 0 && now - _lastStepTime >= 300) {
                _servos.moveServoSmooth(2, 160); // Bend knees to lower chassis
                _servos.moveServoSmooth(3, 20);
                _step = 1;
                _lastStepTime = now;
            } else if (_step == 1 && now - _lastStepTime >= 300) {
                _servos.moveServoSmooth(4, 150); // Spread arms for balance
                _servos.moveServoSmooth(5, 30);
                _step = 2;
                _lastStepTime = now;
            } else if (_step == 2 && now - _lastStepTime >= 200) {
                _currentState = TRANSITION_NONE; // Complete
                Serial.println("[TRANSFORM] Crawler Shape Transition Complete.");
            }
            break;
        }
        case TRANSITION_RECOVER_FORWARD: {
            if (_step == 0 && now - _lastStepTime >= 500) {
                _servos.moveServoSmooth(4, 40);  // Snap back to push
                _servos.moveServoSmooth(5, 140);
                _step = 1;
                _lastStepTime = now;
            } else if (_step == 1 && now - _lastStepTime >= 300) {
                _currentState = TRANSITION_NONE;
                _servos.standPosition();
                Serial.println("[TRANSFORM] Recovery Forward Shape Transition Complete.");
            }
            break;
        }
        case TRANSITION_RECOVER_BACKWARD: {
            if (_step == 0 && now - _lastStepTime >= 400) {
                _servos.moveServoSmooth(2, 160); // Knees snap
                _servos.moveServoSmooth(3, 20);
                _step = 1;
                _lastStepTime = now;
            } else if (_step == 1 && now - _lastStepTime >= 300) {
                _currentState = TRANSITION_NONE;
                _servos.standPosition();
                Serial.println("[TRANSFORM] Recovery Backward Shape Transition Complete.");
            }
            break;
        }
        case TRANSITION_RECOVER_SHAKE: {
            if (now - _lastStepTime < 100) return;
            _lastStepTime = now;

            if (_step == 0) {
                _servos.moveServoSmooth(4, 140);
                _servos.moveServoSmooth(5, 40);
                _step = 1;
            } else {
                _servos.moveServoSmooth(4, 40);
                _servos.moveServoSmooth(5, 140);
                _step = 0;
                _shakeIteration++;
                
                if (_shakeIteration >= 3) {
                    _currentState = TRANSITION_NONE;
                    _servos.standPosition();
                    Serial.println("[TRANSFORM] Recovery Shake Shape Transition Complete.");
                }
            }
            break;
        }
        default:
            _currentState = TRANSITION_NONE;
            break;
    }
}
