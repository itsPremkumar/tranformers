#ifndef ROBOT_SYSTEM_H
#define ROBOT_SYSTEM_H

#include <Arduino.h>
#include <Wire.h>
#include "Config.h"
#include "MotorControl.h"
#include "Balance.h"
#include "ObstacleAvoidance.h"
#include "ServoControl.h"

class RobotSystem {
public:
    RobotSystem(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, ServoControl& servos);
    
    void i2cRecovery();
    void runSelfTest();
    void updateTelemetry();
    void checkBatterySafety();

private:
    MotorControl& _car;
    Balance& _balance;
    ObstacleAvoidance& _obstacle;
    ServoControl& _servos;
    
    unsigned long _lastTelemetryUpdate = 0;
    unsigned long _lastBatteryCheck = 0;
    const int TELEMETRY_INTERVAL = 500;
};

#endif
