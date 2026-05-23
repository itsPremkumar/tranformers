#ifndef OBSTACLE_AVOIDANCE_H
#define OBSTACLE_AVOIDANCE_H

#include <Arduino.h>
#include "Config.h"
#include "HeadControl.h"

struct ScanResult {
    int pan;
    int tilt;
    int distance;
    int score;
};

/**
 * @class ObstacleAvoidance
 * @brief Manages HC-SR04 ultrasonic sensor readings, spatial mapping, and collision warnings.
 * 
 * Works in tandem with HeadControl to perform non-blocking spatial sweeps, keeping the main loop
 * running at high frequency.
 */
class ObstacleAvoidance {
public:
    ObstacleAvoidance(uint8_t trigPin, uint8_t echoPin, HeadControl& head);
    void begin();
    
    /**
     * @brief Periodic update function. Runs the non-blocking background sensor scanning.
     */
    void update();

    // --- Fast, Non-blocking Queries (returns cached values) ---
    int getDistance();
    int readFrontDistance();
    int readGroundDistance();
    
    // --- Synchronous/Blocking versions (mainly for initialization & self-tests) ---
    int readFrontDistanceBlocking();
    int readGroundDistanceBlocking();
    int scanLeftBlocking();
    int scanRightBlocking();

    // --- Advanced Scanning State Machine (Cooperative Non-blocking) ---
    void startQuickScan();
    void startDeepScan();
    bool isScanBusy() const { return _scanState != SCAN_IDLE; }
    ScanResult getLatestScanResult() const { return _latestScanResult; }

    bool detectCliffOrDrop();
    void decayMemoryIfNeeded();
    void resetHead();
    void updateMemory(int pan, int tilt, int distance);
    int getMemoryPenalty(int pan, int tilt);
    bool allDirectionsBlocked();

private:
    enum ScanState {
        SCAN_IDLE,
        SCAN_QUICK_ACTIVE,
        SCAN_DEEP_ACTIVE
    };

    uint8_t _trigPin;
    uint8_t _echoPin;
    HeadControl& _head;

    // Cached values
    int _cachedFrontDistance = 200;
    int _cachedGroundDistance = 30;
    
    // Non-blocking Sweep Variables
    ScanState _scanState = SCAN_IDLE;
    int _scanIndex = 0;
    unsigned long _lastScanStepTime = 0;
    ScanResult _latestScanResult;
    ScanResult _bestScanResult;

    // Advanced configuration
    static const int PAN_COUNT = 7;
    static const int TILT_COUNT = 3;
    const int _panAngles[PAN_COUNT] = {25, 45, 70, 90, 110, 135, 155};
    const int _tiltAngles[TILT_COUNT] = {72, 92, 118};
    
    const int _panCenter = 90;
    const int _panLeft = 150;
    const int _panRight = 30;
    const int _tiltForward = 90;
    const int _tiltDown = 125;
    const int _tiltDrive = 92;

    int _blockedHistory[PAN_COUNT][TILT_COUNT] = {0};
    int _lastDistanceMap[PAN_COUNT][TILT_COUNT] = {0};
    unsigned long _lastSeenMap[PAN_COUNT][TILT_COUNT] = {0};
    unsigned long _lastMemoryDecayMs = 0;
    unsigned long _lastFrontMeasureTime = 0;

    int getDistanceOnce();
    int readAverageDistanceBlocking(int samples = 3);
    int readDistanceMedianBlocking(int samples = 5);
    
    int panIndex(int pan);
    int tiltIndex(int tilt);
    
    // Internal non-blocking step executions
    void processQuickScanStep();
    void processDeepScanStep();
};

#endif // OBSTACLE_AVOIDANCE_H
