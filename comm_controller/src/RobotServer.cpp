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
    _server.on("/voice", HTTP_POST, [this]() { handleVoice(); });
    _server.on("/scan", [this]() { handleScan(); });
    _server.on("/takeover", [this]() { handleTakeover(); });
    _server.on("/stealth", [this]() { handleStealth(); });
    _server.on("/deauth", [this]() { handleDeauth(); });
    _server.on("/honeypot", [this]() { handleHoneypot(); });
    
    _server.begin();

    _webSocket.begin();
    _webSocket.onEvent([this](uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
        onWebSocketEvent(num, type, payload, length);
    });

    #if USE_AI_BRAIN
    _aiClient.begin(AI_BRAIN_HOST, AI_BRAIN_PORT, "/ws");
    _aiClient.onEvent([this](WStype_t type, uint8_t * payload, size_t length) {
        onAiEvent(type, payload, length);
    });
    _aiClient.setReconnectInterval(5000);
    #endif

    Serial.println("[SERVER] HTTP & WebSocket servers started");
}

void WebInterface::handleClient() {
    _server.handleClient();
    _webSocket.loop();
    #if USE_AI_BRAIN
    _aiClient.loop();
    #endif
}

void WebInterface::onAiEvent(WStype_t type, uint8_t * payload, size_t length) {
    if (type == WStype_CONNECTED) {
        Serial.println("[AI-BRAIN] Connected to AI Backend");
        // Send identity to the AI Brain immediately
        String identity = "IDENTITY:{\"name\":\"" + String(ROBOT_NAME) + 
                          "\",\"persona\":\"" + String(ROBOT_PERSONA) + 
                          "\",\"version\":\"" + String(ROBOT_VERSION) + 
                          "\",\"language\":\"" + String(ROBOT_LANGUAGE) + "\"}";
        _aiClient.sendTXT(identity);
    } else if (type == WStype_TEXT) {
        String msg = String((char*)payload);
        Serial.println("[AI-BRAIN] Received: " + msg);
        
        // Treat as a command from the brain
        _lastCommand = msg;
        _hasNewCommand = true;
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

String WebInterface::getHTML() {
    String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1,user-scalable=no'>";
    html += "<meta charset='UTF-8'><title>Transformer Control Center</title>";
    html += "<style>";
    html += "*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',Roboto,sans-serif;background:#0f0c29;background:linear-gradient(to right,#24243e,#302b63,#0f0c29);color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}";
    html += ".container{width:100%;max-width:500px}.header{text-align:center;margin-bottom:20px}h1{font-size:1.8em;letter-spacing:2px;text-transform:uppercase;color:#00f2fe;text-shadow:0 0 10px rgba(0,242,254,0.5)}";
    html += ".card{background:rgba(255,255,255,0.05);backdrop-filter:blur(15px);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:20px;margin-bottom:15px;box-shadow:0 8px 32px 0 rgba(0,0,0,0.37);overflow:hidden}";
    html += ".video-container{position:relative;width:100%;border-radius:15px;overflow:hidden;border:2px solid #00f2fe;box-shadow:0 0 20px rgba(0,242,254,0.3);margin-bottom:15px}";
    html += ".video-container img{width:100%;display:block;transition:0.3s}";
    html += ".video-overlay{position:absolute;top:10px;left:10px;background:rgba(0,0,0,0.6);padding:2px 10px;border-radius:10px;font-size:0.6em;color:#00f2fe;border:1px solid #00f2fe;text-transform:uppercase;letter-spacing:1px}";
    html += ".status-bar{display:flex;justify-content:space-between;font-size:0.9em;color:#00f2fe;margin-bottom:10px}";
    html += ".grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;justify-items:center}";
    html += ".btn{width:100%;aspect-ratio:1/1;max-width:100px;border-radius:15px;border:none;color:#fff;font-weight:bold;cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;transition:0.2s;box-shadow:0 4px 15px rgba(0,0,0,0.3)}";
    html += ".btn:active{transform:scale(0.95);box-shadow:0 2px 5px rgba(0,0,0,0.5)}";
    html += ".btn-move{background:linear-gradient(45deg,#2193b0,#6dd5ed)}.btn-action{background:linear-gradient(45deg,#ff00cc,#3333ff)}.btn-stop{background:linear-gradient(45deg,#ed213a,#93291e)}.btn-mood{background:linear-gradient(45deg,#11998e,#38ef7d)}";
    html += ".icon{font-size:1.8em;margin-bottom:5px}.label{font-size:0.7em;text-transform:uppercase}";
    html += ".slider-container{margin-top:10px}.slider{width:100%;height:10px;border-radius:5px;background:#2c3e50;outline:none;appearance:none;margin:10px 0}.slider::-webkit-slider-thumb{appearance:none;width:20px;height:20px;border-radius:50%;background:#00f2fe;cursor:pointer;box-shadow:0 0 10px #00f2fe}";
    html += ".section-title{font-size:0.8em;color:rgba(255,255,255,0.5);margin-bottom:10px;text-transform:uppercase;letter-spacing:1px}";
    html += "</style></head><body>";
    html += "<div class='container'><div class='header'><h1>Transformer 🤖</h1></div>";
    
    html += "<div class='video-container'>";
    html += "  <div class='video-overlay'>● LIVE FPV</div>";
    html += "  <img src='" + String(VISION_CAM_URL) + "' onerror=\"this.src='https://via.placeholder.com/400x300?text=Camera+Offline'\" />";
    html += "</div>";

    html += "<div class='card'><div class='status-bar'><span>IP: " + WiFi.localIP().toString() + "</span><span id='status'>READY</span></div></div>";
    
    html += "<div class='card'><div class='section-title' style='display:flex;justify-content:space-between;align-items:center'>";
    html += "<span>Movement Control</span>";
    html += "<select id='mode' style='background:#1a1a2e;color:#00f2fe;border:1px solid #00f2fe;border-radius:5px;font-size:0.7em'>";
    html += "<option value='latch'>CRUISE</option><option value='momentary'>HOLD</option></select></div>";
    html += "<div class='grid-3'>";
    html += "<div></div><button class='btn btn-move' onmousedown='m(\"forward\")' onmouseup='s()' onmouseleave='s()'><span class='icon'>▲</span><span class='label'>Forward</span></button><div></div>";
    html += "<button class='btn btn-move' onmousedown='m(\"left\")' onmouseup='s()' onmouseleave='s()'><span class='icon'>◀</span><span class='label'>Left</span></button>";
    html += "<button class='btn btn-stop' onclick='cmd(\"stop\")'><span class='icon'>■</span><span class='label'>Stop</span></button>";
    html += "<button class='btn btn-move' onmousedown='m(\"right\")' onmouseup='s()' onmouseleave='s()'><span class='icon'>▶</span><span class='label'>Right</span></button>";
    html += "<div></div><button class='btn btn-move' onmousedown='m(\"backward\")' onmouseup='s()' onmouseleave='s()'><span class='icon'>▼</span><span class='label'>Back</span></button><div></div>";
    html += "</div>";
    html += "<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px'>";
    html += "<button class='btn btn-move' style='aspect-ratio:auto;height:45px' onmousedown='m(\"left_pivot\")' onmouseup='s()' onmouseleave='s()'><span class='label'>↶ Pivot Left</span></button>";
    html += "<button class='btn btn-move' style='aspect-ratio:auto;height:45px' onmousedown='m(\"right_pivot\")' onmouseup='s()' onmouseleave='s()'><span class='label'>↷ Pivot Right</span></button>";
    html += "</div></div>";

    html += "<div class='card'><div class='section-title'>Head / Camera Pan-Tilt</div>";
    html += "<div class='slider-container'><div class='label'>Pan (Horizontal)</div><input type='range' min='0' max='180' value='90' class='slider' onchange='val(\"pan\",this.value)'></div>";
    html += "<div class='slider-container'><div class='label'>Tilt (Vertical)</div><input type='range' min='0' max='180' value='90' class='slider' onchange='val(\"tilt\",this.value)'></div>";
    html += "</div>";

    html += "<div class='card'><div class='section-title'>Actions & Modes</div><div class='grid-3'>";
    html += "<button class='btn btn-action' onclick='cmd(\"transform\")'><span class='icon'>🔄</span><span class='label'>Transform</span></button>";
    html += "<button class='btn btn-action' onclick='cmd(\"walk\")'><span class='icon'>🚶</span><span class='label'>Walk Mode</span></button>";
    html += "<button class='btn btn-action' onclick='cmd(\"auto\")'><span class='icon'>🤖</span><span class='label'>Auto Pilot</span></button>";
    html += "<button class='btn btn-action' style='background:linear-gradient(45deg,#f093fb,#f5576c)' onclick='cmd(\"test\")'><span class='icon'>🩺</span><span class='label'>Self-Test</span></button>";
    html += "</div></div>";

    html += "<div class='card'><div class='section-title'>Expressions</div><div class='grid-3'>";
    html += "<button class='btn btn-mood' onclick='expr(\"happy\")'><span class='icon'>😊</span><span class='label'>Happy</span></button>";
    html += "<button class='btn btn-mood' onclick='expr(\"angry\")'><span class='icon'>😠</span><span class='label'>Angry</span></button>";
    html += "<button class='btn btn-mood' onclick='expr(\"hero\")'><span class='icon'>😎</span><span class='label'>Hero</span></button>";
    html += "</div></div>";

    html += "<div class='card'><div class='section-title'>Intercom (Robot Voice)</div>";
    html += "<button id='micBtn' class='btn btn-stop' style='width:100%;aspect-ratio:auto;height:60px;flex-direction:row;gap:10px'>";
    html += "<span class='icon'>🎤</span><span class='label'>Hold to Talk</span></button></div>";

    html += "<div class='card'><div class='section-title' style='display:flex;justify-content:space-between;align-items:center'>";
    html += "<span>Surround Intelligence</span>";
    html += "<div><button onclick='cmd(\"scan\")' style='background:#00f2fe;color:#000;border:none;padding:2px 10px;border-radius:5px;font-size:0.7em;font-weight:bold;margin-right:5px'>SCAN</button>";
    html += "<button id='stealthBtn' onclick='cmd(\"stealth\")' style='background:#ff00cc;color:#fff;border:none;padding:2px 10px;border-radius:5px;font-size:0.7em;font-weight:bold;margin-right:5px'>STEALTH</button>";
    html += "<button id='honeypotBtn' onclick='cmd(\"honeypot\")' style='background:#ed213a;color:#fff;border:none;padding:2px 10px;border-radius:5px;font-size:0.7em;font-weight:bold'>HONEYPOT</button></div></div>";
    html += "<div id='device-list' style='font-size:0.8em;max-height:200px;overflow-y:auto;margin-top:10px'>";
    
    if (_surround) {
        for (int i = 0; i < _surround->getDeviceCount(); i++) {
            ScannedDevice d = _surround->getDevice(i);
            String icon = d.isBle ? "📶 " : (d.isSniffed ? "🕵️ " : "🌐 ");
            html += "<div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.1)'>";
            html += "<span>" + icon + d.name + (d.isSniffed ? " (SNIFFED)" : "") + "</span>";
            
            html += "<div style='display:flex;gap:5px'>";
            if (d.mac != "" && !d.isBle) {
                html += "<button onclick='fetch(\"/takeover?mac=" + d.mac + "\")' style='background:none;border:1px solid #ff00cc;color:#ff00cc;font-size:0.7em;padding:1px 5px'>WOL</button>";
                html += "<button onclick='fetch(\"/deauth?mac=" + d.mac + "\")' style='background:none;border:1px solid #ed213a;color:#ed213a;font-size:0.7em;padding:1px 5px'>KICK</button>";
            } else if (!d.isBle && d.ip != "") {
                html += "<button onclick='fetch(\"/takeover?ip=" + d.ip + "\")' style='background:none;border:1px solid #00f2fe;color:#00f2fe;font-size:0.7em;padding:1px 5px'>TAKEOVER</button>";
            } else {
                html += "<span style='color:rgba(255,255,255,0.5)'>" + String(d.rssi) + " dBm</span>";
            }
            html += "</div></div>";
        }
    }
    html += "</div></div>";

    html += "</div>"; // end container
    html += "<script>";
    html += "let socket; let useWS = false;";
    html += "const ROBOT_LANG = '" + String(ROBOT_LANGUAGE) + "';";
    html += "function initWS(){";
    html += "  socket = new WebSocket('ws://'+window.location.hostname+':81/');";
    html += "  socket.onopen = () => { console.log('WS Connected'); useWS = true; document.getElementById('status').textContent='⚡ REAL-TIME'; };";
    html += "  socket.onclose = () => { console.log('WS Disconnected'); useWS = false; document.getElementById('status').textContent='FALLBACK (HTTP)'; setTimeout(initWS, 2000); };";
    html += "  socket.onmessage = (e) => { ";
    html += "    if(e.data.startsWith('SAY:')){";
    html += "      let text = e.data.substring(4);";
    html += "      document.getElementById('status').textContent = 'ROBOT: ' + text;";
    html += "      let utterance = new SpeechSynthesisUtterance(text);";
    html += "      utterance.lang = ROBOT_LANG;";
    html += "      utterance.pitch = 0.8; utterance.rate = 1.0; ";
    html += "      window.speechSynthesis.speak(utterance);";
    html += "    }";
    html += "  };";
    html += "}";

    
    html += "function cmd(d){ let c = 'CMD:'+d.toUpperCase(); if(useWS){ socket.send(c); } else { fetch('/'+d).then(r=>r.text()).then(t=>{document.getElementById('status').textContent=t;}); } }";
    html += "function m(d){ cmd(d); }";
    html += "function s(){ if(document.getElementById('mode').value==='momentary'){ cmd('stop'); } }";
    html += "function val(p,v){ let c = p.toUpperCase()+':'+v; if(useWS){ socket.send(c); } else { fetch('/'+p+'?val='+v); } }";
    html += "function expr(m){ let c = 'FACE:'+m.toUpperCase(); if(useWS){ socket.send(c); } else { fetch('/expression?val='+m); } }";
    
    html += "window.onload = initWS;";
    
    html += "// Intercom Logic\n";
    html += "const micBtn = document.getElementById('micBtn');";
    html += "let mediaRecorder;";

    html += "micBtn.onmousedown = async () => {";
    html += "    try {";
    html += "        micBtn.style.background = 'linear-gradient(45deg, #ff0000, #990000)';";
    html += "        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });";
    html += "        mediaRecorder = new MediaRecorder(stream);";
    html += "        mediaRecorder.ondataavailable = (e) => {";
    html += "            fetch('/voice', { method: 'POST', body: e.data });";
    html += "        };";
    html += "        mediaRecorder.start(100); ";
    html += "    } catch(e) { console.error('Mic Error:', e); }";
    html += "};";

    html += "micBtn.onmouseup = () => {";
    html += "    micBtn.style.background = '';";
    html += "    if(mediaRecorder && mediaRecorder.state !== 'inactive') {";
    html += "        mediaRecorder.stop();";
    html += "        mediaRecorder.stream.getTracks().forEach(t => t.stop());";
    html += "    }";
    html += "};";
    html += "</script></body></html>";
    return html;
}

void WebInterface::handleRoot() {
    _server.send(200, "text/html", getHTML());
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
