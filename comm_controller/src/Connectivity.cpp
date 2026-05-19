#include "Connectivity.h"
#include <esp_now.h>

Connectivity::Connectivity(Network& net, WebInterface& web, SurroundControl& surround, BLEManager& ble) 
    : _net(net), _web(web), _surround(surround), _ble(ble) {}

void Connectivity::begin() {
    _net.beginWiFi();
    _web.begin();
    _ble.begin();
    _lastAiHeartbeat = millis();
}

void Connectivity::update() {
    _net.update();
    _web.handleClient();
    _surround.update();
    _ble.update();

    // Toggle sniffer based on nearby users or commands
    #if USE_NET_SNIFFER
    if (!_net.isHotspotActive() && !_ble.isUserNearby() && !_net.isSnifferActive()) {
        _net.startSniffer();
    } else if ((_net.isHotspotActive() || _ble.isUserNearby()) && _net.isSnifferActive()) {
        _net.stopSniffer();
    }
    #endif

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
        strncpy(sync.ssid, AP_SSID, 32);
        strncpy(sync.pass, AP_PASS, 64);
        
        uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
        esp_now_send(broadcastAddress, (uint8_t *) &sync, sizeof(WiFiSync));
        Serial.println("[SYNC] Slaves moved to Remote-car Hotspot.");
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
    
    // Only heal if WiFi is connected AND AI brain is enabled AND we haven't received
    // any commands in a very long time. Don't restart WiFi - just reconnect AI.
    #if USE_AI_BRAIN
    if (_net.isWiFiConnected() && (millis() - _lastAiHeartbeat > 120000)) {
        Serial.println("[HEAL] AI connection stale. Requesting reconnect...");
        _web.sendToAi("CMD:HEARTBEAT");
        _lastAiHeartbeat = millis();
    }
    #endif
}
