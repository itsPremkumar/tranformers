#include "ObstacleAvoidance.h"

ObstacleAvoidance::ObstacleAvoidance(uint8_t trigPin, uint8_t echoPin, HeadControl& head) 
    : _head(head) {
    _trigPin = trigPin;
    _echoPin = echoPin;
}

void ObstacleAvoidance::begin() {
    pinMode(_trigPin, OUTPUT);
    pinMode(_echoPin, INPUT);
    resetHead();
}

int ObstacleAvoidance::getDistance() {
    return _cachedFrontDistance;
}

int ObstacleAvoidance::readFrontDistance() {
    return _cachedFrontDistance;
}

int ObstacleAvoidance::readGroundDistance() {
    return _cachedGroundDistance;
}

int ObstacleAvoidance::getDistanceOnce() {
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);
    
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trigPin, LOW);
    
    // Decreased timeout to 12000us (~2 meters range) to avoid blocking the CPU
    unsigned long duration = pulseIn(_echoPin, HIGH, 12000); 
    
    if (duration == 0) return 200; // no echo
    
    int distance = (int)(duration * 0.0343 / 2.0);
    if (distance <= 0) distance = 200;
    return distance;
}

int ObstacleAvoidance::readAverageDistanceBlocking(int samples) {
    long sum = 0;
    int validCount = 0;
    
    for (int i = 0; i < samples; i++) {
        int d = getDistanceOnce();
        sum += d;
        validCount++;
        // Reduced settling delay to 15ms to speed up blocking routines
        delay(15);
    }
    
    if (validCount == 0) return 200;
    return sum / validCount;
}

