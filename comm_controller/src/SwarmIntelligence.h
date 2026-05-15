#ifndef SWARM_INTELLIGENCE_H
#define SWARM_INTELLIGENCE_H

#include <Arduino.h>
#include "Config.h"
#include "SwarmLink.h"
#include "Display.h"
#include "RobotServer.h"

class SwarmIntelligence {
public:
    SwarmIntelligence(SwarmLink& swarm, DisplayController* display, WebInterface& web);
    
    void begin();
    void update(int currentMood);
    void broadcastObstacle(int currentMood, float currentYaw, int dist);
    void checkSwarmEvents();

private:
    SwarmLink& _swarm;
    DisplayController* _display;
    WebInterface& _web;
    
    unsigned long _lastSwarmBroadcast = 0;
};

#endif
