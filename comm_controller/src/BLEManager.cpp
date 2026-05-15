#include "BLEManager.h"

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        Serial.println("[BLE] Device Connected!");
    };

    void onDisconnect(BLEServer* pServer) {
        Serial.println("[BLE] Device Disconnected!");
        BLEDevice::startAdvertising(); // Restart advertising
    }
};

BLEManager::BLEManager() {}

void BLEManager::begin() {
    #if USE_BLE_PROXIMITY
    Serial.println("[BLE] Starting BLE Proximity Server...");
    BLEDevice::init(BT_DEVICE_NAME);
    
    _pServer = BLEDevice::createServer();
    _pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = _pServer->createService(SERVICE_UUID);
    BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_READ |
                                         BLECharacteristic::PROPERTY_WRITE
                                       );

    pCharacteristic->setValue("Omni-Core Nearby");
    pService->start();

    _pAdvertising = BLEDevice::getAdvertising();
    _pAdvertising->addServiceUUID(SERVICE_UUID);
    _pAdvertising->setScanResponse(true);
    _pAdvertising->setMinPreferred(0x06);  
    _pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    Serial.println("[BLE] Advertising active. Ready for proximity sync.");
    #endif
}

void BLEManager::update() {
    #if USE_BLE_PROXIMITY
    if (_pServer->getConnectedCount() > 0) {
        _userNearby = true;
        _lastDetection = millis();
    } else {
        // If no connection for 30 seconds, consider user away
        if (millis() - _lastDetection > 30000) {
            _userNearby = false;
        }
    }
    #endif
}

bool BLEManager::isUserNearby() {
    return _userNearby;
}
