#ifndef NAVIGATION_H
#define NAVIGATION_H

#include <Arduino.h>
#include "Config.h"
#include "MotorControl.h"
#include "Balance.h"
#include "ObstacleAvoidance.h"
#include "ServoControl.h"
#include "HeadControl.h"

/**
 * @enum EscapeState
 * @brief Phases of the non-blocking obstacle escape maneuver.
 */
enum EscapeState {
    ESCAPE_IDLE,
    ESCAPE_STOP1,
    ESCAPE_BACKING,
    ESCAPE_STOP2,
    ESCAPE_SCANNING,
    ESCAPE_TURNING,
    ESCAPE_STOP3
};

/**
 * @class Navigation
 * @brief Manages path planning, waypoint tracking, active scanning, and non-blocking obstacle escapes.
 */
class Navigation {
public:
    Navigation(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, ServoControl& servos, HeadControl& head);
    
    /**
     * @brief Periodic active pan-scanning to detect obstacles.
     */
    void updateActiveScan(bool isMovingForward);
    
    /**
     * @brief Waypoint navigation and obstacle avoidance updates.
     */
    void processNavigation(float currentYaw);
    
    /**
     * @brief Stuck detection comparing target speed with IMU acceleration.
     */
    void checkStuckStatus(float amps);
    
    /**
     * @brief Triggers the non-blocking obstacle escape sequence.
     */
    void triggerEscape();
    
    /**
     * @brief Non-blocking updates of the escape maneuver state machine.
     */
    void updateEscape();
    
    int adaptiveForwardSpeed(int distance);
    
    // --- Target Waypoint Controls ---
    void setTargetSpeeds(int left, int right) { _car.setTargetSpeeds(left, right); }
    void setNavigationTarget(float x, float y) { _targetX = x; _targetY = y; _isNavigating = true; }
    void stopNavigation() { _isNavigating = false; _car.stop(); }
    
    bool isNavigating() const { return _isNavigating; }
    bool isEscaping() const { return _escapeState != ESCAPE_IDLE; }
    void setX(float x) { _currentX = x; }
    void setY(float y) { _currentY = y; }

private:
    MotorControl& _car;
    Balance& _balance;
    ObstacleAvoidance& _obstacle;
    ServoControl& _servos;
    HeadControl& _head;
    
    float _targetX = 0, _targetY = 0;
    float _currentX = 0, _currentY = 0;
    bool _isNavigating = false;

    // Non-blocking Escape State
    EscapeState _escapeState = ESCAPE_IDLE;
    unsigned long _escapeTimer = 0;
    int _escapeTurnMs = 0;
    bool _escapeLastTurnWasLeft = false;
    ScanResult _escapeBestScan;
};

#endif // NAVIGATION_H
