#include "DiagnosticServer.h"
#include <WiFi.h>
#include "Config.h"

// HTML page template for direct testing
const char DIAG_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta charset="UTF-8">
    <title>Omni-Morph Motion HW Diagnostic Console</title>
    <style>
        :root {
            --primary: #00f2fe;
            --secondary: #4facfe;
            --bg: #090a0f;
            --card: #151a22;
            --text: #f1f5f9;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: system-ui, -apple-system, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 480px;
        }
        h1 {
            color: var(--primary);
            text-align: center;
            text-transform: uppercase;
            font-size: 1.3rem;
            letter-spacing: 2px;
            margin-bottom: 25px;
            text-shadow: 0 0 12px rgba(0, 242, 254, 0.4);
        }
        .card {
            background: var(--card);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }
        .section-title {
            font-size: 0.8rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }
        .d-pad {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            width: 180px;
            margin: 20px auto;
        }
        .btn {
            background: #21262d;
            border: 1px solid #30363d;
            color: white;
            padding: 18px;
            border-radius: 12px;
            font-size: 1.3rem;
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s ease;
        }
        .btn:active {
            background: var(--primary);
            color: var(--bg);
            border-color: var(--primary);
            transform: scale(0.95);
            box-shadow: 0 0 15px var(--primary);
        }
        .btn-stop {
            background: #ef4444;
            border-color: #ef4444;
        }
        .btn-stop:active {
            background: #b91c1c;
            box-shadow: 0 0 15px #ef4444;
        }
        .btn-utility {
            background: #334155;
            padding: 10px;
            font-size: 0.8rem;
            border-radius: 8px;
            text-transform: uppercase;
        }
        select {
            width: 100%;
            background: #21262d;
            color: var(--primary);
            border: 1px solid var(--primary);
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            outline: none;
            margin-bottom: 10px;
        }
        .hud-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .hud-item {
            background: #0d1117;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 12px;
            text-align: center;
        }
        .hud-label {
            font-size: 0.7rem;
            color: #8b949e;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .hud-value {
            font-size: 1.15rem;
            color: var(--primary);
            font-weight: bold;
            font-family: monospace;
        }
        .footer {
            text-align: center;
            font-size: 0.7rem;
            color: #64748b;
            margin-top: 20px;
        }
    </style>
    <script>
        let mode = 'MOMENTARY';
        
        function sendCmd(cmd) {
            fetch('/cmd?val=' + cmd)
                .catch(err => console.error("Send failed:", err));
        }
        
        function handleStart(cmd) {
            sendCmd(cmd);
        }
        
        function handleEnd() {
            if (mode === 'MOMENTARY') {
                sendCmd('STOP');
            }
        }
        
        function updateMode(val) {
            mode = val;
            sendCmd('MODE_' + val);
        }
        
        function pollStatus() {
            fetch('/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('val-dist').innerText = data.dist + ' cm';
                    document.getElementById('val-amp').innerText = data.amps.toFixed(2) + ' A';
                    document.getElementById('val-yaw').innerText = data.yaw.toFixed(1) + '°';
                    document.getElementById('val-pitch').innerText = data.pitch.toFixed(1) + '°';
                })
                .catch(err => {});
        }
        
        setInterval(pollStatus, 300);
    </script>
