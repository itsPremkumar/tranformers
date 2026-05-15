#ifndef CONNECTIVITY_H
#define CONNECTIVITY_H

#include <Arduino.h>
#include <ArduinoOTA.h>
#include "Config.h"
#include "Network.h"
#include "RobotServer.h"
#include "SurroundControl.h"

class Connectivity {
public:
    Connectivity(Network& net, WebInterface& web, SurroundControl& surround);
    
    void begin();
    void update();
    void reliableSendCommand(String cmd);
    void checkConnectionHealer();
    
    bool isWiFiConnected() { return _net.isWiFiConnected(); }

private:
    Network& _net;
    WebInterface& _web;
    SurroundControl& _surround;
    
    unsigned long _lastAiHeartbeat = 0;
    unsigned long _lastNetworkCheck = 0;
    unsigned long _lastMotionHeartbeat = 0;
};

#endif
