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
};

class SwarmLink {
public:
    SwarmLink();
    void begin(const char* robotName);
    void broadcast(int mood, int battery, const char* cmd = "");
    
    // Callback for when data is received
    static void onDataReceive(const uint8_t * mac, const uint8_t *incomingData, int len);
    
    bool hasNewData() { return _newData; }
    SwarmData getLastData() { _newData = false; return _lastData; }

private:
    static SwarmData _lastData;
    static bool _newData;
    char _robotName[16];
};

#endif
