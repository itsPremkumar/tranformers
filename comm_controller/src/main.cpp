#include <Arduino.h>
#include "Config.h"
#include "Network.h"
#include "Audio.h"
#include "Display.h"
#include "RobotServer.h"
#include "BluetoothAudio.h"
#include <ArduinoOTA.h>
#include <Preferences.h>
#include "SwarmLink.h"
#include "SurroundControl.h"

// Networking using Config IDs
Network network(WIFI_SSID, WIFI_PASS, SIM_RX_PIN, SIM_TX_PIN);

#if USE_AUDIO_SYSTEM
AudioSystem audioSys(I2S_BCK_PIN, I2S_WS_PIN, I2S_DIN_PIN, I2S_DOUT_PIN);
#endif

#if USE_OLED_DISPLAY
DisplayController displayCtrl(0x3C);
#endif

SurroundControl surroundCtrl;

#if USE_AUDIO_SYSTEM
WebInterface web(&audioSys, &surroundCtrl, &network, WEB_PORT);
#else
WebInterface web(NULL, &surroundCtrl, &network, WEB_PORT);
#endif
#if USE_BLUETOOTH_AUDIO
BluetoothAudio btAudio;
#endif

Preferences prefs;
int currentMood = 0; // 0=Happy, 1=Sad, 2=Angry, 3=Hero
SwarmLink swarm;
bool isAiListening = false;
unsigned long lastDisplayUpdate = 0;
unsigned long lastSwarmBroadcast = 0;
unsigned long aiListenStartTime = 0;

void setup() {
    Serial.begin(SERIAL_BAUD);
    
    // Communication with Motion Controller
    Serial2.begin(SERIAL_BAUD, SERIAL_8N1, MOTION_LINK_RX, MOTION_LINK_TX);
    
    #if USE_OLED_DISPLAY
    Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN); 
    displayCtrl.begin();
    
    prefs.begin("robot", false);
    currentMood = prefs.getInt("mood", 0);
    displayCtrl.drawBitmapFace(currentMood);
    #endif
    
    network.beginWiFi();
    
    #if USE_AUDIO_SYSTEM
    audioSys.begin();
    #endif

    #if USE_BLUETOOTH_AUDIO
    // Wait a bit after WiFi to let things settle
    delay(100); 
    btAudio.begin(I2S_BCK_PIN, I2S_WS_PIN, I2S_DOUT_PIN);
    #endif
    
    if (network.isWiFiConnected()) {
        web.begin();
        swarm.begin("OMNI-01"); 
        surroundCtrl.begin();
        #if USE_OLED_DISPLAY
        displayCtrl.peaceFace();
        #endif
    } else {
        #if USE_OLED_DISPLAY
        displayCtrl.sadFace();
        #endif
    }
    
    ArduinoOTA.setHostname(BT_DEVICE_NAME); 
    ArduinoOTA.begin();
    
    Serial.println("Comm Controller Ready.");
}

unsigned long lastNetworkCheck = 0;

