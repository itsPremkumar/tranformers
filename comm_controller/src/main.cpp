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
#include "McpEngine.h"

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
#if USE_BLUETOOTH_AUDIO
Interaction interact(&audioSys, &displayCtrl, &btAudio, web);
#else
Interaction interact(&audioSys, &displayCtrl, NULL, web);
#endif
SwarmIntelligence swarmAI(swarm, &displayCtrl, web);

int currentMood = 0;
unsigned long lastDisplayUpdate = 0;
float currentYaw = 0;

void checkMemory() {
    size_t freeHeap = ESP.getFreeHeap();
    if (freeHeap < MIN_FREE_MEMORY) {
        Serial.printf("[WARN] Low Memory: %u bytes. Cleaning up...\n", freeHeap);
        // Clear caches or disconnect non-essential clients if needed
    }
}

#include <nvs_flash.h>

void setup() {
    Serial.begin(SERIAL_BAUD);
    
    // Explicit NVS initialization and self-healing to prevent wifi_init out-of-memory error (ret=101)
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        err = nvs_flash_init();
    }
    if (err != ESP_OK) {
        Serial.printf("[NVS ERROR] Failed to initialize NVS: %d\n", err);
    }

    Serial2.begin(SERIAL_BAUD, SERIAL_8N1, MOTION_LINK_RX, MOTION_LINK_TX);
    
    esp_task_wdt_init(WDT_TIMEOUT, true);
    esp_task_wdt_add(NULL);

    #if USE_OLED_DISPLAY
    Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN); 
    #endif

    connect.begin();
    interact.begin();
    swarmAI.begin();
    McpEngine::getInstance().begin();

    prefs.begin("robot", false);
    currentMood = prefs.getInt("mood", 0);
    #if USE_OLED_DISPLAY
    displayCtrl.drawBitmapFace(currentMood);
    #endif

    ArduinoOTA.setHostname(BT_DEVICE_NAME);
    ArduinoOTA.setPassword("omni123");

    ArduinoOTA.onStart([]() {
        String type = (ArduinoOTA.getCommand() == U_FLASH) ? "sketch" : "filesystem";
        Serial.println("[OTA] Updating " + type);
        #if USE_OLED_DISPLAY
        displayCtrl.showProgress("UPDATING BRAIN...", 0);
        #endif
        web.broadcast("STATUS: Wireless Update Started...");
    });

    ArduinoOTA.onEnd([]() {
        Serial.println("\n[OTA] Success!");
        #if USE_OLED_DISPLAY
        displayCtrl.showProgress("REBOOTING...", 100);
        #endif
        web.broadcast("STATUS: Update Successful. Rebooting...");
    });

    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        int p = (progress / (total / 100));
        #if USE_OLED_DISPLAY
        displayCtrl.showProgress("UPDATING...", p);
        #endif
        if (p % 10 == 0) web.broadcast("OTA_PROGRESS:" + String(p));
    });

    ArduinoOTA.onError([](ota_error_t error) {
        #if USE_OLED_DISPLAY
        displayCtrl.warningFace();
        #endif
        web.broadcast("STATUS: OTA Error!");
    });

    ArduinoOTA.begin();

    ArduinoOTA.begin();

    if (DEBUG_LEVEL >= 1) Serial.println("Comm Controller Modular Ready.");
    #if USE_AUDIO_SYSTEM
    audioSys.playChime(0);
    #endif
}

void loop() {
    esp_task_wdt_reset();
    checkMemory();
    ArduinoOTA.handle();

    connect.update();
    web.update();
    interact.update(currentMood);
    swarmAI.update(currentMood);
    #if USE_AUDIO_SYSTEM
    audioSys.update();
    #endif

    // 1. Process Web & USB Serial Commands
    static unsigned long lastInteraction = millis();
    String cmd = "";
    bool hasCmd = false;

    if (web.hasNewCommand()) {
        cmd = web.getLastCommand();
        hasCmd = true;
        web.clearCommand();
    } else if (Serial.available()) {
        cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd.length() > 0) {
            hasCmd = true;
        }
    }

    if (hasCmd) {
        lastInteraction = millis(); // Reset idle timer
        if (DEBUG_LEVEL >= 2) Serial.println("Action Received: " + cmd);
        
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
        } else if (cmd.startsWith("SUB_TEXT:")) {
            #if USE_OLED_DISPLAY
            String text = cmd.substring(9);
            displayCtrl.SetSubtitle(text);
            #endif
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
            if (cmd == "CMD:TRANSFORM" || cmd == "CMD:CRAWLER") {
                #if USE_OLED_DISPLAY
                displayCtrl.SetState(FaceState::Transforming);
                #endif
            }
            connect.reliableSendCommand(cmd); 
        }
    }

    // 2. Curiosity Engine: Trigger if idle for 2 minutes
    if (millis() - lastInteraction > 120000) {
        lastInteraction = millis(); // Reset to avoid spamming
        Serial.println("[CURIOSITY] Idle detected. Requesting AI observation...");
        web.sendToAi("CMD:IDLE_OBSERVE");
    }

    // 3. Process Telemetry from Motion Controller
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
