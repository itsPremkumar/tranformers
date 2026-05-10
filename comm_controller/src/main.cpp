#include <Arduino.h>
#include "Config.h"
#include "Network.h"
#include "Audio.h"
#include "Display.h"
#include "WebServer.h"

// Networking using Config IDs
Network network(WIFI_SSID, WIFI_PASS, SIM_RX_PIN, SIM_TX_PIN);

#if USE_AUDIO_SYSTEM
AudioSystem audioSys(I2S_BCK_PIN, I2S_WS_PIN, I2S_DIN_PIN, I2S_DOUT_PIN);
#endif

#if USE_OLED_DISPLAY
DisplayController displayCtrl(0x3C);
#endif

#if USE_AUDIO_SYSTEM
WebInterface web(&audioSys, WEB_PORT);
#else
WebInterface web(NULL, WEB_PORT);
#endif

unsigned long lastDisplayUpdate = 0;

void setup() {
    Serial.begin(SERIAL_BAUD);
    
    // Communication with Motion Controller
    Serial2.begin(SERIAL_BAUD, SERIAL_8N1, MOTION_LINK_RX, MOTION_LINK_TX);
    
    #if USE_OLED_DISPLAY
    Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN); 
    displayCtrl.begin();
    displayCtrl.happyFace();
    #endif
    
    network.beginWiFi();
    
    #if USE_AUDIO_SYSTEM
    audioSys.begin();
    #endif
    
    if (network.isWiFiConnected()) {
        web.begin();
        #if USE_OLED_DISPLAY
        displayCtrl.peaceFace();
        #endif
    } else {
        #if USE_OLED_DISPLAY
        displayCtrl.sadFace();
        #endif
    }
    
    Serial.println("Comm Controller Ready.");
}

unsigned long lastNetworkCheck = 0;

void loop() {
    // 1. Handle Web Requests & WebSocket loop
    web.handleClient();
    
    // 2. Periodic Network Fallback Check (Every 10 seconds)
    if (millis() - lastNetworkCheck > 10000) {
        network.checkConnection();
        lastNetworkCheck = millis();
    }
    
    // 3. Heartbeat Pulse (Every 1 second)
    static unsigned long lastHeartbeat = 0;
    if (millis() - lastHeartbeat > 1000) {
        Serial2.println("BEAT");
        lastHeartbeat = millis();
    }
    
    // 4. Process any new commands from Web UI
    if (web.hasNewCommand()) {
        String cmd = web.getLastCommand();
        Serial.println("Action Received: " + cmd);
        
        if (cmd == "CMD:TEST") {
            Serial.println("\n[COMM-DIAGNOSTICS] Starting Brain Test...");
            Serial.println("[TEST] Active Network: " + network.getActiveNetwork());
            Serial.println("[TEST] WiFi Signal (RSSI): " + String(WiFi.RSSI()) + " dBm");
            #if USE_AUDIO_SYSTEM
            audioSys.playTestTone();
            #endif
            Serial.println("[COMM-DIAGNOSTICS] Brain Test Complete. Forwarding to Motion...");
            Serial2.println(cmd); 
        } else if (cmd.startsWith("FACE:")) {
            #if USE_OLED_DISPLAY
            String mood = cmd.substring(5);
            if (mood == "happy") displayCtrl.happyFace();
            else if (mood == "angry") displayCtrl.angryFace();
            else if (mood == "hero") displayCtrl.heroFace();
            else if (mood == "thinking") displayCtrl.talkingAnimation();
            else if (mood.length() > 0 && isDigit(mood[0])) {
                displayCtrl.drawBitmapFace(mood.toInt());
            }
            #endif
        } else if (cmd.startsWith("SAY:")) {
            #if USE_OLED_DISPLAY
            String text = cmd.substring(4);
            displayCtrl.talkingAnimation();
            Serial.println("Robot Speaking: " + text);
            #endif
            // Also forward to Web UI via WebSocket if connected
            web.broadcast(cmd); 
        } else {
            // Forward everything else (Moves, Pan/Tilt, Modes) to Motion Controller
            Serial2.println(cmd); 
        }

        
        web.clearCommand();
        lastDisplayUpdate = millis();
    }
    
    // 3. Process Audio (Pass-through or simple analysis)
    #if USE_AUDIO_SYSTEM
    // audioSys.processAudio(); 
    #endif
    
    // 4. Update Display animations occasionally
    #if USE_OLED_DISPLAY
    if (millis() - lastDisplayUpdate > 3000) {
        displayCtrl.updateRandom();
        lastDisplayUpdate = millis();
    }
    // 5. Read Telemetry from Motion Controller
    while (Serial2.available()) {
        String telemetry = Serial2.readStringUntil('\n');
        telemetry.trim();
        if (telemetry.startsWith("DISTANCE:")) {
            web.sendToAi(telemetry);
        } else if (telemetry.startsWith("BATTERY:")) {
            web.sendToAi(telemetry);
        } else if (telemetry.startsWith("CURRENT:")) {
            web.sendToAi(telemetry);
        }
    }
}
