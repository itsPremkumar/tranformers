#ifndef SURROUND_CONTROL_H
#define SURROUND_CONTROL_H

#include <Arduino.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <WiFiUdp.h>
#include <HTTPClient.h>

struct ScannedDevice {
    String name;
    String ip;
    String mac;
    int rssi;
    bool isBle;
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
    
    // Takeover Actions
    void controlTasmota(String ip, bool power);
    void controlSamsungTV(String ip, String command);
    
    int getDeviceCount() { return _deviceCount; }
    ScannedDevice getDevice(int index);

private:
    ScannedDevice _devices[20];
    int _deviceCount = 0;
    BLEScan* _pBLEScan;
    unsigned long _lastScanTime = 0;
    
    void addDevice(String name, String ip, String mac, int rssi, bool isBle);
};

#endif
