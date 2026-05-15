#include "RobotServer.h"
#include <WiFi.h>

WebInterface::WebInterface(AudioSystem* audio, SurroundControl* surround, Network* net, int port) 
    : _audio(audio), _surround(surround), _net(net), _server(port), _hasNewCommand(false) {}

void WebInterface::begin() {
    _server.on("/", [this]() { handleRoot(); });
    _server.on("/forward", [this]() { handleForward(); });
    _server.on("/backward", [this]() { handleBackward(); });
    _server.on("/left", [this]() { handleLeft(); });
    _server.on("/right", [this]() { handleRight(); });
    _server.on("/left_pivot", [this]() { handleLeftPivot(); });
    _server.on("/right_pivot", [this]() { handleRightPivot(); });
    _server.on("/stop", [this]() { handleStop(); });
    _server.on("/status", [this]() { handleStatus(); });
    _server.on("/transform", [this]() { handleTransform(); });
    _server.on("/walk", [this]() { handleWalk(); });
    _server.on("/auto", [this]() { handleAuto(); });
    _server.on("/test", [this]() { handleTest(); });
    _server.on("/pan", [this]() { handlePan(); });
    _server.on("/tilt", [this]() { handleTilt(); });
    _server.on("/expression", [this]() { handleExpression(); });
    _server.on("/voice", HTTP_POST, std::bind(&WebInterface::handleVoice, this));
    _server.on("/say", HTTP_GET, std::bind(&WebInterface::handleSay, this));
    _server.on("/scan", std::bind(&WebInterface::handleScan, this));
    _server.on("/takeover", [this]() { handleTakeover(); });
    _server.on("/stealth", [this]() { handleStealth(); });
    _server.on("/deauth", [this]() { handleDeauth(); });
    _server.on("/honeypot", [this]() { handleHoneypot(); });
    _server.on("/flash", [this]() { handleFlash(); });
    
    _server.begin();

    _webSocket.begin();
    _webSocket.onEvent([this](uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
        onWebSocketEvent(num, type, payload, length);
    });

    #if USE_AI_BRAIN
    reconnectAiBrain();
    _aiClient.onEvent([this](WStype_t type, uint8_t * payload, size_t length) {
        onAiEvent(type, payload, length);
    });
    #endif

    Serial.println("[SERVER] HTTP & WebSocket servers started");
}

void WebInterface::reconnectAiBrain() {
    #if USE_AI_BRAIN
    _aiClient.disconnect();
    
    // Logic: If on 4G, ALWAYS use Global. If on WiFi, try Local first.
    bool isOnWifi = (WiFi.status() == WL_CONNECTED);
    
    if (!isOnWifi || (_aiConnectAttempts >= 3 && !_isUsingGlobalAi)) {
        Serial.println("[AI-BRAIN] Switching to GLOBAL (ngrok) Link...");
        _aiClient.begin(AI_BRAIN_GLOBAL_HOST, AI_BRAIN_GLOBAL_PORT, "/ws");
        _isUsingGlobalAi = true;
    } else {
        Serial.println("[AI-BRAIN] Attempting LOCAL Link: " + String(AI_BRAIN_LOCAL_HOST));
        _aiClient.begin(AI_BRAIN_LOCAL_HOST, AI_BRAIN_LOCAL_PORT, "/ws");
        _isUsingGlobalAi = false;
    }
    _lastAiRetry = millis();
    #endif
}

void WebInterface::handleClient() {
    _server.handleClient();
    _webSocket.loop();
    #if USE_AI_BRAIN
    _aiClient.loop();
    
    // Auto-reconnect/switch logic
    if (!_aiClient.isConnected() && (millis() - _lastAiRetry > 8000)) {
        _aiConnectAttempts++;
        reconnectAiBrain();
    }
    #endif
}