int ObstacleAvoidance::readDistanceMedianBlocking(int samples) {
    if (samples < 3) samples = 3;
    if (samples > 9) samples = 9;

    int values[9];
    int count = 0;

    for (int i = 0; i < samples; i++) {
        int d = getDistanceOnce();
        if (d > 0 && d <= 250) {
            values[count++] = d;
        }
        delay(8);
    }

    if (count == 0) return 250;

    // Bubble sort
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

int ObstacleAvoidance::readFrontDistanceBlocking() {
    _head.setTarget(_panCenter, _tiltForward);
    delay(200); // Wait for servo to physically move
    _cachedFrontDistance = readAverageDistanceBlocking(3);
    return _cachedFrontDistance;
}

int ObstacleAvoidance::readGroundDistanceBlocking() {
    _head.setTarget(_panCenter, _tiltDown);
    delay(220); // Wait for servo to physically move
    _cachedGroundDistance = readAverageDistanceBlocking(3);
    return _cachedGroundDistance;
}

int ObstacleAvoidance::scanLeftBlocking() {
    _head.setTarget(_panLeft, _tiltForward);
    delay(250);
    int d = readAverageDistanceBlocking(3);
    _head.setTarget(_panCenter, _tiltForward);
    delay(120);
    return d;
}

int ObstacleAvoidance::scanRightBlocking() {
    _head.setTarget(_panRight, _tiltForward);
    delay(250);
    int d = readAverageDistanceBlocking(3);
    _head.setTarget(_panCenter, _tiltForward);
    delay(120);
    return d;
}

void ObstacleAvoidance::resetHead() {
    _head.reset();
}

void ObstacleAvoidance::startQuickScan() {
    _scanState = SCAN_QUICK_ACTIVE;
    _scanIndex = 0;
    _bestScanResult.score = -999999;
    
    // Command head to first target
    _head.setTarget(45, _tiltDrive);
    _lastScanStepTime = millis();
}

void ObstacleAvoidance::startDeepScan() {
    _scanState = SCAN_DEEP_ACTIVE;
    _scanIndex = 0;
    _bestScanResult.score = -999999;
    
    // Command head to first target of grid (21 items)
    _head.setTarget(_panAngles[0], _tiltAngles[0]);
    _lastScanStepTime = millis();
}

void ObstacleAvoidance::processQuickScanStep() {
    if (_head.isMoving() || millis() - _lastScanStepTime < 40) return;

    const int quickPans[] = {45, 90, 135};
    int pan = quickPans[_scanIndex];
    int d = readDistanceMedianBlocking(3);
    updateMemory(pan, _tiltDrive, d);

    int score = (d * 11) - (abs(pan - _panCenter) * 2) - getMemoryPenalty(pan, _tiltDrive);
    if (d >= SAFE_DISTANCE_CM) score += 40;

    if (score > _bestScanResult.score) {
        _bestScanResult.pan = pan;
        _bestScanResult.tilt = _tiltDrive;
        _bestScanResult.distance = d;
        _bestScanResult.score = score;
    }

    _scanIndex++;
    if (_scanIndex >= 3) {
        _latestScanResult = _bestScanResult;
        _scanState = SCAN_IDLE;
        _head.reset();
    } else {
        int nextPan = quickPans[_scanIndex];
        _head.setTarget(nextPan, _tiltDrive);
        _lastScanStepTime = millis();
    }
}

void ObstacleAvoidance::processDeepScanStep() {
    if (_head.isMoving() || millis() - _lastScanStepTime < 45) return;

    int pi = _scanIndex / TILT_COUNT;
    int ti = _scanIndex % TILT_COUNT;

    int pan = _panAngles[pi];
    int tilt = _tiltAngles[ti];

    int d = readDistanceMedianBlocking(3); // Reduced samples to speed up DeepScan
    updateMemory(pan, tilt, d);

    int score = (d * 11) 
                - (abs(pan - _panCenter) * 3) 
                - (abs(tilt - _tiltDrive) * 2) 
                - getMemoryPenalty(pan, tilt);

    if (d >= SAFE_DISTANCE_CM) score += 40;
    if (d >= CAUTION_DISTANCE_CM) score += 20;
    if (d >= 120) score += 15;
    if (tilt == _tiltDrive) score += 8;

    if (score > _bestScanResult.score) {
        _bestScanResult.pan = pan;
        _bestScanResult.tilt = tilt;
        _bestScanResult.distance = d;
        _bestScanResult.score = score;
    }

    _scanIndex++;
    if (_scanIndex >= (PAN_COUNT * TILT_COUNT)) {
        _latestScanResult = _bestScanResult;
        _scanState = SCAN_IDLE;
        _head.reset();
    } else {
        int nextPi = _scanIndex / TILT_COUNT;
        int nextTi = _scanIndex % TILT_COUNT;
        _head.setTarget(_panAngles[nextPi], _tiltAngles[nextTi]);
        _lastScanStepTime = millis();
    }
}

void ObstacleAvoidance::update() {
    decayMemoryIfNeeded();
    
    if (_scanState == SCAN_QUICK_ACTIVE) {
        processQuickScanStep();
    } else if (_scanState == SCAN_DEEP_ACTIVE) {
        processDeepScanStep();
    } else {
        // IDLE: Periodic non-blocking refresh of front / ground distance
        unsigned long now = millis();
        if (!_head.isMoving() && now - _lastFrontMeasureTime > 80) {
            _lastFrontMeasureTime = now;
            int dist = getDistanceOnce();
            if (_head.getPan() == _panCenter) {
                if (_head.getTilt() == _tiltForward || _head.getTilt() == _tiltDrive) {
                    _cachedFrontDistance = dist;
                } else if (_head.getTilt() == _tiltDown) {
                    _cachedGroundDistance = dist;
                }
            }
        }
    }
}

bool ObstacleAvoidance::detectCliffOrDrop() {
    // Keep it simple and quick
    int centerDist = _cachedFrontDistance;
    int downDist = _cachedGroundDistance;
    
    if (centerDist != 250 && downDist >= 180 && centerDist < 120) return true;
    if (centerDist != 250 && (downDist - centerDist) > 85) return true;
    return false;
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

    if (distance < BLOCK_DISTANCE_CM) {
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

bool ObstacleAvoidance::allDirectionsBlocked() {
    int blockedCount = 0;
    for (int i = 0; i < PAN_COUNT; i++) {
        for (int j = 0; j < TILT_COUNT; j++) {
            if (_lastDistanceMap[i][j] > 0 && _lastDistanceMap[i][j] < BLOCK_DISTANCE_CM) {
                blockedCount++;
            }
        }
    }
    return (blockedCount >= ((PAN_COUNT * TILT_COUNT) * 2 / 3));
}
