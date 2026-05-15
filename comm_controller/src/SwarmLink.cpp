#include "SwarmLink.h"

SwarmData SwarmLink::_lastData;
bool SwarmLink::_newData = false;
bool SwarmLink::_lastSendSuccess = true;

SwarmLink::SwarmLink() {}

void SwarmLink::begin(const char* robotName) {
    strncpy(_robotName, robotName, 16);
    
    // ESP-NOW requires WiFi to be in Station mode
    if (esp_now_init() != ESP_OK) {
        Serial.println("Error initializing ESP-NOW");
        return;
    }

    esp_now_register_recv_cb(SwarmLink::onDataReceive);
    esp_now_register_send_cb(SwarmLink::onDataSent); // Register send callback
    
    // Add broadcast peer
    esp_now_peer_info_t peerInfo;
    memset(&peerInfo, 0, sizeof(peerInfo));
    uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    memcpy(peerInfo.peer_addr, broadcastAddress, 6);
    peerInfo.channel = 0;  // Match current WiFi channel
    peerInfo.encrypt = false;
    
    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
        Serial.println("Failed to add broadcast peer");
    }
}

void SwarmLink::broadcast(int mood, int battery, const char* cmd) {
    uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    sendTo(broadcastAddress, mood, battery, cmd);
}

void SwarmLink::broadcast(SwarmData data) {
    uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    sendTo(broadcastAddress, data);
}

void SwarmLink::sendTo(const uint8_t* mac, int mood, int battery, const char* cmd) {
    SwarmData data;
    strncpy(data.senderName, _robotName, 16);
    data.mood = mood;
    data.batteryLevel = battery;
    strncpy(data.command, cmd, 32);
    
    // Default spatial data
    data.x = 0;
    data.y = 0;
    data.obsX = 0;
    data.obsY = 0;
    data.hasObstacle = false;
    
    sendTo(mac, data);
}

void SwarmLink::sendTo(const uint8_t* mac, SwarmData data) {
    esp_now_send(mac, (uint8_t *) &data, sizeof(data));
}

bool SwarmLink::addPeer(const uint8_t* mac) {
    if (esp_now_is_peer_exist(mac)) return true;
    
    esp_now_peer_info_t peerInfo;
    memset(&peerInfo, 0, sizeof(peerInfo));
    memcpy(peerInfo.peer_addr, mac, 6);
    peerInfo.channel = 0; 
    peerInfo.encrypt = false;
    
    return (esp_now_add_peer(&peerInfo) == ESP_OK);
}

void SwarmLink::onDataReceive(const uint8_t * mac, const uint8_t *incomingData, int len) {
    memcpy(&_lastData, incomingData, sizeof(_lastData));
    _newData = true;
    
    Serial.print("[SWARM] Message from: ");
    Serial.println(_lastData.senderName);
}

void SwarmLink::onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
    _lastSendSuccess = (status == ESP_NOW_SEND_SUCCESS);
    if (!_lastSendSuccess) {
        Serial.println("[SWARM] Delivery Failed to Peer");
    }
}
