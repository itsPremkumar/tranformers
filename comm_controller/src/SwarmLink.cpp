#include "SwarmLink.h"

SwarmData SwarmLink::_lastData;
bool SwarmLink::_newData = false;

SwarmLink::SwarmLink() {}

void SwarmLink::begin(const char* robotName) {
    strncpy(_robotName, robotName, 16);
    
    // ESP-NOW requires WiFi to be in Station mode
    if (esp_now_init() != ESP_OK) {
        Serial.println("Error initializing ESP-NOW");
        return;
    }

    esp_now_register_recv_cb(SwarmLink::onDataReceive);
    
    // Add broadcast peer
    esp_now_peer_info_t peerInfo;
    memset(&peerInfo, 0, sizeof(peerInfo));
    uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    memcpy(peerInfo.peer_addr, broadcastAddress, 6);
    peerInfo.channel = 0;  
    peerInfo.encrypt = false;
    
    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
        Serial.println("Failed to add broadcast peer");
    }
}

void SwarmLink::broadcast(int mood, int battery, const char* cmd) {
    SwarmData data;
    strncpy(data.senderName, _robotName, 16);
    data.mood = mood;
    data.batteryLevel = battery;
    strncpy(data.command, cmd, 32);
    
    uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    esp_now_send(broadcastAddress, (uint8_t *) &data, sizeof(data));
}

void SwarmLink::onDataReceive(const uint8_t * mac, const uint8_t *incomingData, int len) {
    memcpy(&_lastData, incomingData, sizeof(_lastData));
    _newData = true;
    
    Serial.print("[SWARM] Message from: ");
    Serial.println(_lastData.senderName);
}
