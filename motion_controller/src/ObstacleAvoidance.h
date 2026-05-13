#ifndef OBSTACLE_AVOIDANCE_H
#define OBSTACLE_AVOIDANCE_H

#include <Arduino.h>
#include <ESP32Servo.h>
#include "Config.h"

struct ScanResult {
    int pan;
    int tilt;
    int distance;
    int score;
};

class ObstacleAvoidance {
public:
    ObstacleAvoidance(uint8_t trigPin, uint8_t echoPin, uint8_t panPin, uint8_t tiltPin);
    void begin();
    
    // Existing methods (preserved)
    int getDistance();
    int readFrontDistance();
    int readGroundDistance();
    int scanLeft();
    int scanRight();
    
    // New Advanced methods
    ScanResult quickScan();
    ScanResult deepScan();
    bool detectCliffOrDrop();
    void decayMemoryIfNeeded();
    void resetHead();
    void updateMemory(int pan, int tilt, int distance);
    int getMemoryPenalty(int pan, int tilt);
    bool allDirectionsBlocked();
    
    void setPan(int angle) { _panServo.write(angle); }
    void setTilt(int angle) { _tiltServo.write(angle); }
    void smoothServoWrite(Servo &servo, int &currentPos, int targetPos);

private:
    uint8_t _trigPin, _echoPin;
    uint8_t _panPin, _tiltPin;
    
    Servo _panServo;
    Servo _tiltServo;
    
    // Existing configuration
    const int _panCenter = 90;
    const int _panLeft = 150;
    const int _panRight = 30;
    const int _tiltForward = 90;
    const int _tiltDown = 125;

    // Advanced configuration
    static const int PAN_COUNT = 7;
    static const int TILT_COUNT = 3;
    const int _panAngles[PAN_COUNT] = {25, 45, 70, 90, 110, 135, 155};
    const int _tiltAngles[TILT_COUNT] = {72, 92, 118};
    const int _tiltDrive = 92;
    
    int _currentPan = 90;
    int _currentTilt = 92;
    
    int _blockedHistory[PAN_COUNT][TILT_COUNT] = {0};
    int _lastDistanceMap[PAN_COUNT][TILT_COUNT] = {0};
    unsigned long _lastSeenMap[PAN_COUNT][TILT_COUNT] = {0};
    unsigned long _lastMemoryDecayMs = 0;

    int getDistanceOnce();
    int readAverageDistance(int samples = 3);
    int readDistanceMedian(int samples = 5);
    
    int panIndex(int pan);
    int tiltIndex(int tilt);
};

#endif
