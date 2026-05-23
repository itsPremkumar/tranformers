#include "Navigation.h"

Navigation::Navigation(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, ServoControl& servos, HeadControl& head)
    : _car(car), _balance(balance), _obstacle(obstacle), _servos(servos), _head(head) {}

void Navigation::updateActiveScan(bool isMovingForward) {
    static unsigned long lastSweep = 0;
    static int sweepPos = 90;
    static int sweepDir = 5;
    
    // Only sweep pan if moving and not busy with a manual scan
    if (isMovingForward && !_obstacle.isScanBusy() && millis() - lastSweep > 60) {
        sweepPos += sweepDir;
        if (sweepPos >= 135 || sweepPos <= 45) sweepDir *= -1;
        
        _head.setPan(sweepPos);
        int dist = _obstacle.getDistance();
        
        if (dist > 0 && dist < SAFE_DISTANCE_CM) {
            Serial.println("[SAFETY] Side Obstacle Detected at " + String(sweepPos) + " deg! Distance: " + String(dist));
            _car.stop(); // Safe stop using ramping
            Serial2.println("STATUS: Safety stop! Obstacle at " + String(sweepPos) + " degrees.");
            _head.reset(); 
        }
        lastSweep = millis();
    }
}

void Navigation::processNavigation(float currentYaw) {
    if (!_isNavigating) return;
    
    // If escaping, let the escape state machine execute
    if (isEscaping()) {
        updateEscape();
        return;
    }
    
    float dx = _targetX - _currentX;
    float dy = _targetY - _currentY;
    float distance = sqrt(dx*dx + dy*dy);
    float angleToTarget = atan2(dy, dx) * 180.0 / PI;
    
    // 1. Safety Check: Stop or trigger escape if something is in front
    #if USE_ULTRASONIC
    int frontDist = _obstacle.readFrontDistance();
    if (frontDist > 0 && frontDist < BLOCK_DISTANCE_CM) {
        triggerEscape();
        return;
    }
    #else
    int frontDist = 100; // Assume clear
    #endif

    // 2. Target Reached logic
    if (distance < 5.0f) { 
        Serial.println("[NAV] Target Reached!");
        _car.stop();
        _isNavigating = false;
        return;
    }
    
    // 3. Smooth Steering Calculation
    float yawError = angleToTarget - currentYaw;
    while (yawError > 180) yawError -= 360;
    while (yawError < -180) yawError += 360;
    
    if (abs(yawError) > 15) {
        // Pivot toward target with proportional power
        int turnPower = constrain(abs(yawError) * 5, SPEED_SLOW, SPEED_TURN);
        if (yawError > 0) {
            _car.setTargetSpeeds(turnPower, -turnPower);
        } else {
            _car.setTargetSpeeds(-turnPower, turnPower);
        }
    } else {
        // Drive forward with adaptive speed based on distance to obstacles
        int forwardSpeed = adaptiveForwardSpeed(frontDist);
        
        // 4. Dynamic Waypoint Braking: Slow down as we get very close to target
        if (distance < 30.0f) {
            forwardSpeed = map(distance, 5, 30, SPEED_SLOW, forwardSpeed);
        }
        
        _car.setTargetSpeeds(forwardSpeed, forwardSpeed);
    }
}

void Navigation::checkStuckStatus(float amps) {
    static unsigned long moveStartTime = 0;
    static bool wasMoving = false;
    
    if (_car.getSpeed() > 0) {
        if (!wasMoving) moveStartTime = millis();
        wasMoving = true;
        
        if (millis() - moveStartTime > 3000) {
            #if USE_MPU6050
            if (abs(_balance.getAccelX()) < 0.05 && amps > 0.5) { 
                Serial2.println("STATUS: I am stuck!");
                triggerEscape();
                moveStartTime = millis();
            }
            #endif
        }
    } else {
        wasMoving = false;
    }
}