void WebInterface::onAiEvent(WStype_t type, uint8_t * payload, size_t length) {
    if (type == WStype_CONNECTED) {
        Serial.printf("[AI-BRAIN] Connected via %s link\n", _isUsingGlobalAi ? "GLOBAL" : "LOCAL");
        _aiConnectAttempts = 0; // Reset on success
        String identity = "IDENTITY:{\"name\":\"" + String(ROBOT_NAME) + 
                          "\",\"persona\":\"" + String(ROBOT_PERSONA) + 
                          "\",\"version\":\"" + String(ROBOT_VERSION) + 
                          "\",\"language\":\"" + String(ROBOT_LANGUAGE) + "\"}";
        _aiClient.sendTXT(identity);
    } else if (type == WStype_TEXT) {
        String msg = String((char*)payload);
        Serial.println("[AI-BRAIN] Received: " + msg);
        
        if (msg.startsWith("POS:")) {
            int comma = msg.indexOf(',');
            _robotX = msg.substring(4, comma).toFloat();
            _robotY = msg.substring(comma + 1).toFloat();
        } else {
            // Treat as a command from the brain
            _lastCommand = msg;
            _hasNewCommand = true;
        }
    } else if (type == WStype_BIN) {
        Serial.printf("[AI-BRAIN] Received binary audio: %u bytes\n", length);
        if (_audio) {
            _audio->playRawPCM(payload, length);
        }
    } else if (type == WStype_DISCONNECTED) {
        Serial.println("[AI-BRAIN] Disconnected from AI Backend");
    }
}


void WebInterface::onWebSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
    if (type == WStype_CONNECTED) {
        // Send identity to the new client
        String identity = "IDENTITY:{\"name\":\"" + String(ROBOT_NAME) + 
                          "\",\"persona\":\"" + String(ROBOT_PERSONA) + 
                          "\",\"version\":\"" + String(ROBOT_VERSION) + "\"}";
        _webSocket.sendTXT(num, identity);
        Serial.println("[WS] Sent Identity to client " + String(num));
    }
    else if (type == WStype_TEXT) {
        _lastCommand = String((char*)payload);
        _hasNewCommand = true;
        _webSocket.sendTXT(num, "ACK"); // Acknowledge command
    }
}


void WebInterface::broadcast(String msg) {
    _webSocket.broadcastTXT(msg);
}


String WebInterface::getLastCommand() {
    return _lastCommand;
}

bool WebInterface::hasNewCommand() {
    return _hasNewCommand;
}

void WebInterface::clearCommand() {
    _hasNewCommand = false;
    _lastCommand = "";
}

void WebInterface::handleRoot() {
    _server.send(200, "text/html", getDashboardHTML(_surround));
}







void WebInterface::handleForward() { _lastCommand = "CMD:FORWARD"; _hasNewCommand = true; _server.send(200, "text/plain", "FORWARD"); }
void WebInterface::handleBackward() { _lastCommand = "CMD:BACKWARD"; _hasNewCommand = true; _server.send(200, "text/plain", "BACKWARD"); }
void WebInterface::handleLeft() { _lastCommand = "CMD:LEFT"; _hasNewCommand = true; _server.send(200, "text/plain", "LEFT"); }
void WebInterface::handleRight() { _lastCommand = "CMD:RIGHT"; _hasNewCommand = true; _server.send(200, "text/plain", "RIGHT"); }
void WebInterface::handleLeftPivot() { _lastCommand = "CMD:LEFT_PIVOT"; _hasNewCommand = true; _server.send(200, "text/plain", "PIVOT LEFT"); }
void WebInterface::handleRightPivot() { _lastCommand = "CMD:RIGHT_PIVOT"; _hasNewCommand = true; _server.send(200, "text/plain", "PIVOT RIGHT"); }
void WebInterface::handleStop() { _lastCommand = "CMD:STOP"; _hasNewCommand = true; _server.send(200, "text/plain", "STOPPED"); }
void WebInterface::handleTransform() { _lastCommand = "CMD:TRANSFORM"; _hasNewCommand = true; _server.send(200, "text/plain", "TRANSFORMING"); }
void WebInterface::handleWalk() { _lastCommand = "CMD:WALK"; _hasNewCommand = true; _server.send(200, "text/plain", "WALK MODE"); }
void WebInterface::handleAuto() { _lastCommand = "CMD:AUTO"; _hasNewCommand = true; _server.send(200, "text/plain", "AUTO PILOT"); }
void WebInterface::handleTest() { _lastCommand = "CMD:TEST"; _hasNewCommand = true; _server.send(200, "text/plain", "RUNNING DIAGNOSTICS"); }

void WebInterface::handlePan() {
    if (_server.hasArg("val")) {
        _lastCommand = "PAN:" + _server.arg("val");
        _hasNewCommand = true;
    }
    _server.send(200, "text/plain", "OK");
}