void loop() {
    ArduinoOTA.handle();
    
    // Update Wireless Masters
    network.update();
    surroundCtrl.update();
    
    // Server & Web Interface
    web.handleClient();
    
    // 2. Periodic Network Fallback Check (Every 10 seconds)
    if (millis() - lastNetworkCheck > 10000) {
        network.checkConnection();
        lastNetworkCheck = millis();
    }
    
    // 3. Heartbeat & Audio Processing
    static unsigned long lastHeartbeat = 0;
    if (millis() - lastHeartbeat > 1000) {
        Serial2.println("BEAT");
        lastHeartbeat = millis();
    }

    #if USE_AUDIO_SYSTEM
    if (audioSys.processAudio()) {
        isAiListening = true;
        aiListenStartTime = millis();
        #if USE_OLED_DISPLAY
        displayCtrl.heroFace();
        #endif
        web.broadcast("STATUS: I am listening...");
        Serial.println("[AI] Wake Word Detected. Listening...");
    }

    // Auto-timeout AI listening after 10 seconds of no interaction
    if (isAiListening && (millis() - aiListenStartTime > 10000)) {
        isAiListening = false;
        web.broadcast("STATUS: Going to sleep...");
        #if USE_OLED_DISPLAY
        displayCtrl.drawBitmapFace(currentMood);
        #endif
    }
    #endif
    
    // 4. Process any new commands from Web UI
    if (web.hasNewCommand()) {
        aiListenStartTime = millis(); // Refresh timeout
        String cmd = web.getLastCommand();
        Serial.println("Action Received: " + cmd);
        
        if (cmd == "CMD:TEST") {
            // ... (keep test logic)
        } else if (cmd == "CMD:SCAN") {
            surroundCtrl.scanNetwork();
            surroundCtrl.startBleScan(5);
            String msg = "Captured " + String(surroundCtrl.getDeviceCount()) + " devices.";
            web.broadcast("STATUS: " + msg);
            #if USE_OLED_DISPLAY
            displayCtrl.heroFace(); // Show excitement
            #endif
        } else if (cmd.startsWith("FACE:")) {
            #if USE_OLED_DISPLAY
            String mood = cmd.substring(5);
            if (mood == "happy") { currentMood = 0; displayCtrl.happyFace(); }
            else if (mood == "sad") { currentMood = 1; displayCtrl.sadFace(); }
            else if (mood == "angry") { currentMood = 2; displayCtrl.angryFace(); }
            else if (mood == "hero") { currentMood = 3; displayCtrl.heroFace(); }
            else if (mood.length() > 0 && isDigit(mood[0])) {
                currentMood = mood.toInt();
                displayCtrl.drawBitmapFace(currentMood);
            }
            prefs.putInt("mood", currentMood);
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
    audioSys.processAudio(); 
    #endif
    
    // 4. Update Display animations or Lip-Sync
    #if USE_OLED_DISPLAY
    int amp = audioSys.getRecentAmplitude();
    if (amp > 500) { // If audio is playing
        displayCtrl.drawTalkingMouth(amp);
        lastDisplayUpdate = millis(); // Defer random animations
    } else if (millis() - lastDisplayUpdate > 3000) {
        displayCtrl.updateRandom();
        lastDisplayUpdate = millis();
    }
    #endif
    
    surroundCtrl.update();

    // 5. Swarm Intelligence (ESP-NOW)
    if (millis() - lastSwarmBroadcast > 5000) {
        // Broadcast our state to other robots
        int batVal = analogRead(34); // Pseudo battery read for swarm data
        swarm.broadcast(currentMood, batVal);
        lastSwarmBroadcast = millis();
    }

    if (swarm.hasNewData()) {
        SwarmData other = swarm.getLastData();
        Serial.print("[SWARM-AI] Mirroring mood from: ");
        Serial.println(other.senderName);
        
        #if USE_OLED_DISPLAY
        // Social Mirroring: If another robot is "Angry", we get "Hero" mode to help
        if (other.mood == 2) { 
            displayCtrl.heroFace();
            web.broadcast("STATUS: Fellow robot is in trouble! I'm helping.");
        }
        #endif
    }
    
    // 6. Read Telemetry from Motion Controller
    while (Serial2.available()) {
        String telemetry = Serial2.readStringUntil('\n');
        telemetry.trim();
        if (telemetry.startsWith("DISTANCE:")) {
            web.sendToAi(telemetry);
        } else if (telemetry.startsWith("BATTERY:")) {
            web.sendToAi(telemetry);
        } else if (telemetry.startsWith("CURRENT:")) {
            web.sendToAi(telemetry);
        } else if (telemetry.startsWith("ROUGHNESS:")) {
            float r = telemetry.substring(10).toFloat();
            if (r > 0.05) { // Threshold for "Rough"
                web.broadcast("STATUS: Rough Terrain Detected! Consider CRAWLER mode.");
                #if USE_OLED_DISPLAY
                displayCtrl.warningFace();
                #endif
            }
        } else if (telemetry == "CMD:BATTERY_LOW") {
            #if USE_OLED_DISPLAY
            displayCtrl.sadFace(); // Show sad face for low battery
            #endif
            web.broadcast("STATUS: Battery Low!");
        } else if (telemetry == "CMD:BATTERY_CRITICAL") {
            #if USE_OLED_DISPLAY
            displayCtrl.drawBitmapFace(4); // Use a "dead" or "critical" face if bitmap 4 is suitable
            #endif
            web.broadcast("STATUS: CRITICAL BATTERY! Shutting down...");
        }
    }
}
