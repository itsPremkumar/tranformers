#ifndef COMMAND_HANDLER_H
#define COMMAND_HANDLER_H

#include <Arduino.h>
#include "Config.h"
#include "MotorControl.h"
#include "Balance.h"
#include "ObstacleAvoidance.h"
#include "ServoControl.h"
#include "Navigation.h"
#include "RobotSystem.h"
#include "HeadControl.h"

// Forward declarations of mode-specific controllers
class CarModeController;
class BipedModeController;
class CrawlerModeController;
class TransformManager;

enum RobotState {
    STATE_STAND,
    STATE_WALK,
    STATE_CAR,
    STATE_AVOID,
    STATE_AVOID_ADVANCED,
    STATE_FALLEN,
    STATE_CRAWLER,
    STATE_SUN_SEEK
};

/**
 * @class CommandHandler
 * @brief Parses commands and routes them to the correct active operational mode controller.
 */
class CommandHandler {
public:
    CommandHandler(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, 
                  ServoControl& servos, Navigation& nav, RobotSystem& system, HeadControl& head,
                  CarModeController& carMode, BipedModeController& bipedMode,
                  CrawlerModeController& crawlerMode, TransformManager& transform);
    
    void processCommand(String cmd);
    void updateState();
    
    RobotState getState() const { return _currentState; }
    void setState(RobotState s) { _currentState = s; }
    bool isMovingForward() const { return _isMovingForward; }
    bool isTurning() const { return _isTurning; }

private:
    MotorControl& _car;
    Balance& _balance;
    ObstacleAvoidance& _obstacle;
    ServoControl& _servos;
    Navigation& _nav;
    RobotSystem& _system;
    HeadControl& _head;
    
    CarModeController& _carMode;
    BipedModeController& _bipedMode;
    CrawlerModeController& _crawlerMode;
    TransformManager& _transform;
    
    RobotState _currentState = STATE_STAND;
    bool _isMovingForward = false;
    bool _isTurning = false;
    bool _isAidingGyro = false;
    float _targetYaw = 0;
    unsigned long _lastHeartbeatReceived = 0;
};

#endif // COMMAND_HANDLER_H