void WebInterface::handleTilt() {
    if (_server.hasArg("val")) {
        _lastCommand = "TILT:" + _server.arg("val");
        _hasNewCommand = true;
    }
    _server.send(200, "text/plain", "OK");
}

void WebInterface::handleExpression() {
    if (_server.hasArg("val")) {
        _lastCommand = "FACE:" + _server.arg("val");
        _hasNewCommand = true;
    }
    _server.send(200, "text/plain", "OK");
}

void WebInterface::handleVoice() {
    if (_server.hasArg("plain")) {
        // Here we would push the binary data to the AudioSystem
        // For now, we'll mark it as a voice command
        _lastCommand = "AUDIO:DATA";
        _hasNewCommand = true;
    }
    _server.send(200, "text/plain", "OK");
}

void WebInterface::handleSay() {
    if (_server.hasArg("text")) {
        String text = _server.arg("text");
        #if USE_AUDIO_SYSTEM
        if (_audio) _audio->speak(text);
        #endif
        _server.send(200, "text/plain", "JARVIS speaking...");
    } else {
        _server.send(400, "text/plain", "Missing text arg");
    }
}

void WebInterface::handleStatus() {
    // We'll show the network type in the response
    String json = "{\"ip\":\"" + WiFi.localIP().toString() + "\",\"rssi\":" + String(WiFi.RSSI()) + ",\"net\":\"" + (WiFi.status() == WL_CONNECTED ? "WiFi" : "4G") + "\"}";
    _server.send(200, "application/json", json);
}

void WebInterface::sendToAi(String msg) {
    #if USE_AI_BRAIN
    if (_aiClient.isConnected()) {
        _aiClient.sendTXT(msg);
    }
    #endif
}

void WebInterface::handleScan() {
    if (_surround) {
        _surround->scanNetwork();
        _surround->startBleScan(5);
    }
    _server.send(200, "text/plain", "SCANNING STARTED");
}

void WebInterface::handleTakeover() {
    if (_server.hasArg("ip")) {
        String ip = _server.arg("ip");
        if (_surround) _surround->controlTasmota(ip, true);
        _server.send(200, "text/plain", "TAKEOVER SENT TO " + ip);
    } else if (_server.hasArg("mac")) {
        String mac = _server.arg("mac");
        if (_surround) _surround->wakeOnLan(mac.c_str());
        _server.send(200, "text/plain", "WOL SENT TO " + mac);
    } else {
        _server.send(400, "text/plain", "MISSING IP/MAC");
    }
}

void WebInterface::handleStealth() {
    static bool stealthOn = false;
    stealthOn = !stealthOn;
    if (_surround) {
        if (stealthOn) _surround->startSniffing();
        else _surround->stopSniffing();
    }
    _server.send(200, "text/plain", stealthOn ? "STEALTH ON" : "STEALTH OFF");
}

void WebInterface::handleDeauth() {
    if (_server.hasArg("mac")) {
        String mac = _server.arg("mac");
        if (_surround) _surround->deauthDevice(mac);
        _server.send(200, "text/plain", "DEAUTH SENT TO " + mac);
    } else {
        _server.send(400, "text/plain", "MISSING MAC");
    }
}

void WebInterface::handleHoneypot() {
    static bool honeyOn = false;
    honeyOn = !honeyOn;
    if (_net) {
        if (honeyOn) _net->startHoneypot("FREE_WIFI_ROBOT");
        else _net->stopHoneypot();
    }
    _server.send(200, "text/plain", honeyOn ? "HONEYPOT ON" : "HONEYPOT OFF");
}

void WebInterface::handleFlash() {
    static bool flashOn = false;
    flashOn = !flashOn;
    
    // 1. Send Command to Vision Controller (Wireless Flash)
    HTTPClient http;
    String camUrl = String(VISION_CAM_URL);
    // Replace '/stream' with '/flash'
    camUrl.replace("/stream", "/flash");
    http.begin(camUrl + "?val=" + String(flashOn ? 1 : 0));
    http.GET();
    http.end();

    // 2. Local State Management
    _lastCommand = String("FLASH:") + (flashOn ? "ON" : "OFF");
    _hasNewCommand = true;
    _server.send(200, "text/plain", flashOn ? "FLASH ON" : "FLASH OFF");
}