int Navigation::adaptiveForwardSpeed(int distance) {
    int maxSpeed = _car.getSpeed();
    if (distance > 85) return maxSpeed;
    if (distance > SAFE_DISTANCE_CM) return (maxSpeed * 3) / 4; // 75% of slider speed
    return (maxSpeed * 1) / 2; // 50% of slider speed
}

void Navigation::triggerEscape() {
    if (_escapeState == ESCAPE_IDLE) {
        Serial.println("[ESCAPE] Obstacle encountered, triggering escape maneuver...");
        _escapeState = ESCAPE_STOP1;
        _car.stop();
        _escapeTimer = millis();
    }
}

void Navigation::updateEscape() {
    unsigned long now = millis();
    
    switch (_escapeState) {
        case ESCAPE_IDLE:
            break;
            
        case ESCAPE_STOP1:
            if (now - _escapeTimer >= 100) {
                _car.moveBackward();
                _escapeState = ESCAPE_BACKING;
                _escapeTimer = now;
            }
            break;
            
        case ESCAPE_BACKING:
            if (now - _escapeTimer >= REVERSE_TIME_MS) {
                _car.stop();
                _escapeState = ESCAPE_STOP2;
                _escapeTimer = now;
            }
            break;
            
        case ESCAPE_STOP2:
            if (now - _escapeTimer >= 100) {
                _obstacle.startQuickScan();
                _escapeState = ESCAPE_SCANNING;
            }
            break;
            
        case ESCAPE_SCANNING:
            if (!_obstacle.isScanBusy()) {
                static bool deepScanStarted = false;
                
                // If quick scan complete, check if we need a deep scan
                if (!deepScanStarted && _obstacle.getLatestScanResult().distance < CAUTION_DISTANCE_CM) {
                    _obstacle.startDeepScan();
                    deepScanStarted = true;
                    return;
                }
                
                // Deep scan done or quick scan was sufficient
                deepScanStarted = false;
                _escapeBestScan = _obstacle.getLatestScanResult();
                
                if (_escapeBestScan.distance < BLOCK_DISTANCE_CM || _obstacle.allDirectionsBlocked()) {
                    Serial.println("[ESCAPE] Dead-end detected! Stronger escape turn.");
                    _car.setSpeed(SPEED_TURN);
                    if (_escapeLastTurnWasLeft) {
                        _car.turnRight();
                        _escapeLastTurnWasLeft = false;
                    } else {
                        _car.turnLeft();
                        _escapeLastTurnWasLeft = true;
                    }
                    _escapeTurnMs = 700;
                    _escapeState = ESCAPE_TURNING;
                    _escapeTimer = now;
                    return;
                }
                
                int delta = _escapeBestScan.pan - 90;
                _escapeTurnMs = map(constrain(abs(delta), 0, 90), 0, 90, TURN_BASE_MS_MIN, TURN_BASE_MS_MAX);
                
                if (abs(delta) <= 10) {
                    _car.setSpeed(SPEED_SLOW);
                    _car.moveForward();
                    _escapeState = ESCAPE_TURNING;
                    _escapeTurnMs = 220;
                } else {
                    _car.setSpeed(SPEED_TURN);
                    if (delta < 0) {
                        _car.turnLeft();
                        _escapeLastTurnWasLeft = true;
                    } else {
                        _car.turnRight();
                        _escapeLastTurnWasLeft = false;
                    }
                    _escapeState = ESCAPE_TURNING;
                }
                _escapeTimer = now;
            }
            break;
            
        case ESCAPE_TURNING:
            if (now - _escapeTimer >= (unsigned long)_escapeTurnMs) {
                _car.stop();
                _escapeState = ESCAPE_STOP3;
                _escapeTimer = now;
            }
            break;
            
        case ESCAPE_STOP3:
            if (now - _escapeTimer >= 90) {
                _obstacle.resetHead();
                _escapeState = ESCAPE_IDLE; // Complete
                Serial.println("[ESCAPE] Escape maneuver complete.");
            }
            break;
    }
}
