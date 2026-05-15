#include "ObstacleAvoidance.h"

ObstacleAvoidance::ObstacleAvoidance(uint8_t trigPin, uint8_t echoPin, uint8_t panPin, uint8_t tiltPin) {
    _trigPin = trigPin;
    _echoPin = echoPin;
    _panPin = panPin;
    _tiltPin = tiltPin;
}

void ObstacleAvoidance::begin() {
    pinMode(_trigPin, OUTPUT);
    pinMode(_echoPin, INPUT);
    
    _panServo.setPeriodHertz(50);
    _tiltServo.setPeriodHertz(50);
    
    _panServo.attach(_panPin, 500, 2400);
    _tiltServo.attach(_tiltPin, 500, 2400);
    
    _panServo.write(_panCenter);
    _tiltServo.write(_tiltForward);
}

int ObstacleAvoidance::getDistance() {
    return getDistanceOnce();
}

int ObstacleAvoidance::getDistanceOnce() {
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);
    
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trigPin, LOW);
    
    unsigned long duration = pulseIn(_echoPin, HIGH, 30000); // 30ms timeout
    
    if (duration == 0) return 200; // no echo
    
    int distance = (int)(duration * 0.0343 / 2.0);
    if (distance <= 0) distance = 200;
    return distance;
}

int ObstacleAvoidance::readAverageDistance(int samples) {
    long sum = 0;
    int validCount = 0;
    
    for (int i = 0; i < samples; i++) {
        int d = getDistanceOnce();
        sum += d;
        validCount++;
        delay(40);
    }
    
    if (validCount == 0) return 200;
    return sum / validCount;
}

int ObstacleAvoidance::readFrontDistance() {
    _panServo.write(_panCenter);
    _tiltServo.write(_tiltForward);
    delay(250);
    return readAverageDistance();
}

int ObstacleAvoidance::readGroundDistance() {
    _panServo.write(_panCenter);
    _tiltServo.write(_tiltDown);
    delay(300);
    return readAverageDistance();
}

int ObstacleAvoidance::scanLeft() {
    _panServo.write(_panLeft);
    _tiltServo.write(_tiltForward);
    delay(350);
    int d = readAverageDistance();
    _panServo.write(_panCenter);
    delay(150);
    return d;
}

int ObstacleAvoidance::scanRight() {
    _panServo.write(_panRight);
    _tiltServo.write(_tiltForward);
    delay(350);
    int d = readAverageDistance();
    _panServo.write(_panCenter);
    delay(150);
    return d;
}

// =====================================================
// ADVANCED FEATURES
// =====================================================

void ObstacleAvoidance::smoothServoWrite(Servo &servo, int &currentPos, int targetPos) {
    targetPos = constrain(targetPos, 0, 180);
    if (currentPos == targetPos) return;

    int step = (targetPos > currentPos) ? 1 : -1;
    while (currentPos != targetPos) {
        currentPos += step;
        servo.write(currentPos);
        delay(8); // SERVO_STEP_DELAY_MS
    }
}

void ObstacleAvoidance::resetHead() {
    smoothServoWrite(_panServo, _currentPan, _panCenter);
    smoothServoWrite(_tiltServo, _currentTilt, _tiltDrive);
    delay(35);
}

int ObstacleAvoidance::readDistanceMedian(int samples) {
    if (samples < 3) samples = 3;
    if (samples > 9) samples = 9;

    int values[9];
    int count = 0;

    for (int i = 0; i < samples; i++) {
        int d = getDistanceOnce();
        if (d > 0 && d <= 250) {
            values[count++] = d;
        }
        delay(10);
    }

    if (count == 0) return 250;

    // Sort small array (bubble sort)
    for (int i = 0; i < count - 1; i++) {
        for (int j = 0; j < count - i - 1; j++) {
            if (values[j] > values[j + 1]) {
                int t = values[j];
                values[j] = values[j + 1];
                values[j + 1] = t;
            }
        }
    }
    return values[count / 2];
}

int ObstacleAvoidance::panIndex(int pan) {
    for (int i = 0; i < PAN_COUNT; i++) {
        if (_panAngles[i] == pan) return i;
    }
    return -1;
}

int ObstacleAvoidance::tiltIndex(int tilt) {
    for (int i = 0; i < TILT_COUNT; i++) {
        if (_tiltAngles[i] == tilt) return i;
    }
    return -1;
}

