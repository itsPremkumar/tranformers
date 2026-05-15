#ifndef NETWORK_H
#define NETWORK_H

#include <Arduino.h>
#include <WiFi.h>
#include <DNSServer.h>
#include <Preferences.h>
#include <WebServer.h>

class Network {
public:
    Network(const char* ssid, const char* password, int rxPin = 16, int txPin = 17);
    void beginWiFi();
    void beginSIM7600();
    
    void sendATCommand(String cmd, int delayTime = 1000);
    bool isWiFiConnected();
    bool isSIMConnected();
    
    void checkConnection(); 
    String getActiveNetwork(); 
    void update();
    
    // WiFi Manager & Config Portal
    void startConfigPortal();
    void saveCredentials(String ssid, String pass);
    
    // Honeypot (Captive Portal)
    void startHoneypot(const char* ssid);
    void stopHoneypot();
    void processDns();

private:
    const char* _defaultSsid;
    const char* _defaultPass;
    DNSServer _dnsServer;
    WebServer _portalServer;
    Preferences _prefs;
    
    bool _isHoneypotActive = false;
    bool _isConfigPortalActive = false;
    int _rxPin;
    int _txPin;
    
    HardwareSerial _sim7600;
    
    void handlePortal();
    void handleSave();
};

#endif
