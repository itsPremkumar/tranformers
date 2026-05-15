#ifndef SWARMLINK_H
#define SWARMLINK_H

#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>

struct SwarmData {
    char senderName[16];
    int mood;
    int batteryLevel;
    char command[32];
    
    // NEW: Shared Spatial Intelligence
    float x;             // Robot's current X (from Odometry)
    float y;             // Robot's current Y
    float obsX;          // Detected obstacle X
    float obsY;          // Detected obstacle Y
    bool hasObstacle;    // Flag to alert other robots
};

class SwarmLink {
public:
    SwarmLink();
    void begin(const char* robotName);
    void broadcast(int mood, int battery, const char* cmd = "");
    void broadcast(SwarmData data);
    
    // NEW: Send to a specific robot (Unicast) with reliability
    void sendTo(const uint8_t* mac, int mood, int battery, const char* cmd = "");
    void sendTo(const uint8_t* mac, SwarmData data);
    bool addPeer(const uint8_t* mac);
    
    // Callbacks
    static void onDataReceive(const uint8_t * mac, const uint8_t *incomingData, int len);
    static void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status);
    
    bool hasNewData() { return _newData; }
    SwarmData getLastData() { _newData = false; return _lastData; }
    
    // NEW: Check if the last direct message was successful
    bool isLastMessageDelivered() { return _lastSendSuccess; }

private:
    static SwarmData _lastData;
    static bool _newData;
    static bool _lastSendSuccess;
    char _robotName[16];
};

#endif
