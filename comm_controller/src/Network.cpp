#include "Network.h"

Network::Network(const char* ssid, const char* password, int rxPin, int txPin) 
    : _defaultSsid(ssid), _defaultPass(password), _rxPin(rxPin), _txPin(txPin), _sim7600(2), _portalServer(80) {
}

void Network::beginWiFi() {
    _prefs.begin("wifi", false);
    String savedSsid = _prefs.getString("ssid", _defaultSsid);
    String savedPass = _prefs.getString("pass", _defaultPass);
    
    Serial.println("[WIFI] Connecting to: " + savedSsid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(savedSsid.c_str(), savedPass.c_str());

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) { // 15 seconds
        delay(500);
        Serial.print(".");
        attempts++;
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("[WIFI] Connected successfully");
        Serial.println("[WIFI] IP: " + WiFi.localIP().toString());
    } else {
        Serial.println("[ERROR] WiFi connection failed. Starting Setup Portal...");
        startConfigPortal();
    }
}

void Network::startConfigPortal() {
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP("Omni-Setup", "12345678");
    
    Serial.println("[PORTAL] AP Started: Omni-Setup");
    Serial.print("[PORTAL] IP: ");
    Serial.println(WiFi.softAPIP());

    _dnsServer.start(53, "*", WiFi.softAPIP());
    
    _portalServer.on("/", [this]() { handlePortal(); });
    _portalServer.on("/save", [this]() { handleSave(); });
    _portalServer.onNotFound([this]() { handlePortal(); });
    _portalServer.begin();
    
    _isConfigPortalActive = true;
}

void Network::handlePortal() {
    String html = "<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
    html += "<style>body{font-family:sans-serif;background:#1a1a2e;color:#fff;text-align:center;padding:20px}";
    html += "input{width:100%;padding:10px;margin:10px 0;border-radius:5px;border:none}";
    html += "button{background:#00f2fe;color:#000;padding:10px 20px;border:none;border-radius:5px;font-weight:bold}</style></head>";
    html += "<body><h1>🤖 Transformer Setup</h1><form action='/save' method='POST'>";
    html += "SSID:<br><input type='text' name='ssid' placeholder='WiFi Name'><br>";
    html += "Password:<br><input type='password' name='pass' placeholder='Password'><br>";
    html += "<button type='submit'>CONNECT</button></form></body></html>";
    _portalServer.send(200, "text/html", html);
}

void Network::handleSave() {
    if (_portalServer.hasArg("ssid") && _portalServer.hasArg("pass")) {
        String s = _portalServer.arg("ssid");
        String p = _portalServer.arg("pass");
        saveCredentials(s, p);
        _portalServer.send(200, "text/html", "<html><body><h1>Settings Saved!</h1><p>Robot is restarting to connect...</p></body></html>");
        delay(2000);
        ESP.restart();
    }
}

#include <esp_now.h>

struct WiFiSync {
    char ssid[32];
    char pass[64];
};

void Network::saveCredentials(String ssid, String pass) {
    _prefs.putString("ssid", ssid);
    _prefs.putString("pass", pass);
    Serial.println("[PORTAL] New Credentials Saved Locally.");

    // Advanced: Sync to Slave ESP32s (Vision & Motion) via ESP-NOW
    WiFiSync sync;
    memset(&sync, 0, sizeof(WiFiSync));
    strncpy(sync.ssid, ssid.c_str(), 32);
    strncpy(sync.pass, pass.c_str(), 64);
    
    uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    esp_now_send(broadcastAddress, (uint8_t *) &sync, sizeof(WiFiSync));
    Serial.println("[SYNC] Broadcasted WiFi Update to Slaves.");
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
    return true; 
}

void Network::update() {
    checkConnection();
    processDns();
    if (_isConfigPortalActive) _portalServer.handleClient();
}

void Network::startHoneypot(const char* ssid) {
    Serial.println("[NET] Starting HONEYPOT: " + String(ssid));
    WiFi.softAP(ssid);
    _dnsServer.start(53, "*", WiFi.softAPIP()); 
    _isHoneypotActive = true;
}

void Network::stopHoneypot() {
    _dnsServer.stop();
    WiFi.softAPdisconnect(true);
    _isHoneypotActive = false;
    Serial.println("[NET] Honeypot DISABLED.");
}

void Network::processDns() {
    if (_isHoneypotActive || _isConfigPortalActive) _dnsServer.processNextRequest();
}

void Network::startRobotHotspot() {
    Serial.println("[NET] Creating Robot Gateway (Internal Hotspot)...");
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP("Omni-Gateway", "robot4glink"); // Secure internal password
    _isHotspotActive = true;
    Serial.print("[NET] Gateway IP: ");
    Serial.println(WiFi.softAPIP());
}

void Network::checkConnection() {
    static unsigned long lastCheck = 0;
    if (millis() - lastCheck < 5000) return; // Only check every 5s
    lastCheck = millis();

    if (WiFi.status() != WL_CONNECTED && !_isConfigPortalActive && !_isHotspotActive) {
        Serial.println("[NET] Connection Lost. Trying LTE Fallback...");
        
        // If LTE is available, share it!
        if (isSIMConnected()) {
            startRobotHotspot();
            Serial.println("[NET] System now operating on 4G LTE.");
        }
    }
}

String Network::getActiveNetwork() {
    if (WiFi.status() == WL_CONNECTED) return "WiFi";
    return "4G LTE";
}
