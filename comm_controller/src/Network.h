#ifndef NETWORK_H
#define NETWORK_H

#include <Arduino.h>
#include <WiFi.h>
#include <HardwareSerial.h>

class Network {
public:
    Network(const char* ssid, const char* password, int rxPin = 16, int txPin = 17);
    void beginWiFi();
    void beginSIM7600();
    
    void sendATCommand(String cmd, int delayTime = 1000);
    bool isWiFiConnected();
    bool isSIMConnected();
    
    void checkConnection(); // Logic to handle fallback
    String getActiveNetwork(); // Returns "WiFi" or "4G"

private:
    const char* _ssid;
    const char* _password;
    int _rxPin;
    int _txPin;
    
    HardwareSerial _sim7600;
};

#endif
