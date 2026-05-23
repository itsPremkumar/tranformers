#ifndef DIAGNOSTIC_SERVER_H
#define DIAGNOSTIC_SERVER_H

#include <Arduino.h>
#include <WebServer.h>
#include "MotorControl.h"
#include "CommandHandler.h"
#include "ObstacleAvoidance.h"
#include "Balance.h"

/**
 * @class DiagnosticServer
 * @brief Standalone Web Server hosted directly on the Motion Controller for direct hardware bring-up and testing.
 */
class DiagnosticServer {
public:
    DiagnosticServer(MotorControl& car, CommandHandler& cmdHandler, ObstacleAvoidance& obstacle, Balance& balance);
    void begin();
    void update();

private:
    WebServer _server;
    MotorControl& _car;
    CommandHandler& _cmdHandler;
    ObstacleAvoidance& _obstacle;
    Balance& _balance;

    void handleRoot();
    void handleCommand();
    void handleStatus();
};

#endif // DIAGNOSTIC_SERVER_H
