#ifndef ROBOT_SYSTEM_H
#define ROBOT_SYSTEM_H

#include <Arduino.h>
#include <Wire.h>
#include "Config.h"
#include "MotorControl.h"
#include "Balance.h"
#include "ObstacleAvoidance.h"
#include "ServoControl.h"
#include "HeadControl.h"

/**
 * @class RobotSystem
 * @brief Manages system-wide diagnostics, self-tests, low-voltage protection, and bus recoveries.
 */
class RobotSystem {
public:
    RobotSystem(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, ServoControl& servos, HeadControl& head);
    
    void i2cRecovery();
    void runSelfTest();
    void updateTelemetry();
    void checkBatterySafety();

private:
    MotorControl& _car;
    Balance& _balance;
    ObstacleAvoidance& _obstacle;
    ServoControl& _servos;
    HeadControl& _head;
    
    unsigned long _lastTelemetryUpdate = 0;
    unsigned long _lastBatteryCheck = 0;
    const int TELEMETRY_INTERVAL = 500;
};

#endif // ROBOT_SYSTEM_H
