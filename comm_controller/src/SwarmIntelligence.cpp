#include "SwarmIntelligence.h"

SwarmIntelligence::SwarmIntelligence(SwarmLink& swarm, DisplayController* display, WebInterface& web)
    : _swarm(swarm), _display(display), _web(web) {}

void SwarmIntelligence::begin() {
    _swarm.begin(ROBOT_NAME);
}

void SwarmIntelligence::update(int currentMood) {
    if (millis() - _lastSwarmBroadcast > 5000) {
        int batVal = analogRead(34);
        _swarm.broadcast(currentMood, batVal);
        _lastSwarmBroadcast = millis();
    }
    checkSwarmEvents();
}

void SwarmIntelligence::broadcastObstacle(int currentMood, float currentYaw, int dist) {
    if (dist > 0 && dist < 30) {
        float rad = (currentYaw * PI) / 180.0;
        float obsX = _web.getPosX() + dist * cos(rad);
        float obsY = _web.getPosY() + dist * sin(rad);
        
        Serial.printf("[SWARM] Obstacle detected at X:%.1f Y:%.1f\n", obsX, obsY);
        
        SwarmData data;
        data.mood = currentMood;
        data.batteryLevel = 100;
        data.x = _web.getPosX();
        data.y = _web.getPosY();
        data.obsX = obsX;
        data.obsY = obsY;
        data.hasObstacle = true;
        strcpy(data.command, "OBSTACLE_ALERT");
        
        _swarm.broadcast(data); 
    }
}

void SwarmIntelligence::checkSwarmEvents() {
    if (_swarm.hasNewData()) {
        SwarmData other = _swarm.getLastData();
        Serial.print("[SWARM-AI] Received data from: ");
        Serial.println(other.senderName);
        
        #if USE_OLED_DISPLAY
        if (_display && other.mood == 2) { // Other is angry
            _display->heroFace();
            _web.broadcast("STATUS: Fellow robot needs help!");
        }
        #endif

        if (other.hasObstacle) {
            _web.broadcast("ALERT: " + String(other.senderName) + " found obstacle at " + String(other.obsX) + "," + String(other.obsY));
        }
    }
}