void ObstacleAvoidance::updateMemory(int pan, int tilt, int distance) {
    int pi = panIndex(pan);
    int ti = tiltIndex(tilt);
    if (pi < 0 || ti < 0) return;

    _lastDistanceMap[pi][ti] = distance;
    _lastSeenMap[pi][ti] = millis();

    if (distance < BLOCK_DISTANCE_CM) { // BLOCK_DISTANCE_CM
        if (_blockedHistory[pi][ti] < 50) _blockedHistory[pi][ti]++;
    } else {
        if (_blockedHistory[pi][ti] > 0) _blockedHistory[pi][ti]--;
    }
}

int ObstacleAvoidance::getMemoryPenalty(int pan, int tilt) {
    int pi = panIndex(pan);
    int ti = tiltIndex(tilt);
    if (pi < 0 || ti < 0) return 0;

    int blocked = _blockedHistory[pi][ti];
    int lastD = _lastDistanceMap[pi][ti];
    int penalty = blocked * 6;
    if (lastD > 0 && lastD < BLOCK_DISTANCE_CM) penalty += 10;
    return penalty;
}

void ObstacleAvoidance::decayMemoryIfNeeded() {
    const unsigned long INTERVAL = 4000;
    if (millis() - _lastMemoryDecayMs < INTERVAL) return;
    _lastMemoryDecayMs = millis();

    for (int i = 0; i < PAN_COUNT; i++) {
        for (int j = 0; j < TILT_COUNT; j++) {
            if (_blockedHistory[i][j] > 0) _blockedHistory[i][j]--;
        }
    }
}

ScanResult ObstacleAvoidance::quickScan() {
    ScanResult best;
    best.pan = _panCenter;
    best.tilt = _tiltDrive;
    best.distance = 0;
    best.score = -999999;

    int quickPans[] = {45, 90, 135};
    for (int i = 0; i < 3; i++) {
        int pan = quickPans[i];
        smoothServoWrite(_panServo, _currentPan, pan);
        smoothServoWrite(_tiltServo, _currentTilt, _tiltDrive);
        delay(35);

        int d = readDistanceMedian(3);
        updateMemory(pan, _tiltDrive, d);

        int score = (d * 11) - (abs(pan - _panCenter) * 2) - getMemoryPenalty(pan, _tiltDrive);
        if (d >= 38) score += 40; // SAFE_DISTANCE_CM

        if (score > best.score) {
            best.pan = pan;
            best.tilt = _tiltDrive;
            best.distance = d;
            best.score = score;
        }
    }
    return best;
}

ScanResult ObstacleAvoidance::deepScan() {
    ScanResult best;
    best.pan = _panCenter;
    best.tilt = _tiltDrive;
    best.distance = 0;
    best.score = -999999;

    for (int i = 0; i < PAN_COUNT; i++) {
        for (int j = 0; j < TILT_COUNT; j++) {
            int pan = _panAngles[i];
            int tilt = _tiltAngles[j];

            smoothServoWrite(_panServo, _currentPan, pan);
            smoothServoWrite(_tiltServo, _currentTilt, tilt);
            delay(35);

            int d = readDistanceMedian(5);
            updateMemory(pan, tilt, d);

            int score = (d * 11) 
                        - (abs(pan - _panCenter) * 3) 
                        - (abs(tilt - _tiltDrive) * 2) 
                        - getMemoryPenalty(pan, tilt);

            if (d >= 38) score += 40;  // SAFE_DISTANCE_CM
            if (d >= 55) score += 20;  // CAUTION_DISTANCE_CM
            if (d >= 120) score += 15;
            if (tilt == _tiltDrive) score += 8;

            if (score > best.score) {
                best.pan = pan;
                best.tilt = tilt;
                best.distance = d;
                best.score = score;
            }
        }
    }
    return best;
}

bool ObstacleAvoidance::detectCliffOrDrop() {
    smoothServoWrite(_panServo, _currentPan, _panCenter);
    smoothServoWrite(_tiltServo, _currentTilt, _tiltForward);
    delay(35);
    int centerDist = readDistanceMedian(3);

    smoothServoWrite(_panServo, _currentPan, _panCenter);
    smoothServoWrite(_tiltServo, _currentTilt, _tiltDown);
    delay(35);
    int downDist = readDistanceMedian(3);

    resetHead();

    if (centerDist != 250 && downDist >= 180 && centerDist < 120) return true;
    if (centerDist != 250 && (downDist - centerDist) > 85) return true;

    return false;
}

bool ObstacleAvoidance::allDirectionsBlocked() {
    int blockedCount = 0;
    for (int i = 0; i < PAN_COUNT; i++) {
        for (int j = 0; j < TILT_COUNT; j++) {
            if (_lastDistanceMap[i][j] > 0 && _lastDistanceMap[i][j] < 26) {
                blockedCount++;
            }
        }
    }
    return (blockedCount >= ((PAN_COUNT * TILT_COUNT) * 2 / 3));
}

