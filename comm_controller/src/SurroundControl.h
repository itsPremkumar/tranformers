#ifndef SURROUND_CONTROL_H
#define SURROUND_CONTROL_H

#include <Arduino.h>
#include "Config.h"
#include <WiFi.h>
#include <ESPmDNS.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <WiFiUdp.h>
#include <HTTPClient.h>
#include <esp_wifi.h>

struct ScannedDevice {
    String name;
    String ip;
    String mac;
    int rssi;
    int battery; 
    bool isBle;
    bool isSniffed; 
};

class SurroundControl : public BLEAdvertisedDeviceCallbacks {
public:
    SurroundControl();
    void begin();
    void update();
    
    // WiFi Discovery
    void scanNetwork();
    void wakeOnLan(const char* macStr);
    
    // BLE Discovery
    void startBleScan(int duration = 5);
    void onResult(BLEAdvertisedDevice advertisedDevice) override;
    
    // WiFi Sniffing (Promiscuous Mode)
    void startSniffing();
    void stopSniffing();
    static void onWiFiPacket(void* buf, wifi_promiscuous_pkt_type_t type);
    
    // Security & Auditing
    void deauthDevice(String mac);
    void injectPacket(uint8_t* buf, int len);
    
    // Interaction & HID
    void startAirMouse();
    void sendMouseMove(int8_t x, int8_t y);
    
    // Intelligence & Positioning
    void logRssiFingerprint(String roomName);
    
    // Takeover Actions
    void controlTasmota(String ip, bool power);
    
    // Discovery & Auto-Config
    void discoverRobotParts();
    String getVisionURL();
    
    int getDeviceCount() { return _deviceCount; }
    ScannedDevice getDevice(int index);

private:
    ScannedDevice _devices[20];
    int _deviceCount = 0;
    BLEScan* _pBLEScan;
    unsigned long _lastScanTime = 0;
    
    String _visionIP = "";
    
    void addDevice(String name, String ip, String mac, int rssi, bool isBle);
};

#endif
