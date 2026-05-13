#include "SurroundControl.h"

SurroundControl::SurroundControl() : _deviceCount(0) {}

void SurroundControl::begin() {
    // Initialize BLE
    BLEDevice::init("OMNI-SCANNER");
    _pBLEScan = BLEDevice::getScan();
    _pBLEScan->setAdvertisedDeviceCallbacks(this);
    _pBLEScan->setActiveScan(true);
    _pBLEScan->setInterval(100);
    _pBLEScan->setWindow(99);
}

void SurroundControl::update() {
    // Periodic Auto-Scan every 60 seconds
    if (millis() - _lastScanTime > 60000) {
        scanNetwork();
        startBleScan(2);
        _lastScanTime = millis();
    }
}

void SurroundControl::scanNetwork() {
    Serial.println("[SURROUND] Scanning WiFi for services...");
    int n = MDNS.queryService("http", "tcp");
    if (n == 0) {
        Serial.println("[SURROUND] No HTTP services found via mDNS.");
    } else {
        for (int i = 0; i < n; ++i) {
            addDevice(MDNS.hostname(i), MDNS.IP(i).toString(), "", MDNS.port(i), false);
        }
    }
}

void SurroundControl::startBleScan(int duration) {
    Serial.println("[SURROUND] Starting BLE Scan...");
    _pBLEScan->start(duration, false);
}

void SurroundControl::onResult(BLEAdvertisedDevice advertisedDevice) {
    String name = advertisedDevice.getName().c_str();
    if (name.length() == 0) name = "Unknown BLE";
    addDevice(name, "", advertisedDevice.getAddress().toString().c_str(), advertisedDevice.getRSSI(), true);
}

void SurroundControl::addDevice(String name, String ip, String mac, int rssi, bool isBle) {
    // Check if exists
    for (int i = 0; i < _deviceCount; i++) {
        if (isBle && _devices[i].mac == mac) {
            _devices[i].rssi = rssi;
            return;
        }
        if (!isBle && _devices[i].ip == ip) return;
    }

    if (_deviceCount < 20) {
        _devices[_deviceCount] = {name, ip, mac, rssi, isBle};
        _deviceCount++;
        Serial.printf("[SURROUND] Captured: %s (%s)\n", name.c_str(), isBle ? "BLE" : "WiFi");
    }
}

void SurroundControl::wakeOnLan(const char* macStr) {
    WiFiUDP udp;
    uint8_t mac[6];
    sscanf(macStr, "%x:%x:%x:%x:%x:%x", &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5]);
    
    uint8_t packet[102];
    memset(packet, 0xFF, 6);
    for (int i = 1; i <= 16; i++) {
        memcpy(&packet[i * 6], mac, 6);
    }
    
    udp.beginPacket(IPAddress(255, 255, 255, 255), 9);
    udp.write(packet, 102);
    udp.endPacket();
    Serial.printf("[SURROUND] WOL Sent to %s\n", macStr);
}

void SurroundControl::controlTasmota(String ip, bool power) {
    HTTPClient http;
    String url = "http://" + ip + "/cm?cmnd=Power%20" + (power ? "ON" : "OFF");
    http.begin(url);
    int httpCode = http.GET();
    http.end();
    Serial.printf("[SURROUND] Tasmota %s -> %d\n", ip.c_str(), httpCode);
}

ScannedDevice SurroundControl::getDevice(int index) {
    if (index < _deviceCount) return _devices[index];
    return {"", "", "", 0, false};
}
