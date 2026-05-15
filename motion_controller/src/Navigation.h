#ifndef NAVIGATION_H
#define NAVIGATION_H

#include <Arduino.h>
#include "Config.h"
#include "MotorControl.h"
#include "Balance.h"
#include "ObstacleAvoidance.h"
#include "ServoControl.h"

class Navigation {
public:
    Navigation(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, ServoControl& servos);
    
    void updateSmoothMotors();
    void updateActiveScan(bool isMovingForward);
    void processNavigation(float currentYaw);
    void checkStuckStatus(float amps);
    void escapeObstacle(bool& lastTurnWasLeft);
    int adaptiveForwardSpeed(int distance);
    
    // Setters for targets
    void setTargetSpeeds(int left, int right) { _targetLeftSpeed = left; _targetRightSpeed = right; }
    void setNavigationTarget(float x, float y) { _targetX = x; _targetY = y; _isNavigating = true; }
    void stopNavigation() { _isNavigating = false; _targetLeftSpeed = 0; _targetRightSpeed = 0; }
    
    bool isNavigating() const { return _isNavigating; }
    void setX(float x) { _currentX = x; }
    void setY(float y) { _currentY = y; }

private:
    MotorControl& _car;
    Balance& _balance;
    ObstacleAvoidance& _obstacle;
    ServoControl& _servos;
    
    int _targetLeftSpeed = 0;
    int _targetRightSpeed = 0;
    float _currentLeftSpeed = 0;
    float _currentRightSpeed = 0;
    const float SMOOTHING_FACTOR = 0.15;
    
    float _targetX = 0, _targetY = 0;
    float _currentX = 0, _currentY = 0;
    bool _isNavigating = false;
};

#endif
