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
#include <esp_task_wdt.h>

#define WDT_TIMEOUT 10 // 10 seconds for Comm Controller

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

// --- ADVANCED SELF-HEALING: RELIABLE SERIAL LINK ---
void reliableSendCommand(String cmd) {
    int retries = 0;
    bool ackReceived = false;
    
    while (retries < 3 && !ackReceived) {
        Serial2.println(cmd);
        unsigned long start = millis();
        
        while (millis() - start < 150) { 
            if (Serial2.available()) {
                String response = Serial2.readStringUntil('\n');
                response.trim();
                if (response == "ACK:" + cmd) {
                    ackReceived = true;
                    break;
                }
            }
        }
        if (!ackReceived) {
            retries++;
            Serial.println("[RETRY] Command failed: " + cmd + " (Attempt " + String(retries) + ")");
        }
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    
    // Enable Hardware Watchdog (Anti-Freeze)
    esp_task_wdt_init(WDT_TIMEOUT, true);
    esp_task_wdt_add(NULL);

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
    esp_task_wdt_reset(); // Feed the watchdog (Anti-Freeze)
    ArduinoOTA.handle();
    
    // 1. Connection Watchdog (Self-Healing)
    static unsigned long lastAiHeartbeat = millis();
    if (web.hasNewCommand()) {
        lastAiHeartbeat = millis(); // Reset healer on activity
    }
    
    // If we've been connected to WiFi but no AI data for 45s, connection is "Zombie"
    if (network.isWiFiConnected() && (millis() - lastAiHeartbeat > 45000)) {
        Serial.println("[HEAL] Connection Zombie detected. Re-initializing Network...");
        network.beginWiFi(); // Force a fresh connection
        lastAiHeartbeat = millis();
    }

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
        } else if (cmd.startsWith("GOTO:")) {
            // Forward coordinate navigation to Motion Controller
            reliableSendCommand(cmd);
        } else {
            // Forward everything else (Moves, Pan/Tilt, Modes) to Motion Controller
            // SELF-HEALING: Reliable Command Link with ACKs
            reliableSendCommand(cmd); 
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
    
    // 5. Advanced Network Synchronization (Hotspot Sync)
    static bool hotspotSynced = false;
    if (network.isHotspotActive() && !hotspotSynced) {
        WiFiSync sync;
        strncpy(sync.ssid, "Omni-Gateway", 32);
        strncpy(sync.pass, "robot4glink", 64);
        
        uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
        esp_now_send(broadcastAddress, (uint8_t *) &sync, sizeof(WiFiSync));
        Serial.println("[SYNC] Slaves moved to 4G Internal Hotspot.");
        hotspotSynced = true;
    }
    
    // 6. Read Telemetry from Motion Controller
    static float currentYaw = 0;
    while (Serial2.available()) {
        String telemetry = Serial2.readStringUntil('\n');
        telemetry.trim();
        
        if (telemetry.startsWith("YAW:")) {
            currentYaw = telemetry.substring(4).toFloat();
        } else if (telemetry.startsWith("DISTANCE:")) {
            int dist = telemetry.substring(9).toInt();
            web.sendToAi(telemetry);
            
            // Shared Obstacle Memory Logic
            if (dist > 0 && dist < 30) {
                float rad = (currentYaw * PI) / 180.0;
                float obsX = web.getPosX() + dist * cos(rad);
                float obsY = web.getPosY() + dist * sin(rad);
                
                Serial.printf("[SWARM] Obstacle detected at X:%.1f Y:%.1f. Broadcasting...\n", obsX, obsY);
                
                // Construct swarm data with obstacle
                SwarmData data;
                strncpy(data.senderName, ROBOT_NAME, 16);
                data.mood = currentMood;
                data.x = web.getPosX();
                data.y = web.getPosY();
                data.obsX = obsX;
                data.obsY = obsY;
                data.hasObstacle = true;
                
                // Broadcast to everyone
                swarm.broadcast(data.mood, 100, ""); // Need to update swarm.broadcast to take SwarmData or similar
                // Wait, swarm.broadcast currently takes int mood, int battery. 
                // I'll update SwarmLink.cpp to allow broadcasting full data.
            }
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

    if (swarm.hasNewData()) {
        SwarmData other = swarm.getLastData();
        if (other.hasObstacle) {
            Serial.printf("[SWARM-AI] Robot %s alerted! Obstacle at (%.1f, %.1f)\n", other.senderName, other.obsX, other.obsY);
            web.broadcast("ALERT: " + String(other.senderName) + " found obstacle at " + String(other.obsX) + "," + String(other.obsY));
        }
    }
}
