#include "Connectivity.h"
#include <esp_now.h>

Connectivity::Connectivity(Network& net, WebInterface& web, SurroundControl& surround) 
    : _net(net), _web(web), _surround(surround) {}

void Connectivity::begin() {
    _net.beginWiFi();
    if (_net.isWiFiConnected()) {
        _web.begin();
    }
    _lastAiHeartbeat = millis();
}

void Connectivity::update() {
    _net.update();
    _web.handleClient();
    _surround.update();

    // 1. Connection Healer
    checkConnectionHealer();

    // 2. Periodic Network Check
    if (millis() - _lastNetworkCheck > 10000) {
        _net.checkConnection();
        _lastNetworkCheck = millis();
    }

    // 3. Heartbeat to Motion Controller
    if (millis() - _lastMotionHeartbeat > 1000) {
        Serial2.println("BEAT");
        _lastMotionHeartbeat = millis();
    }

    // 4. Hotspot Sync logic
    static bool hotspotSynced = false;
    if (_net.isHotspotActive() && !hotspotSynced) {
        struct WiFiSync {
            char ssid[32];
            char pass[64];
        };
        WiFiSync sync;
        strncpy(sync.ssid, "Omni-Gateway", 32);
        strncpy(sync.pass, "robot4glink", 64);
        
        uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
        esp_now_send(broadcastAddress, (uint8_t *) &sync, sizeof(WiFiSync));
        Serial.println("[SYNC] Slaves moved to 4G Internal Hotspot.");
        hotspotSynced = true;
    }
}

void Connectivity::reliableSendCommand(String cmd) {
    int retries = 0;
    bool ackReceived = false;
    
    while (retries < 3 && !ackReceived) {
        Serial2.println(cmd);
        unsigned long start = millis();
        
        while (millis() - start < 150) { 
            if (Serial2.available()) {
                String response = Serial2.readStringUntil('\n');
                response.trim();
                if (response == "ACK:" + cmd) {
                    ackReceived = true;
                    break;
                }
            }
        }
        if (!ackReceived) {
            retries++;
            Serial.println("[RETRY] Command failed: " + cmd + " (Attempt " + String(retries) + ")");
        }
    }
}

void Connectivity::checkConnectionHealer() {
    if (_web.hasNewCommand()) {
        _lastAiHeartbeat = millis();
    }
    
    if (_net.isWiFiConnected() && (millis() - _lastAiHeartbeat > 45000)) {
        Serial.println("[HEAL] Connection Zombie detected. Re-initializing Network...");
        _net.beginWiFi();
        _lastAiHeartbeat = millis();
    }
}
