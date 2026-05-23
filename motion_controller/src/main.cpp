#include <Arduino.h>
#include <Preferences.h>
#include <esp_now.h>
#include <WiFi.h>
#include <ArduinoOTA.h>
#include <esp_task_wdt.h>
#include "Config.h"
#include "MotorControl.h"
#include "ServoControl.h"
#include "Balance.h"
#include "HeadControl.h"
#include "ObstacleAvoidance.h"
#include "RobotSystem.h"
#include "Navigation.h"
#include "TransformManager.h"
#include "CarModeController.h"
#include "BipedModeController.h"
#include "CrawlerModeController.h"
#include "CommandHandler.h"

#define WDT_TIMEOUT_SECONDS 5
unsigned long lastHeartbeatTime = 0;

// --- Hardware Instances ---
MotorControl car(MOTOR_IN1, MOTOR_IN2, MOTOR_IN3, MOTOR_IN4, MOTOR_ENA, MOTOR_ENB);
ServoControl servos;
Balance balance;
HeadControl head(PAN_SERVO_PIN, TILT_SERVO_PIN);
ObstacleAvoidance obstacle(TRIG_PIN, ECHO_PIN, head);
Preferences prefs;

// --- Decoupled Subsystem / Manager Instances ---
RobotSystem systemMgr(car, balance, obstacle, servos, head);
Navigation nav(car, balance, obstacle, servos, head);

// --- Mode Controllers ---
CarModeController carMode(car, obstacle, balance, nav);
TransformManager transformMgr(servos);
BipedModeController bipedMode(servos, balance, transformMgr);
CrawlerModeController crawlerMode(car, servos);

// --- High-Level Command Router ---
CommandHandler cmdHandler(car, balance, obstacle, servos, nav, systemMgr, head,
                         carMode, bipedMode, crawlerMode, transformMgr);

#include "DiagnosticServer.h"
DiagnosticServer diagServer(car, cmdHandler, obstacle, balance);

struct WiFiSync {
    char ssid[32];
    char pass[64];
};

void onDataReceive(const uint8_t * mac, const uint8_t *incomingData, int len) {
    if (len == sizeof(WiFiSync)) {
        WiFiSync sync;
        memcpy(&sync, incomingData, sizeof(WiFiSync));
        prefs.begin("wifi", false);
        prefs.putString("ssid", sync.ssid);
        prefs.putString("pass", sync.pass);
        prefs.end();
        delay(500);
        ESP.restart();
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial2.begin(SERIAL_BAUD, SERIAL_8N1, COMM_LINK_RX, COMM_LINK_TX); 
    
    #if USE_WDT
    esp_task_wdt_init(WDT_TIMEOUT_SECONDS, true);
    esp_task_wdt_add(NULL);
    #endif

    // 1. WiFi & Sync Init
    prefs.begin("wifi", false);
    String ssid = prefs.getString("ssid", WIFI_SSID);
    String pass = prefs.getString("pass", WIFI_PASS);
    
    WiFi.mode(WIFI_AP_STA);
    if (esp_now_init() == ESP_OK) {
        esp_now_register_recv_cb(onDataReceive);
    }

    #if USE_OTA
    WiFi.begin(ssid.c_str(), pass.c_str());
    ArduinoOTA.setHostname("omni-motion");
    ArduinoOTA.setPassword("omni123");
    
    ArduinoOTA.onStart([]() {
        Serial.println("[OTA] Critical Motion Update Started...");
    });
    
    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        Serial.printf("[OTA] Progress: %u%%\r", (progress / (total / 100)));
    });
    
    ArduinoOTA.begin();
    #endif

    // 2. Hardware & Subsystems Init
    Wire.begin(); 
    car.begin();
    head.begin();
    transformMgr.begin();
    carMode.begin();
    bipedMode.begin();
    crawlerMode.begin();
    diagServer.begin();
    
    #if USE_SERVO_DRIVER
    servos.begin();
    servos.standPosition();
    #endif
    
    #if USE_MPU6050
    if (!balance.begin()) {
        Serial.println("Warning: MPU6050 connection failed.");
        #if USE_I2C_HEALER
        systemMgr.i2cRecovery();
        #endif
    }
    balance.resetYaw();
    #endif
    
    #if USE_ULTRASONIC
    obstacle.begin();
    #endif

    lastHeartbeatTime = millis();
}

