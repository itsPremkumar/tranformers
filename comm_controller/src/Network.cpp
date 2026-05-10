#include "Network.h"

Network::Network(const char* ssid, const char* password, int rxPin, int txPin) 
    : _ssid(ssid), _password(password), _rxPin(rxPin), _txPin(txPin), _sim7600(2) {
}

void Network::beginWiFi() {
    Serial.println("[WIFI] Connecting...");
    WiFi.mode(WIFI_STA);
    WiFi.begin(_ssid, _password);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("[WIFI] Connected successfully");
        Serial.println("[WIFI] IP: " + WiFi.localIP().toString());
    } else {
        Serial.println("[ERROR] WiFi connection failed");
    }
}

void Network::beginSIM7600() {
    _sim7600.begin(115200, SERIAL_8N1, _rxPin, _txPin);
    delay(3000);
    Serial.println("Initializing SIM7600...");
    
    sendATCommand("AT");
    sendATCommand("AT+CPIN?");
    sendATCommand("AT+CSQ");
    sendATCommand("AT+CREG?");
    sendATCommand("AT+CGDCONT=1,\"IP\",\"internet\"");
    sendATCommand("AT+CGACT=1,1");
}

void Network::sendATCommand(String cmd, int delayTime) {
    _sim7600.println(cmd);
    delay(delayTime);
    
    while (_sim7600.available()) {
        Serial.write(_sim7600.read());
    }
}

bool Network::isWiFiConnected() {
    return WiFi.status() == WL_CONNECTED;
}

bool Network::isSIMConnected() {
    // Basic check for SIM7600 readiness
    return true; // Simplify for now, logic would involve AT commands
}

void Network::checkConnection() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[NETWORK] WiFi Lost. Checking 4G Fallback...");
        // In a real scenario, you'd trigger SIM7600 data connection here
        // For now, we log and keep the system alive
    }
}

String Network::getActiveNetwork() {
    if (WiFi.status() == WL_CONNECTED) return "WiFi";
    return "4G LTE";
}
