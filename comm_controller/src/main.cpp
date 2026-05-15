#include <Arduino.h>
#include <ArduinoOTA.h>
#include <Preferences.h>
#include <esp_task_wdt.h>
#include "Config.h"
#include "Network.h"
#include "AudioSystem.h"
#include "Display.h"
#include "RobotServer.h"
#include "BluetoothAudio.h"
#include "SwarmLink.h"
#include "SurroundControl.h"
#include "Connectivity.h"
#include "Interaction.h"
#include "SwarmIntelligence.h"
#include "BLEManager.h"

#define WDT_TIMEOUT 10 

// --- Hardware Instances ---
Network network(WIFI_SSID, WIFI_PASS, SIM_RX_PIN, SIM_TX_PIN);
SurroundControl surroundCtrl;
SwarmLink swarm;
Preferences prefs;
BLEManager bleManager;

#if USE_AUDIO_SYSTEM
AudioSystem audioSys(I2S_BCK_PIN, I2S_WS_PIN, I2S_DIN_PIN, I2S_DOUT_PIN);
#endif

#if USE_OLED_DISPLAY
DisplayController displayCtrl(0x3C);
#endif

#if USE_BLUETOOTH_AUDIO
BluetoothAudio btAudio;
#endif

#if USE_AUDIO_SYSTEM
WebInterface web(&audioSys, &surroundCtrl, &network, WEB_PORT);
#else
WebInterface web(NULL, &surroundCtrl, &network, WEB_PORT);
#endif

// --- Module Instances ---
Connectivity connect(network, web, surroundCtrl, bleManager);
Interaction interact(&audioSys, &displayCtrl, &btAudio, web);
SwarmIntelligence swarmAI(swarm, &displayCtrl, web);

int currentMood = 0;
unsigned long lastDisplayUpdate = 0;
float currentYaw = 0;

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial2.begin(SERIAL_BAUD, SERIAL_8N1, MOTION_LINK_RX, MOTION_LINK_TX);
    
    esp_task_wdt_init(WDT_TIMEOUT, true);
    esp_task_wdt_add(NULL);

    #if USE_OLED_DISPLAY
    Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN); 
    #endif

    interact.begin();
    connect.begin();
    swarmAI.begin();

    prefs.begin("robot", false);
    currentMood = prefs.getInt("mood", 0);
    #if USE_OLED_DISPLAY
    displayCtrl.drawBitmapFace(currentMood);
    #endif

    ArduinoOTA.setHostname(BT_DEVICE_NAME); 
    ArduinoOTA.begin();

    Serial.println("Comm Controller Modular Ready.");
}

void loop() {
    esp_task_wdt_reset();
    ArduinoOTA.handle();

    connect.update();
    interact.update(currentMood);
    swarmAI.update(currentMood);
    #if USE_AUDIO_SYSTEM
    audioSys.update();
    #endif

    // 1. Process Web Commands
    if (web.hasNewCommand()) {
        String cmd = web.getLastCommand();
        Serial.println("Action Received: " + cmd);
        
        if (cmd == "CMD:SCAN") {
            surroundCtrl.scanNetwork();
            surroundCtrl.startBleScan(5);
            web.broadcast("STATUS: Scanning started...");
        } else if (cmd.startsWith("FACE:")) {
            interact.handleMoodChange(currentMood, cmd);
            prefs.putInt("mood", currentMood);
        } else if (cmd.startsWith("SAY:")) {
            #if USE_OLED_DISPLAY
            displayCtrl.talkingAnimation();
            #endif
            web.broadcast(cmd); 
        } else if (cmd.startsWith("MEM:")) {
            // Memory logic kept in main for now as it uses local Preferences
            int eqIdx = cmd.indexOf('=');
            if (eqIdx > 4) {
                String key = cmd.substring(4, eqIdx);
                String val = cmd.substring(eqIdx + 1);
                Preferences vault;
                vault.begin("vault", false);
                vault.putString(key.c_str(), val);
                vault.end();
                web.broadcast("STATUS: I remembered " + key);
            }
        } else if (cmd.startsWith("GET_MEM:")) {
            String key = cmd.substring(8);
            Preferences vault;
            vault.begin("vault", true);
            String val = vault.getString(key.c_str(), "Unknown");
            vault.end();
            web.broadcast("MEM_VAL:" + key + "=" + val);
        } else {
            connect.reliableSendCommand(cmd); 
        }
        web.clearCommand();
    }

    // 2. Process Telemetry from Motion Controller
    while (Serial2.available()) {
        String telemetry = Serial2.readStringUntil('\n');
        telemetry.trim();
        
        if (telemetry.startsWith("YAW:")) {
            currentYaw = telemetry.substring(4).toFloat();
        } else if (telemetry.startsWith("DISTANCE:")) {
            int dist = telemetry.substring(9).toInt();
            web.sendToAi(telemetry);
            swarmAI.broadcastObstacle(currentMood, currentYaw, dist);
        } else if (telemetry.startsWith("ROUGHNESS:")) {
            float r = telemetry.substring(10).toFloat();
            if (r > 0.05) {
                web.broadcast("STATUS: Rough Terrain Detected!");
                #if USE_OLED_DISPLAY
                displayCtrl.warningFace();
                #endif
            }
        } else if (telemetry == "CMD:BATTERY_LOW") {
            #if USE_OLED_DISPLAY
            displayCtrl.sadFace();
            #endif
            web.broadcast("STATUS: Battery Low!");
        } else if (telemetry == "CMD:BATTERY_CRITICAL") {
            #if USE_OLED_DISPLAY
            displayCtrl.drawBitmapFace(4);
            #endif
            web.broadcast("STATUS: CRITICAL BATTERY! Shutting down...");
        } else {
            web.sendToAi(telemetry);
        }
    }
}
