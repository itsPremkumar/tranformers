#ifndef BLE_MANAGER_H
#define BLE_MANAGER_H

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include "Config.h"

class BLEManager {
public:
    BLEManager();
    void begin();
    void update();
    bool isUserNearby();

private:
    bool _userNearby = false;
    unsigned long _lastDetection = 0;
    BLEServer* _pServer;
    BLEAdvertising* _pAdvertising;
};

#endif