void loop() {
    #if USE_WDT
    esp_task_wdt_reset();
    #endif

    #if USE_OTA
    // SAFETY INTERLOCK: Only handle OTA if robot is in a stable/stopped state
    if (cmdHandler.getState() == STATE_STAND || cmdHandler.getState() == STATE_CAR) {
        ArduinoOTA.handle();
    }
    #endif
    
    // 1. Update Sensors & Core Systems
    #if USE_MPU6050
    if (balance.isOnline() && !balance.update() && USE_I2C_HEALER) {
        systemMgr.i2cRecovery();
    }
    #endif
    
    head.update();
    obstacle.update();
    systemMgr.updateTelemetry();
    systemMgr.checkBatterySafety();
    cmdHandler.updateState();
    diagServer.update();

    // 2. Command Processing & Heartbeat Failsafe
    String cmd = "";
    bool hasCmd = false;
    if (Serial2.available()) {
        cmd = Serial2.readStringUntil('\n');
        hasCmd = true;
    } else if (Serial.available()) {
        cmd = Serial.readStringUntil('\n');
        hasCmd = true;
    }

    if (hasCmd) {
        cmd.trim();
        if (cmd.length() > 0) {
            lastHeartbeatTime = millis(); // Refresh safety timer
            
            if (cmd != "BEAT") {
                Serial.println("Exec: " + cmd);
                Serial2.println("ACK:" + cmd); 
                cmdHandler.processCommand(cmd);
            }
        }
    }

    // Safety: No heartbeat for too long? STOP!
    if (millis() - lastHeartbeatTime > HEARTBEAT_TIMEOUT_MS) {
        if (cmdHandler.isMovingForward() || cmdHandler.isTurning()) {
            Serial.println("[FAILSAFE] Comm Link Lost! Emergency Stop.");
            car.emergencyBrake();
            cmdHandler.processCommand("CMD:STOP");
        }
    }
    
    // 3. Autonomy & Safety
    nav.updateActiveScan(cmdHandler.isMovingForward());
    
    // Stall protection
    float vCurr = (analogRead(CURRENT_PIN) / 4095.0) * 3.3;
    float amps = (vCurr - 1.65) / 0.1;
    if (amps > 3.0f) {
        car.emergencyBrake();
        Serial2.println("STATUS: MOTOR STALL!");
    }

    // 4. Mode-Specific execution and updates
    RobotState currentState = cmdHandler.getState();
    
    // Always update active shape transitions
    transformMgr.update();

    #if USE_ULTRASONIC
    // Tilt Compensation (Non-blocking)
    if (currentState != STATE_FALLEN && !transformMgr.isTransitioning() && !obstacle.isScanBusy()) {
        float pitch = balance.getPitch();
        int tiltAdjustment = map(pitch, -45, 45, -30, 30);
        head.setTilt(90 + tiltAdjustment); 
    }
    #endif

    // Route execution to corresponding mode controller
    if (transformMgr.isTransitioning()) {
        car.stop(); // Prevent wheel spinning during transformations
    } else {
        switch (currentState) {
            case STATE_STAND:
            case STATE_WALK:
                bipedMode.update();
                break;
                
            case STATE_CAR:
                carMode.update();
                break;
                
            case STATE_AVOID: {
                carMode.update();
                #if USE_ULTRASONIC
                int frontDistance = obstacle.readFrontDistance();
                int groundDistance = obstacle.readGroundDistance();
                
                if (groundDistance > 45) { // Hole (safety fallback)
                    car.stop(); delay(200);
                    car.moveBackward(); delay(400);
                    car.stop();
                } else if (frontDistance < 25) { // Obstacle
                    car.stop(); delay(200);
                    car.moveBackward(); delay(400);
                    car.stop();
                    if (obstacle.scanLeftBlocking() > obstacle.scanRightBlocking()) car.turnLeft();
                    else car.turnRight();
                    delay(500);
                    car.stop();
                } else {
                    car.moveForward();
                }
                #endif
                break;
            }
            
            case STATE_AVOID_ADVANCED: {
                carMode.update();
                #if USE_ULTRASONIC
                if (nav.isEscaping()) {
                    break;
                }
                int frontDistance = obstacle.readFrontDistance();
                if (frontDistance > SAFE_DISTANCE_CM) { 
                    car.setSpeed(nav.adaptiveForwardSpeed(frontDistance));
                    car.moveForward();
                } else {
                    nav.triggerEscape();
                }
                #endif
                break;
            }
            
            case STATE_CRAWLER:
                crawlerMode.update();
                break;
                
            case STATE_FALLEN:
                bipedMode.update(); // Wait for recovery in biped mode
                break;
                
            case STATE_SUN_SEEK: {
                carMode.update();
                #if USE_ULTRASONIC
                if (obstacle.readFrontDistance() < 25) {
                    car.stop();
                    delay(200);
                    car.turnRight(); delay(500);
                    car.stop();
                } else {
                    car.setSpeed(SPEED_SLOW);
                    car.moveForward();
                }
                #endif
                break;
            }
        }
    }

    delay(5); 
}