</head>
<body>
    <div class="container">
        <h1>Motion HW Diagnostics</h1>
        
        <div class="card">
            <div class="section-title">Control Settings</div>
            <select onchange="updateMode(this.value)">
                <option value="MOMENTARY" selected>MOMENTARY (DEAD MAN SWITCH)</option>
                <option value="LATCHING">LATCHING (CRUISE CONTROL)</option>
            </select>
            
            <div class="d-pad">
                <div></div>
                <button class="btn" onmousedown="handleStart('FORWARD')" onmouseup="handleEnd()" onmouseleave="handleEnd()">▲</button>
                <div></div>
                <button class="btn" onmousedown="handleStart('LEFT')" onmouseup="handleEnd()" onmouseleave="handleEnd()">◀</button>
                <button class="btn btn-stop" onclick="sendCmd('STOP')">■</button>
                <button class="btn" onmousedown="handleStart('RIGHT')" onmouseup="handleEnd()" onmouseleave="handleEnd()">▶</button>
                <div></div>
                <button class="btn" onmousedown="handleStart('BACKWARD')" onmouseup="handleEnd()" onmouseleave="handleEnd()">▼</button>
                <div></div>
            </div>
        </div>

        <div class="card">
            <div class="section-title">Diagnostics HUD</div>
            <div class="hud-grid">
                <div class="hud-item">
                    <div class="hud-label">Ultrasonic Range</div>
                    <div id="val-dist" class="hud-value">-- cm</div>
                </div>
                <div class="hud-item">
                    <div class="hud-label">Current Draw</div>
                    <div id="val-amp" class="hud-value">-- A</div>
                </div>
                <div class="hud-item">
                    <div class="hud-label">IMU Yaw</div>
                    <div id="val-yaw" class="hud-value">--°</div>
                </div>
                <div class="hud-item">
                    <div class="hud-label">IMU Pitch</div>
                    <div id="val-pitch" class="hud-value">--°</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="section-title">Direct Utilities</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <button class="btn btn-utility" onclick="sendCmd('TRANSFORM')">⚡ Transform</button>
                <button class="btn btn-utility" onclick="sendCmd('TEST')">🩺 Self-Test</button>
            </div>
        </div>
        
        <div class="footer">
            Direct Web Panel hosted on Motion Control ESP32
        </div>
    </div>
</body>
</html>
)rawliteral";

DiagnosticServer::DiagnosticServer(MotorControl& car, CommandHandler& cmdHandler, ObstacleAvoidance& obstacle, Balance& balance) 
    : _server(80), _car(car), _cmdHandler(cmdHandler), _obstacle(obstacle), _balance(balance) {}

void DiagnosticServer::begin() {
    // Start Dedicated Diagnostics SoftAP
    WiFi.softAP(DIAG_SSID, DIAG_PASS);
    Serial.println("[DIAG-AP] Test Suite Hotspot Started.");
    Serial.print("[DIAG-AP] Connect to SSID: ");
    Serial.print(DIAG_SSID);
    Serial.print(" | IP: ");
    Serial.println(WiFi.softAPIP());

    // Setup HTTP server endpoints
    _server.on("/", std::bind(&DiagnosticServer::handleRoot, this));
    _server.on("/cmd", std::bind(&DiagnosticServer::handleCommand, this));
    _server.on("/status", std::bind(&DiagnosticServer::handleStatus, this));
    
    _server.begin();
    Serial.println("[DIAG-SERVER] Web server started on port 80.");
}

void DiagnosticServer::update() {
    _server.handleClient();
}

void DiagnosticServer::handleRoot() {
    _server.send_P(200, "text/html", DIAG_HTML);
}

void DiagnosticServer::handleCommand() {
    if (_server.hasArg("val")) {
        String cmd = _server.arg("val");
        // Re-construct cmd format if not already matching the protocol
        if (!cmd.startsWith("CMD:")) {
            cmd = "CMD:" + cmd;
        }
        Serial.println("[DIAG-SERVER] Handled Command: " + cmd);
        _cmdHandler.processCommand(cmd);
        _server.send(200, "text/plain", "OK");
    } else {
        _server.send(400, "text/plain", "Bad Request");
    }
}

void DiagnosticServer::handleStatus() {
    float vCurr = (analogRead(CURRENT_PIN) / 4095.0) * 3.3;
    float amps = (vCurr - 1.65) / 0.1;
    if (amps < 0.0f) amps = 0.0f;

    String json = "{";
    json += "\"dist\":" + String(_obstacle.readFrontDistance()) + ",";
    json += "\"yaw\":" + String(_balance.getYaw(), 1) + ",";
    json += "\"pitch\":" + String(_balance.getPitch(), 1) + ",";
    json += "\"amps\":" + String(amps, 2);
    json += "}";
    _server.send(200, "application/json", json);
}
