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
#include "ObstacleAvoidance.h"
#include "RobotSystem.h"
#include "Navigation.h"
#include "CommandHandler.h"

#define WDT_TIMEOUT_SECONDS 5
unsigned long lastHeartbeatTime = 0;

// --- Hardware Instances ---
MotorControl car(MOTOR_IN1, MOTOR_IN2, MOTOR_IN3, MOTOR_IN4, MOTOR_ENA, MOTOR_ENB);
ServoControl servos;
Balance balance;
ObstacleAvoidance obstacle(TRIG_PIN, ECHO_PIN, PAN_SERVO_PIN, TILT_SERVO_PIN);
Preferences prefs;

// --- Module Instances ---
RobotSystem systemMgr(car, balance, obstacle, servos);
Navigation nav(car, balance, obstacle, servos);
CommandHandler cmdHandler(car, balance, obstacle, servos, nav, systemMgr);

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

    // 2. Hardware Init
    Wire.begin(); 
    car.begin();
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
    if (!balance.update() && USE_I2C_HEALER) {
        systemMgr.i2cRecovery();
    }
    #endif
    
    nav.updateSmoothMotors();
    systemMgr.updateTelemetry();
    systemMgr.checkBatterySafety();
    cmdHandler.updateState();
    #if USE_SERVO_SLEEP
    servos.updateSleep();
    #endif

    // 2. Command Processing & Heartbeat Failsafe
    if (Serial2.available()) {
        String cmd = Serial2.readStringUntil('\n');
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
            car.stop();
            cmdHandler.processCommand("CMD:STOP");
        }
    }
    
    // 3. Autonomy & Safety
    nav.updateActiveScan(cmdHandler.isMovingForward());
    nav.processNavigation(balance.getYaw());
    
    // Stall protection & Stuck detection
    float vCurr = (analogRead(CURRENT_PIN) / 4095.0) * 3.3;
    float amps = (vCurr - 1.65) / 0.1;
    if (amps > 3.0) {
        car.stop();
        Serial2.println("STATUS: MOTOR STALL!");
    }
    nav.checkStuckStatus(amps);

    // 4. State Machine Execution
    RobotState currentState = cmdHandler.getState();
    static bool lastTurnWasLeft = false;

    #if USE_ULTRASONIC
    // Tilt Compensation
    if (currentState != STATE_FALLEN) {
        float pitch = balance.getPitch();
        int tiltAdjustment = map(pitch, -45, 45, -30, 30);
        obstacle.setTilt(90 + tiltAdjustment); 
    }
    #endif

    switch (currentState) {
        case STATE_STAND: break;
        case STATE_CAR: break;
        case STATE_WALK:
            #if ENABLE_WALKING
            servos.walkForward();
            #endif
            break;
        case STATE_AVOID: {
            #if USE_ULTRASONIC
            int frontDistance = obstacle.readFrontDistance();
            int groundDistance = obstacle.readGroundDistance();
            
            if (groundDistance > 45) { // Hole
                car.stop(); delay(200);
                car.moveBackward(); delay(400);
                car.stop();
            } else if (frontDistance < 25) { // Obstacle
                car.stop(); delay(200);
                car.moveBackward(); delay(400);
                car.stop();
                if (obstacle.scanLeft() > obstacle.scanRight()) car.turnLeft();
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
            #if USE_ULTRASONIC
            obstacle.resetHead();
            int frontDistance = obstacle.readFrontDistance();
            if (frontDistance > SAFE_DISTANCE_CM) { 
                car.setSpeed(nav.adaptiveForwardSpeed(frontDistance));
                car.moveForward();
                delay(frontDistance > CAUTION_DISTANCE_CM ? 35 : 45);
            } else {
                nav.escapeObstacle(lastTurnWasLeft);
            }
            #endif
            break;
        }
        case STATE_FALLEN: {
            #if ENABLE_TRANSFORM
            servos.recoverFromFall(balance.checkFall());
            cmdHandler.processCommand("CMD:STOP"); // Reset to stand
            #endif
            break;
        }
        case STATE_CRAWLER: break;
    }

    delay(5); 
}
