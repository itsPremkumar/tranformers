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
#include "DiagnosticServer.h"

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

TaskHandle_t balanceTaskHandle = NULL;
volatile bool balanceOnline = false;

// ==========================================
// Safety & Watchdog Configuration
// ==========================================
#define WDT_TIMEOUT_SECONDS 5
unsigned long lastHeartbeatTime = 0;

// ==========================================
// Hardware Driver Instances
// ==========================================
MotorControl car(MOTOR_IN1, MOTOR_IN2, MOTOR_IN3, MOTOR_IN4, MOTOR_ENA, MOTOR_ENB);
ServoControl servos;
Balance balance;
HeadControl head(PAN_SERVO_PIN, TILT_SERVO_PIN);
ObstacleAvoidance obstacle(TRIG_PIN, ECHO_PIN, head);
Preferences prefs;

// ==========================================
// Subsystem Manager Instances
// ==========================================
RobotSystem systemMgr(car, balance, obstacle, servos, head);
Navigation nav(car, balance, obstacle, servos, head);
TransformManager transformMgr(servos);

// Mode Controllers
CarModeController carMode(car, obstacle, balance, nav);
BipedModeController bipedMode(servos, balance, transformMgr);
CrawlerModeController crawlerMode(car, servos);

// Control Router & Diagnostic Web Server
CommandHandler cmdHandler(car, balance, obstacle, servos, nav, systemMgr, head,
                         carMode, bipedMode, crawlerMode, transformMgr);
DiagnosticServer diagServer(car, cmdHandler, obstacle, balance, head);

// ==========================================
// WiFi Synchronization Setup
// ==========================================
struct WiFiSync {
    char ssid[32];
    char pass[64];
};

void onDataReceive(const uint8_t *mac, const uint8_t *incomingData, int len) {
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

// ==========================================
// Helper Function Declarations
// ==========================================
void updateSensors();
void processSerialCommands();
void checkFailsafes();
void updateRobotStateBehavior(RobotState state);
void balanceTask(void *pvParameters);

// ==========================================
// System Setup
// ==========================================
void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial2.begin(SERIAL_BAUD, SERIAL_8N1, COMM_LINK_RX, COMM_LINK_TX); 
    
    #if USE_WDT
    esp_task_wdt_init(WDT_TIMEOUT_SECONDS, true);
    esp_task_wdt_add(NULL);
    #endif

    // Initialize WiFi credentials (AP + Station Modes)
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

    // Initialize Subsystems & Controllers
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

    // Spawn high-priority FreeRTOS balance task on Core 1 (priority 3, stack 4096)
    xTaskCreatePinnedToCore(
        balanceTask,
        "BalanceTask",
        4096,
        NULL,
        3,
        &balanceTaskHandle,
        1
    );
}

// ==========================================
// Main Execution Loop
// ==========================================
void loop() {
    #if USE_WDT
    esp_task_wdt_reset();
    #endif

    #if USE_OTA
    // Safety check: Only run OTA handler when stationary
    if (cmdHandler.getState() == STATE_STAND || cmdHandler.getState() == STATE_CAR) {
        ArduinoOTA.handle();
    }
    #endif
    
    updateSensors();
    processSerialCommands();
    checkFailsafes();
    updateRobotStateBehavior(cmdHandler.getState());

    delay(5); 
}

// ==========================================
// Helper Function Implementations
// ==========================================

void updateSensors() {
    head.update();
    obstacle.update();
    systemMgr.updateTelemetry();
    systemMgr.checkBatterySafety();
    cmdHandler.updateState();
    diagServer.update();
}

void processSerialCommands() {
    static String rxSerialBuffer;
    static String rxMotionBuffer;
    
    while (Serial2.available()) {
        char c = (char)Serial2.read();
        if (c == '\n') {
            rxMotionBuffer.trim();
            if (rxMotionBuffer.length() > 0) {
                lastHeartbeatTime = millis(); // Refresh safety timeout
                if (rxMotionBuffer != "BEAT") {
                    Serial.println("Exec: " + rxMotionBuffer);
                    Serial2.println("ACK:" + rxMotionBuffer); 
                    cmdHandler.processCommand(rxMotionBuffer);
                }
            }
            rxMotionBuffer = "";
        } else {
            rxMotionBuffer += c;
        }
    }
    
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n') {
            rxSerialBuffer.trim();
            if (rxSerialBuffer.length() > 0) {
                lastHeartbeatTime = millis(); // Refresh safety timeout
                if (rxSerialBuffer != "BEAT") {
                    Serial.println("Exec: " + rxSerialBuffer);
                    Serial2.println("ACK:" + rxSerialBuffer); 
                    cmdHandler.processCommand(rxSerialBuffer);
                }
            }
            rxSerialBuffer = "";
        } else {
            rxSerialBuffer += c;
        }
    }
}

void checkFailsafes() {
    // 1. Comm Link Watchdog
    if (millis() - lastHeartbeatTime > HEARTBEAT_TIMEOUT_MS) {
        if (cmdHandler.isMovingForward() || cmdHandler.isTurning()) {
            Serial.println("[FAILSAFE] Comm Link Lost! Emergency Stop.");
            car.emergencyBrake();
            cmdHandler.processCommand("CMD:STOP");
        }
    }
    
    // 2. Active Sweep Scan
    nav.updateActiveScan(cmdHandler.isMovingForward());
    
    // 3. Current Overload Stall Protection
    float vCurr = (analogRead(CURRENT_PIN) / 4095.0) * 3.3;
    float amps = (vCurr - 1.65) / 0.1;
    if (amps > 3.0f) {
        car.emergencyBrake();
        Serial2.println("STATUS: MOTOR STALL!");
    }
}

void updateRobotStateBehavior(RobotState currentState) {
    transformMgr.update();

    #if USE_ULTRASONIC
    // Non-blocking servo tilt adaptation to stabilize center sensor
    if (currentState != STATE_FALLEN && !transformMgr.isTransitioning() && !obstacle.isScanBusy()) {
        float pitch = balance.getPitch();
        int tiltAdjustment = map(pitch, -45, 45, -30, 30);
        head.setTilt(90 + tiltAdjustment); 
    }
    #endif

    // Route execution to corresponding active mode controller
    if (transformMgr.isTransitioning()) {
        car.stop(); // Block wheel rotation during transforms
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
                
                if (groundDistance > 45) { // Cliff / Hole detected
                    car.stop(); delay(200);
                    car.moveBackward(); delay(400);
                    car.stop();
                } else if (frontDistance < 25) { // Front Obstacle
                    car.stop(); delay(200);
                    car.moveBackward(); delay(400);
                    car.stop();
                    if (obstacle.scanLeftBlocking() > obstacle.scanRightBlocking()) {
                        car.turnLeft();
                    } else {
                        car.turnRight();
                    }
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
                bipedMode.update();
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
}

void balanceTask(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(10); // 100Hz = 10ms
    
    for (;;) {
        #if USE_MPU6050
        bool ok = balance.update();
        balanceOnline = ok && balance.isOnline();
        if (!ok && USE_I2C_HEALER) {
            systemMgr.i2cRecovery();
        }
        #else
        balanceOnline = false;
        #endif
        
        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}
