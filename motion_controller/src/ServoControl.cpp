#include "ServoControl.h"

ServoControl::ServoControl(uint8_t addr) : _pwm(addr) {
    for (int i = 0; i < NUM_SERVOS; i++) {
        _servoPos[i] = 90;
        _targetPos[i] = 90;
        _moveSpeed[i] = 5;
        _lastMoveTime[i] = millis();
    }
}

void ServoControl::begin() {
    _pwm.begin();
    _pwm.setPWMFreq(50); // Standard analog servo frequency
    
    delay(100);
    // Initialize all servos to 90 degrees
    for (int i = 0; i < NUM_SERVOS; i++) {
        _pwm.setPWM(i, 0, angleToPulse(90));
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
        _pwm.setPWM(i, 0, angleToPulse(_servoPos[i]));
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

    if (allIdle) {
        for (int i = 0; i < NUM_SERVOS; i++) {
            _pwm.setPWM(i, 0, 4096); // Fully OFF for PCA9685
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
                
                _pwm.setPWM(i, 0, angleToPulse(_servoPos[i]));
                _lastMoveTime[i] = now;
            }
        }
    }
    
    if (moving) _lastActivityTime = now;
    
    updateBreathing();
    updateSleep();
}

void ServoControl::updateBreathing() {
    if (!_breathingEnabled || _isAsleep) return;
    
    // Only breathe if we haven't moved manually for 2 seconds
    if (millis() - _lastActivityTime < 2000) return;

    static float angle = 0;
    angle += 0.03; // Speed of breathing
    if (angle > TWO_PI) angle = 0;

    // Subtle sway for Head (Channel 14/15) and Hips (Channel 0/1)
    float offset = sin(angle) * 2.5; // 2.5 degree sway
    
    // Apply offset to target to let update() handle the smooth transition
    // Head Tilt (Subtle up/down)
    _pwm.setPWM(15, 0, angleToPulse(90 + offset)); 
    // Hips (Subtle side sway)
    _pwm.setPWM(0, 0, angleToPulse(90 + offset * 0.5));
    _pwm.setPWM(1, 0, angleToPulse(90 - offset * 0.5));
}

void ServoControl::moveGroup(int channels[], int targets[], int count) {
    for (int i = 0; i < count; i++) {
        moveServoSmooth(channels[i], targets[i], 5);
    }
}

void ServoControl::standPosition() {
    for (int i = 0; i < NUM_SERVOS; i++) {
        moveServoSmooth(i, 90, 5);
    }
}

void ServoControl::walkForward() {
    // Step 1
    moveServoSmooth(0, 70);  // left hip
    moveServoSmooth(1, 110); // right hip
    delay(200);

    // Step 2
    moveServoSmooth(2, 60);  // left knee
    delay(200);

    // Step 3
    moveServoSmooth(2, 90);
    moveServoSmooth(0, 90);
    moveServoSmooth(1, 90);
    delay(200);

    // Step 4
    moveServoSmooth(0, 110);
    moveServoSmooth(1, 70);
    delay(200);

    // Step 5
    moveServoSmooth(3, 60);  // right knee
    delay(200);

    // Step 6
    moveServoSmooth(3, 90);
    moveServoSmooth(0, 90);
    moveServoSmooth(1, 90);
    delay(200);
}

void ServoControl::transformToCar() {
    // Fold legs
    moveServoSmooth(2, 30);
    moveServoSmooth(3, 30);
    delay(300);

    // Fold arms
    moveServoSmooth(4, 20);
    moveServoSmooth(5, 160);
    delay(300);

    // Rotate body
    moveServoSmooth(6, 150);
    moveServoSmooth(7, 30);
    delay(300);

    // Final lock
    moveServoSmooth(8, 0);
    moveServoSmooth(9, 180);
}

void ServoControl::transformToCrawler() {
    // Spread hips wide
    moveServoSmooth(0, 160); // Left hip out
    moveServoSmooth(1, 20);  // Right hip out
    delay(300);

    // Bend knees to lower the chassis
    moveServoSmooth(2, 160); // Left knee
    moveServoSmooth(3, 20);  // Right knee
    delay(300);

    // Spread arms for balance
    moveServoSmooth(4, 150);
    moveServoSmooth(5, 30);
    delay(200);
}

void ServoControl::pushMotion() {
    // Start with arms in neutral
    moveServoSmooth(4, 90);
    moveServoSmooth(5, 90);
    delay(200);

    // Push forward (Shoulders/Arms)
    moveServoSmooth(4, 30);
    moveServoSmooth(5, 150);
    delay(500); // Hold the push

    // Return to neutral
    moveServoSmooth(4, 90);
    moveServoSmooth(5, 90);
}

void ServoControl::kickMotion() {
    // Lift leg (hip)
    moveServoSmooth(0, 60); 
    delay(200);

    // Snap kick (knee)
    moveServoSmooth(2, 160);
    delay(300);

    // Retract
    moveServoSmooth(2, 90);
    moveServoSmooth(0, 90);
}

void ServoControl::recoverFromFall(FallDirection dir) {
    if (dir == NO_FALL) return;

    Serial.println("[RECOVERY] Executing self-righting sequence...");

    if (dir == FALL_FORWARD) {
        // Use arms to push back
        moveServoSmooth(4, 160); // Right arm forward
        moveServoSmooth(5, 20);  // Left arm forward
        delay(500);
        moveServoSmooth(4, 40);  // Snap back to push
        moveServoSmooth(5, 140); 
        delay(300);
    } else if (dir == FALL_BACKWARD) {
        // Use legs to push forward
        moveServoSmooth(0, 150); // Hips forward
        moveServoSmooth(1, 30);
        delay(400);
        moveServoSmooth(2, 160); // Knees snap
        moveServoSmooth(3, 20);
        delay(300);
    } else {
        // General shake to try and get up
        for(int i=0; i<3; i++) {
            moveServoSmooth(4, 40);
            moveServoSmooth(5, 140);
            delay(100);
            moveServoSmooth(4, 140);
            moveServoSmooth(5, 40);
            delay(100);
        }
    }

    // Return to stand
    standPosition();
    Serial.println("[RECOVERY] Sequence complete.");
}
