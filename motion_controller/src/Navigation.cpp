#include "Navigation.h"

Navigation::Navigation(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, ServoControl& servos)
    : _car(car), _balance(balance), _obstacle(obstacle), _servos(servos) {}

void Navigation::updateSmoothMotors() {
    _currentLeftSpeed += (_targetLeftSpeed - _currentLeftSpeed) * SMOOTHING_FACTOR;
    _currentRightSpeed += (_targetRightSpeed - _currentRightSpeed) * SMOOTHING_FACTOR;
    _car.applySmoothSpeeds((int)_currentLeftSpeed, (int)_currentRightSpeed);
}

void Navigation::updateActiveScan(bool isMovingForward) {
    static unsigned long lastSweep = 0;
    static int sweepPos = 90;
    static int sweepDir = 5;
    
    if (isMovingForward && millis() - lastSweep > 50) {
        sweepPos += sweepDir;
        if (sweepPos >= 135 || sweepPos <= 45) sweepDir *= -1;
        
        _servos.setPan(sweepPos);
        int dist = _obstacle.getDistance();
        
        if (dist > 0 && dist < SAFE_DISTANCE_CM) {
            Serial.println("[SAFETY] Side Obstacle Detected at " + String(sweepPos) + " deg! Distance: " + String(dist));
            _car.stop();
            Serial2.println("STATUS: Safety stop! Obstacle at " + String(sweepPos) + " degrees.");
            _servos.setPan(90); 
        }
        lastSweep = millis();
    }
}

void Navigation::processNavigation(float currentYaw) {
    if (!_isNavigating) return;
    
    float dx = _targetX - _currentX;
    float dy = _targetY - _currentY;
    float distance = sqrt(dx*dx + dy*dy);
    float angleToTarget = atan2(dy, dx) * 180.0 / PI;
    
    if (distance < 5.0) { 
        Serial.println("[NAV] Target Reached!");
        _targetLeftSpeed = 0; _targetRightSpeed = 0;
        _isNavigating = false;
        return;
    }
    
    float yawError = angleToTarget - currentYaw;
    if (yawError > 180) yawError -= 360;
    if (yawError < -180) yawError += 360;
    
    if (abs(yawError) > 15) {
        if (yawError > 0) { _targetLeftSpeed = 150; _targetRightSpeed = -150; }
        else { _targetLeftSpeed = -150; _targetRightSpeed = 150; }
    } else {
        _targetLeftSpeed = 180; _targetRightSpeed = 180;
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
                _car.stop();
                delay(500);
                _car.moveBackward(150); delay(1000);
                _car.turnLeft(); delay(800);
                _car.stop();
                moveStartTime = millis();
            }
            #endif
        }
    } else {
        wasMoving = false;
    }
}

int Navigation::adaptiveForwardSpeed(int distance) {
    if (distance > 85) return 190;
    if (distance > SAFE_DISTANCE_CM) return 165;
    return 135;
}

void Navigation::escapeObstacle(bool& lastTurnWasLeft) {
    _car.stop();
    delay(100);

    _car.moveBackward();
    delay(REVERSE_TIME_MS);
    _car.stop();
    delay(100);

    ScanResult best = _obstacle.quickScan();

    if (best.distance < CAUTION_DISTANCE_CM) {
        best = _obstacle.deepScan();
    }

    if (best.distance < BLOCK_DISTANCE_CM || _obstacle.allDirectionsBlocked()) {
        Serial.println("Dead-end detected -> stronger escape turn");
        if (lastTurnWasLeft) {
            _car.setSpeed(185);
            _car.turnRight();
            delay(700);
            lastTurnWasLeft = false;
        } else {
            _car.setSpeed(185);
            _car.turnLeft();
            delay(700);
            lastTurnWasLeft = true;
        }
        _car.stop();
        delay(100);
        _obstacle.resetHead();
        return;
    }

    int delta = best.pan - 90;
    int turnMs = map(constrain(abs(delta), 0, 90), 0, 90, TURN_BASE_MS_MIN, TURN_BASE_MS_MAX);

    if (abs(delta) <= 10) {
        _car.setSpeed(135);
        _car.moveForward();
        delay(220);
        _car.stop();
        _obstacle.resetHead();
        return;
    }

    _car.setSpeed(185);
    if (delta < 0) {
        _car.turnLeft();
        delay(turnMs);
        lastTurnWasLeft = true;
    } else {
        _car.turnRight();
        delay(turnMs);
        lastTurnWasLeft = false;
    }
    _car.stop();
    delay(90);
    _obstacle.resetHead();
}
