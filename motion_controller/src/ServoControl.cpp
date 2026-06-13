#include "ServoControl.h"
#include "Config.h"

ServoControl::ServoControl(uint8_t addr) : _pwm1(0x40), _pwm2(0x41) {
    for (int i = 0; i < NUM_SERVOS; i++) {
        _servoPos[i] = 90;
        _targetPos[i] = 90;
        _moveSpeed[i] = 5;
        _lastMoveTime[i] = millis();
    }
}

void ServoControl::begin() {
    _pwm1.begin();
    _pwm1.setPWMFreq(50); // Standard analog servo frequency
    
    _pwm2.begin();
    _pwm2.setPWMFreq(50); 
    
    delay(100);
    // Initialize all servos to 90 degrees
    for (int i = 0; i < NUM_SERVOS; i++) {
        if (i < 16) {
            _pwm1.setPWM(i, 0, angleToPulse(90));
        } else {
            _pwm2.setPWM(i - 16, 0, angleToPulse(90));
        }
        _servoPos[i] = 90;
        _lastMoveTime[i] = millis();
    }
}

int ServoControl::angleToPulse(int angle) {
    return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

void ServoControl::wakeServos() {
    if (!_isAsleep) return;
    for (int i = 0; i < NUM_SERVOS; i++) {
        if (i < 16) {
            _pwm1.setPWM(i, 0, angleToPulse(_servoPos[i]));
        } else {
            _pwm2.setPWM(i - 16, 0, angleToPulse(_servoPos[i]));
        }
    }
    _isAsleep = false;
    Serial.println("[SERVO] Waking all servos.");
}

void ServoControl::updateSleep() {
    #if USE_SERVO_SLEEP
    if (_isAsleep) return;
    
    bool allIdle = true;
    for (int i = 0; i < NUM_SERVOS; i++) {
        if (millis() - _lastMoveTime[i] < 3000) { // 3 seconds idle time
            allIdle = false;
            break;
        }
    }

    if (allIdle && _currentAction == ACTION_NONE) {
        for (int i = 0; i < NUM_SERVOS; i++) {
            if (i < 16) {
                _pwm1.setPWM(i, 0, 4096); // Fully OFF for PCA9685
            } else {
                _pwm2.setPWM(i - 16, 0, 4096);
            }
        }
        _isAsleep = true;
        Serial.println("[SERVO] Anti-Zitter Active (Sleep).");
    }
    #endif
}

void ServoControl::moveServoSmooth(int channel, int targetAngle, int speedDelay) {
    if (channel < 0 || channel >= NUM_SERVOS) return;
    
    if (_isAsleep) wakeServos();
    _targetPos[channel] = targetAngle;
    _moveSpeed[channel] = speedDelay;
}

void ServoControl::update() {
    unsigned long now = millis();
    bool moving = false;
    
    for (int i = 0; i < NUM_SERVOS; i++) {
        if (_servoPos[i] != _targetPos[i]) {
            moving = true;
            if (now - _lastMoveTime[i] >= (unsigned long)_moveSpeed[i]) {
                if (_servoPos[i] < _targetPos[i]) _servoPos[i]++;
                else _servoPos[i]--;
                
                if (i < 16) {
                    _pwm1.setPWM(i, 0, angleToPulse(_servoPos[i]));
                } else {
                    _pwm2.setPWM(i - 16, 0, angleToPulse(_servoPos[i]));
                }
                _lastMoveTime[i] = now;
            }
        }
    }
    
    if (moving) _lastActivityTime = now;
    
    // Execute active multi-step action non-blockingly
    if (_currentAction != ACTION_NONE) {
        processActionStep();
    }
    
    updateBreathing();
    updateSleep();
}

void ServoControl::updateBreathing() {
    if (!_breathingEnabled || _isAsleep || _currentAction != ACTION_NONE) return;
    
    // Only breathe if we haven't moved manually for 2 seconds
    if (millis() - _lastActivityTime < 2000) return;

    static float angle = 0;
    angle += 0.03; // Speed of breathing
    if (angle > TWO_PI) angle = 0;

    // Subtle sway for Hips (Channel 0/1)
    float offset = sin(angle) * 2.5; 
    
    _pwm.setPWM(0, 0, angleToPulse(90 + offset * 0.5));
    _pwm.setPWM(1, 0, angleToPulse(90 - offset * 0.5));
}

void ServoControl::moveGroup(int channels[], int targets[], int count) {
    for (int i = 0; i < count; i++) {
        moveServoSmooth(channels[i], targets[i], 5);
    }
}

void ServoControl::standPosition() {
    stopAction();
    for (int i = 0; i < NUM_SERVOS; i++) {
        moveServoSmooth(i, 90, 5);
    }
}

void ServoControl::walkForward() {
    if (_currentAction != ACTION_WALK) {
        _currentAction = ACTION_WALK;
        _actionStep = 0;
        _lastActionStepTime = 0; // Trigger step 0 immediately
    }
}

void ServoControl::transformToCar() {
    if (_currentAction != ACTION_TRANSFORM_CAR) {
        _currentAction = ACTION_TRANSFORM_CAR;
        _actionStep = 0;
        _lastActionStepTime = millis();
        // Start folding legs immediately
        moveServoSmooth(2, 30);
        moveServoSmooth(3, 30);
    }
}

void ServoControl::transformToCrawler() {
    if (_currentAction != ACTION_TRANSFORM_CRAWLER) {
        _currentAction = ACTION_TRANSFORM_CRAWLER;
        _actionStep = 0;
        _lastActionStepTime = millis();
        // Start spreading hips immediately
        moveServoSmooth(0, 160);
        moveServoSmooth(1, 20);
    }
}

void ServoControl::pushMotion() {
    if (_currentAction != ACTION_PUSH) {
        _currentAction = ACTION_PUSH;
        _actionStep = 0;
        _lastActionStepTime = millis();
        moveServoSmooth(4, 90);
        moveServoSmooth(5, 90);
    }
}

void ServoControl::kickMotion() {
    if (_currentAction != ACTION_KICK) {
        _currentAction = ACTION_KICK;
        _actionStep = 0;
        _lastActionStepTime = millis();
        moveServoSmooth(0, 60); // Lift leg
    }
}

void ServoControl::recoverFromFall(FallDirection dir) {
    if (dir == NO_FALL) return;

    Serial.println("[RECOVERY] Triggering non-blocking self-righting sequence...");

    if (dir == FALL_FORWARD) {
        _currentAction = ACTION_RECOVERY_FORWARD;
        _actionStep = 0;
        _lastActionStepTime = millis();
        moveServoSmooth(4, 160); // Right arm forward
        moveServoSmooth(5, 20);  // Left arm forward
    } else if (dir == FALL_BACKWARD) {
        _currentAction = ACTION_RECOVERY_BACKWARD;
        _actionStep = 0;
        _lastActionStepTime = millis();
        moveServoSmooth(0, 150); // Hips forward
        moveServoSmooth(1, 30);
    } else {
        _currentAction = ACTION_RECOVERY_SHAKE;
        _actionStep = 0;
        _shakeIteration = 0;
        _lastActionStepTime = millis();
        moveServoSmooth(4, 40);
        moveServoSmooth(5, 140);
    }
}

void ServoControl::stopAction() {
    _currentAction = ACTION_NONE;
    _actionStep = 0;
    _shakeIteration = 0;
}

void ServoControl::processActionStep() {
    unsigned long now = millis();
    
    switch (_currentAction) {
        case ACTION_WALK: {
            if (now - _lastActionStepTime < 200) return;
            _lastActionStepTime = now;
            
            switch (_actionStep) {
                case 0:
                    moveServoSmooth(0, 70);  // left hip
                    moveServoSmooth(1, 110); // right hip
                    _actionStep++;
                    break;
                case 1:
                    moveServoSmooth(2, 60);  // left knee
                    _actionStep++;
                    break;
                case 2:
                    moveServoSmooth(2, 90);
                    moveServoSmooth(0, 90);
                    moveServoSmooth(1, 90);
                    _actionStep++;
                    break;
                case 3:
                    moveServoSmooth(0, 110);
                    moveServoSmooth(1, 70);
                    _actionStep++;
                    break;
                case 4:
                    moveServoSmooth(3, 60);  // right knee
                    _actionStep++;
                    break;
                case 5:
                    moveServoSmooth(3, 90);
                    moveServoSmooth(0, 90);
                    moveServoSmooth(1, 90);
                    _actionStep = 0; // Repeat sequence
                    break;
            }
            break;
        }
        case ACTION_TRANSFORM_CAR: {
            if (_actionStep == 0 && now - _lastActionStepTime >= 300) {
                moveServoSmooth(4, 20); // Fold arms
                moveServoSmooth(5, 160);
                _actionStep = 1;
                _lastActionStepTime = now;
            } else if (_actionStep == 1 && now - _lastActionStepTime >= 300) {
                moveServoSmooth(6, 150); // Rotate body
                moveServoSmooth(7, 30);
                _actionStep = 2;
                _lastActionStepTime = now;
            } else if (_actionStep == 2 && now - _lastActionStepTime >= 300) {
                moveServoSmooth(8, 0);   // Final lock
                moveServoSmooth(9, 180);
                _currentAction = ACTION_NONE; // Complete
                Serial.println("[TRANSFORM] Car Transformation Done.");
            }
            break;
        }
        case ACTION_TRANSFORM_CRAWLER: {
            if (_actionStep == 0 && now - _lastActionStepTime >= 300) {
                moveServoSmooth(2, 160); // Bend knees to lower chassis
                moveServoSmooth(3, 20);
                _actionStep = 1;
                _lastActionStepTime = now;
            } else if (_actionStep == 1 && now - _lastActionStepTime >= 300) {
                moveServoSmooth(4, 150); // Spread arms for balance
                moveServoSmooth(5, 30);
                _actionStep = 2;
                _lastActionStepTime = now;
            } else if (_actionStep == 2 && now - _lastActionStepTime >= 200) {
                _currentAction = ACTION_NONE; // Complete
                Serial.println("[TRANSFORM] Crawler Transformation Done.");
            }
            break;
        }
        case ACTION_PUSH: {
            if (_actionStep == 0 && now - _lastActionStepTime >= 200) {
                moveServoSmooth(4, 30); // Push forward (Shoulders/Arms)
                moveServoSmooth(5, 150);
                _actionStep = 1;
                _lastActionStepTime = now;
            } else if (_actionStep == 1 && now - _lastActionStepTime >= 500) {
                moveServoSmooth(4, 90); // Return to neutral
                moveServoSmooth(5, 90);
                _currentAction = ACTION_NONE; // Complete
            }
            break;
        }
        case ACTION_KICK: {
            if (_actionStep == 0 && now - _lastActionStepTime >= 200) {
                moveServoSmooth(2, 160); // Snap kick (knee)
                _actionStep = 1;
                _lastActionStepTime = now;
            } else if (_actionStep == 1 && now - _lastActionStepTime >= 300) {
                moveServoSmooth(2, 90);  // Retract
                moveServoSmooth(0, 90);
                _currentAction = ACTION_NONE; // Complete
            }
            break;
        }
        case ACTION_RECOVERY_FORWARD: {
            if (_actionStep == 0 && now - _lastActionStepTime >= 500) {
                moveServoSmooth(4, 40);  // Snap back to push
                moveServoSmooth(5, 140); 
                _actionStep = 1;
                _lastActionStepTime = now;
            } else if (_actionStep == 1 && now - _lastActionStepTime >= 300) {
                _currentAction = ACTION_NONE;
                standPosition();
                Serial.println("[RECOVERY] Forward sequence complete.");
            }
            break;
        }
        case ACTION_RECOVERY_BACKWARD: {
            if (_actionStep == 0 && now - _lastActionStepTime >= 400) {
                moveServoSmooth(2, 160); // Knees snap
                moveServoSmooth(3, 20);
                _actionStep = 1;
                _lastActionStepTime = now;
            } else if (_actionStep == 1 && now - _lastActionStepTime >= 300) {
                _currentAction = ACTION_NONE;
                standPosition();
                Serial.println("[RECOVERY] Backward sequence complete.");
            }
            break;
        }
        case ACTION_RECOVERY_SHAKE: {
            if (now - _lastActionStepTime < 100) return;
            _lastActionStepTime = now;

            if (_actionStep == 0) {
                moveServoSmooth(4, 140);
                moveServoSmooth(5, 40);
                _actionStep = 1;
            } else {
                moveServoSmooth(4, 40);
                moveServoSmooth(5, 140);
                _actionStep = 0;
                _shakeIteration++;
                
                if (_shakeIteration >= 3) {
                    _currentAction = ACTION_NONE;
                    standPosition();
                    Serial.println("[RECOVERY] Shake sequence complete.");
                }
            }
            break;
        }
        default:
            _currentAction = ACTION_NONE;
            break;
    }
}
