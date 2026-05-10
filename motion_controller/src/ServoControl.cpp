#include "ServoControl.h"

ServoControl::ServoControl(uint8_t addr) : _pwm(addr) {
    for (int i = 0; i < NUM_SERVOS; i++) {
        _servoPos[i] = 90;
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
    }
}

int ServoControl::angleToPulse(int angle) {
    return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

void ServoControl::moveServoSmooth(int channel, int targetAngle, int speedDelay) {
    if (channel < 0 || channel >= NUM_SERVOS) return;
    
    int current = _servoPos[channel];
    
    if (current < targetAngle) {
        for (int pos = current; pos <= targetAngle; pos++) {
            _pwm.setPWM(channel, 0, angleToPulse(pos));
            delay(speedDelay);
        }
    } else {
        for (int pos = current; pos >= targetAngle; pos--) {
            _pwm.setPWM(channel, 0, angleToPulse(pos));
            delay(speedDelay);
        }
    }
    
    _servoPos[channel] = targetAngle;
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
