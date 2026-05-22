#include "Network.h"
#include <ESPmDNS.h>
#include <esp_wifi.h>
#include "Config.h"
#include <esp_task_wdt.h>

Network::Network(const char* ssid, const char* password, int rxPin, int txPin) 
    : _defaultSsid(ssid), _defaultPass(password), _rxPin(rxPin), _txPin(txPin), _sim7600(2), _portalServer(8080) {
}

void Network::beginWiFi() {
    _prefs.begin("wifi", false);
    String savedSsid = _prefs.getString("ssid", _defaultSsid);
    String savedPass = _prefs.getString("pass", _defaultPass);
    
    Serial.println("[WIFI] Starting AP_STA Mode...");
    WiFi.mode(WIFI_AP_STA);
    
    Serial.println("[WIFI] Connecting to: " + savedSsid);
    
    #if USE_WIFI_LR
    beginLongRange();
    #endif

    WiFi.begin(savedSsid.c_str(), savedPass.c_str());

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) { // 10 seconds
        esp_task_wdt_reset();
        delay(500);
        Serial.print(".");
        attempts++;
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("[WIFI] Connected successfully");
        Serial.println("[WIFI] STA IP: " + WiFi.localIP().toString());
        
        // Start Access Point after connection is established
        // so it inherits the correct channel of the router.
        bool result = WiFi.softAP(AP_SSID, AP_PASS);
        if (result) {
            Serial.println("[SUCCESS] Hotspot Started");
            _isHotspotActive = true;
        } else {
            Serial.println("[ERROR] Hotspot Failed");
        }
        
        #if USE_MDNS
        setupMDNS();
        #endif
    } else {
        Serial.println("[WIFI] Station Mode: Connection failed or timed out.");
        Serial.println("[WIFI] Continuing with Access Point active.");
        WiFi.disconnect();
        
        // Start Access Point
        bool result = WiFi.softAP(AP_SSID, AP_PASS);
        if (result) {
            Serial.println("[SUCCESS] Hotspot Started");
            _isHotspotActive = true;
        } else {
            Serial.println("[ERROR] Hotspot Failed");
        }
    }
    
    if (_isHotspotActive) {
        // Force standard protocols on AP interface so phones can see it
        esp_wifi_set_protocol(WIFI_IF_AP, WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N);
        
        IPAddress IP = WiFi.softAPIP();
        Serial.println("---------------------------------");
        Serial.print("SSID     : ");
        Serial.println(AP_SSID);
        Serial.print("Password : ");
        Serial.println(AP_PASS);
        Serial.print("AP IP    : ");
        Serial.println(IP);
        Serial.printf("AP Channel: %d\n", WiFi.channel());
        Serial.println("---------------------------------");
    }
}

void Network::setupMDNS() {
    if (!MDNS.begin("omni")) {
        Serial.println("[MDNS] Error setting up MDNS responder!");
        return;
    }
    Serial.println("[MDNS] Responder started: http://omni.local");
    MDNS.addService("http", "tcp", 80);
}

void Network::beginLongRange() {
    Serial.println("[WIFI] Enabling 802.11 Long Range Mode...");
    esp_wifi_set_protocol(WIFI_IF_STA, WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N | WIFI_PROTOCOL_LR);
}

// Sniffer Callback
void sniffer_callback(void* buf, wifi_promiscuous_pkt_type_t type) {
    if (type != WIFI_PKT_MGMT) return;
    wifi_promiscuous_pkt_t* pkt = (wifi_promiscuous_pkt_t*)buf;
    int rssi = pkt->rx_ctrl.rssi;
    // Basic detection: log high-strength signals from unknown devices
    if (rssi > -50) {
        Serial.printf("[SNIFFER] Strong management packet detected! RSSI: %d\n", rssi);
    }
}

void Network::startSniffer() {
    if (_isHotspotActive) {
        Serial.println("[SNIFFER] Cannot start sniffer while AP Hotspot is active!");
        return;
    }
    Serial.println("[SNIFFER] Starting Network Audit Sniffer...");
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
    _isSnifferActive = true;
}

void Network::stopSniffer() {
    esp_wifi_set_promiscuous(false);
    _isSnifferActive = false;
    Serial.println("[SNIFFER] Sniffer disabled.");
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
    // Only run checkConnection on a timer, not every loop iteration
    static unsigned long lastUpdate = 0;
    if (millis() - lastUpdate > 15000) {
        checkConnection();
        lastUpdate = millis();
    }
    if (_isHoneypotActive || _isConfigPortalActive) processDns();
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
    WiFi.softAP(AP_SSID, AP_PASS); // Keep direct Remote-car AP configuration
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
