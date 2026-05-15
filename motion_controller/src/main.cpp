#include <Arduino.h>
#include <Preferences.h>
#include <esp_now.h>
#include "Config.h"
#include "MotorControl.h"
#include "ServoControl.h"
#include "Balance.h"
#include "ObstacleAvoidance.h"
#include <WiFi.h>
#include <ArduinoOTA.h>

struct WiFiSync {
    char ssid[32];
    char pass[64];
};

Preferences prefs;

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

// --- ADVANCED SELF-HEALING: I2C BUS RECOVERY ---
void i2cRecovery() {
    Serial.println("[HEAL] I2C Bus Lock detected. Clearing bus...");
    pinMode(SDA, INPUT_PULLUP);
    pinMode(SCL, OUTPUT);
    for (int i = 0; i < 10; i++) {
        digitalWrite(SCL, LOW); delayMicroseconds(5);
        digitalWrite(SCL, HIGH); delayMicroseconds(5);
    }
    Wire.begin();
}

// --- ADVANCED SELF-HEALING: STUCK DETECTION ---
void checkStuckStatus(float amps) {
    static unsigned long moveStartTime = 0;
    static bool wasMoving = false;
    
    // Simple check: are we trying to move?
    if (car.getSpeed() > 0) {
        if (!wasMoving) moveStartTime = millis();
        wasMoving = true;
        
        if (millis() - moveStartTime > 3000) {
            // If speed is high but IMU shows zero movement, we are stuck!
            if (abs(balance.getAccelX()) < 0.05 && amps > 0.5) {
                Serial2.println("STATUS: I am stuck! Trying escape maneuver...");
                car.stop();
                delay(500);
                car.moveBackward(150); delay(1000);
                car.turnLeft(180); delay(800);
                car.stop();
                moveStartTime = millis(); // Reset
            }
        }
    } else {
        wasMoving = false;
    }
}
ServoControl servos;
Balance balance;
ObstacleAvoidance obstacle(TRIG_PIN, ECHO_PIN, PAN_SERVO_PIN, TILT_SERVO_PIN);

enum RobotState {
    STATE_STAND,
    STATE_WALK,
    STATE_CAR,
    STATE_AVOID,
    STATE_AVOID_ADVANCED,
    STATE_FALLEN,
    STATE_CRAWLER
};

RobotState currentState = STATE_STAND;
bool isMovingForward = false; 
bool lastTurnWasLeft = false;
float targetYaw = 0;
bool isAidingGyro = false;
unsigned long lastHeartbeatReceived = 0;
const unsigned long HEARTBEAT_TIMEOUT = 2500; // 2.5 seconds

void runSelfTest() {
    Serial.println("\n[DIAGNOSTICS] Starting Full System Test...");
    
    // 1. I2C Bus Check
    #if USE_SERVO_DRIVER
    Wire.beginTransmission(0x40); // PCA9685
    if (Wire.endTransmission() == 0) Serial.println("[PASS] PCA9685 Driver Found.");
    else Serial.println("[FAIL] PCA9685 Driver Not Responding!");
    #endif

    #if USE_MPU6050
    Wire.beginTransmission(0x68); // MPU6050
    if (Wire.endTransmission() == 0) Serial.println("[PASS] MPU6050 Sensor Found.");
    else Serial.println("[FAIL] MPU6050 Sensor Not Responding!");
    #endif

    // 2. Ultrasonic Check
    #if USE_ULTRASONIC
    int dist = obstacle.readFrontDistance();
    if (dist > 0 && dist < 400) Serial.println("[PASS] Ultrasonic Sensor: " + String(dist) + "cm");
    else Serial.println("[FAIL] Ultrasonic Sensor Reading Invalid!");
    #endif

    // 3. Servo Sweep
    Serial.println("[TEST] Sweeping Head Servos...");
    obstacle.setPan(45); delay(300);
    obstacle.setPan(135); delay(300);
    obstacle.setPan(90);
    Serial.println("[PASS] Servo Sweep Complete.");

    // 4. Motor & IMU Movement Test
    Serial.println("[TEST] Testing Motors & Accelerometer...");
    #if USE_MPU6050
    float startAccX = balance.getPitch(); 
    #endif
    car.moveForward();
    delay(400);
    car.stop();
    #if USE_MPU6050
    float endAccX = balance.getPitch();
    if (abs(endAccX - startAccX) > 0.01) Serial.println("[PASS] Motor Movement Detected (IMU).");
    else Serial.println("[FAIL] No IMU Movement Detected!");
    #endif

    Serial.println("[DIAGNOSTICS] System Test Complete.\n");
}

void processCommand(String cmd) {
    cmd.trim();
    lastHeartbeatReceived = millis(); 
    
    if (cmd == "BEAT") return; 
    if (cmd == "CMD:TEST") { runSelfTest(); return; }

    if (cmd == "CMD:FORWARD") {
        #if USE_ULTRASONIC
        if (obstacle.readFrontDistance() > 20) {
            car.moveForward();
            currentState = STATE_CAR;
            isMovingForward = true;
            #if USE_MPU6050
            targetYaw = balance.getYaw();
            isAidingGyro = true;
            #endif
        } else {
            Serial.println("[SAFETY] Blocked Forward move: Object too close!");
            car.stop();
            isMovingForward = false;
        }
        #else
        car.moveForward();
        currentState = STATE_CAR;
        isMovingForward = true;
        #if USE_MPU6050
        targetYaw = balance.getYaw();
        isAidingGyro = true;
        #endif
        #endif
    } else if (cmd == "CMD:BACKWARD") {
        car.moveBackward();
        currentState = STATE_CAR;
        isMovingForward = false;
        isAidingGyro = false;
    } else if (cmd == "CMD:LEFT") {
        car.turnLeft();
        currentState = STATE_CAR;
        isMovingForward = false;
        isAidingGyro = false;
    } else if (cmd == "CMD:RIGHT") {
        car.turnRight();
        currentState = STATE_CAR;
        isMovingForward = false;
        isAidingGyro = false;
    } else if (cmd == "CMD:LEFT_PIVOT") {
        car.turnLeftPivot();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:RIGHT_PIVOT") {
        car.turnRightPivot();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:LEFT_PIVOT_BACK") {
        car.turnLeftPivotBack();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:RIGHT_PIVOT_BACK") {
        car.turnRightPivotBack();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:LEFT_ZERO") {
        car.turnLeftZero();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:RIGHT_ZERO") {
        car.turnRightZero();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:STOP") {
        car.stop();
        currentState = STATE_STAND;
        isMovingForward = false;
        isAidingGyro = false;
    } else if (cmd == "CMD:WALK") {
        #if ENABLE_WALKING
        currentState = STATE_WALK;
        isMovingForward = true; // Assuming walk is forward by default
        #endif
    } else if (cmd == "CMD:TRANSFORM") {
        #if ENABLE_TRANSFORM
        servos.transformToCar();
        currentState = STATE_CAR;
        isMovingForward = false;
        #endif
    } else if (cmd == "CMD:PUSH") {
        servos.pushMotion();
    } else if (cmd == "CMD:KICK") {
        servos.kickMotion();
        #if USE_ULTRASONIC
        currentState = STATE_AVOID;
        #endif
    } else if (cmd == "CMD:CRAWLER") {
        #if ENABLE_TRANSFORM
        servos.transformToCrawler();
        currentState = STATE_CRAWLER;
        isMovingForward = false;
        #endif
    } else if (cmd == "CMD:AUTO_ADV") {
        #if USE_ULTRASONIC
        currentState = STATE_AVOID_ADVANCED;
        #endif
    } else if (cmd.startsWith("PAN:")) {
        obstacle.setPan(cmd.substring(4).toInt());
    } else if (cmd.startsWith("TILT:")) {
        obstacle.setTilt(cmd.substring(5).toInt());
    }
}

int adaptiveForwardSpeed(int distance) {
    if (distance > 85) return 190; // SPEED_FORWARD
    if (distance > SAFE_DISTANCE_CM) return 165; // SPEED_CRUISE
    return 135; // SPEED_SLOW
}

void escapeObstacle() {
    car.stop();
    delay(100);

    car.moveBackward();
    delay(REVERSE_TIME_MS); // REVERSE_TIME_MS
    car.stop();
    delay(100);

    // 1. Quick Scan
    ScanResult best = obstacle.quickScan();

    // 2. Fallback to Deep Scan if needed
    if (best.distance < CAUTION_DISTANCE_CM) { // CAUTION_DISTANCE_CM
        Serial.println("Quick scan failed, initiating DEEP scan...");
        best = obstacle.deepScan();
    }

    // 3. Severe escape for dead ends
    if (best.distance < BLOCK_DISTANCE_CM || obstacle.allDirectionsBlocked()) {
        Serial.println("Dead-end detected -> stronger escape turn");
        if (lastTurnWasLeft) {
            car.setSpeed(185); // SPEED_TURN
            car.turnRight();
            delay(700);
            lastTurnWasLeft = false;
        } else {
            car.setSpeed(185); // SPEED_TURN
            car.turnLeft();
            delay(700);
            lastTurnWasLeft = true;
        }
        car.stop();
        delay(100);
        obstacle.resetHead();
        return;
    }

    // 4. Normal turn toward best path
    int delta = best.pan - 90; // PAN_CENTER
    int turnMs = map(constrain(abs(delta), 0, 90), 0, 90, TURN_BASE_MS_MIN, TURN_BASE_MS_MAX);

    if (abs(delta) <= 10) {
        car.setSpeed(135);
        car.moveForward();
        delay(220);
        car.stop();
        obstacle.resetHead();
        return;
    }

    car.setSpeed(185);
    if (delta < 0) {
        car.turnLeft();
        delay(turnMs);
        lastTurnWasLeft = true;
    } else {
        car.turnRight();
        delay(turnMs);
        lastTurnWasLeft = false;
    }
    car.stop();
    delay(90);
    obstacle.resetHead();
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial2.begin(SERIAL_BAUD, SERIAL_8N1, COMM_LINK_RX, COMM_LINK_TX); 
    
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
    ArduinoOTA.setHostname("Omni-Motion");
    ArduinoOTA.begin();
    #endif

    // 2. Hardware Init (Preserved)
    Wire.begin(); 
    car.begin();
    #if USE_SERVO_DRIVER
    servos.begin();
    #endif
    
    #if USE_MPU6050
    if (!balance.begin()) {
        Serial.println("Warning: MPU6050 connection failed.");
    }
    #endif
    
    #if USE_ULTRASONIC
    obstacle.begin();
    #endif
    
    #if USE_SERVO_DRIVER
    servos.standPosition();
    #endif

    balance.resetYaw();
    lastHeartbeatReceived = millis();
}

unsigned long lastTelemetryUpdate = 0;
const int TELEMETRY_INTERVAL = 500; // 500ms

void loop() {
    static unsigned long lastBatteryCheck = 0;
    static bool batteryCritical = false;
    static unsigned long lastSensorFusion = 0;
    static FallDirection lastFall = NO_FALL;

    // 1. SELF-HEALING: Battery Safety & Auto-Sleep
    int batRaw = analogRead(BATTERY_PIN);
    float voltage = (batRaw / 4095.0) * 3.3 * 4.0; // 1:4 voltage divider check
    if (voltage < 6.4 && voltage > 1.0) { // 6.4V is safety for 2S LiPo
        Serial2.println("CMD:BATTERY_CRITICAL");
        Serial.println("[HEAL] CRITICAL BATTERY! Entering Deep Sleep to protect hardware...");
        car.stop();
        #if USE_SERVO_DRIVER
        servos.standPosition();
        #endif
        delay(2000);
        esp_deep_sleep_start();
    }

    #if USE_OTA
    ArduinoOTA.handle();
    #endif

    #if USE_MPU6050
    balance.update();
    
    // Auto Fall Detection and Recovery
    FallDirection fall = balance.checkFall();
    if (fall != NO_FALL && currentState != STATE_FALLEN) {
        Serial.println("[IMU] Fall detected! Transitioning to STATE_FALLEN");
        currentState = STATE_FALLEN;
        lastFall = fall;
        car.stop();
    }
    #endif
    
    // --- PERIODIC TELEMETRY ---
    if (millis() - lastTelemetryUpdate > TELEMETRY_INTERVAL) {
        #if USE_ULTRASONIC
        int dist = obstacle.readFrontDistance();
        Serial.println("DISTANCE:" + String(dist));
        #endif
        
        // Battery Monitoring (Assuming 3.3V ADC and voltage divider)
        float vBat = (analogRead(BATTERY_PIN) / 4095.0) * 3.3 * 2.0; // Multiplier depends on divider
        Serial.println("BATTERY:" + String(vBat, 2));
        
        // Current Monitoring (Assuming ACS712 or shunt)
        float vCurr = (analogRead(CURRENT_PIN) / 4095.0) * 3.3;
        float amps = (vCurr - 1.65) / 0.1; // Offset and sensitivity depends on sensor
        Serial.println("CURRENT:" + String(amps, 2));
        Serial.println("ROUGHNESS:" + String(balance.getTerrainRoughness(), 4));
        Serial.println("YAW:" + String(balance.getYaw(), 2));
        
        lastTelemetryUpdate = millis();

        // Smart Battery Check
        if (millis() - lastBatteryCheck > 5000) { // Check every 5 seconds
            float vBat = (analogRead(BATTERY_PIN) / 4095.0) * 3.3 * 2.0;
            if (vBat < 6.4) {
                Serial2.println("CMD:BATTERY_CRITICAL");
                batteryCritical = true;
                car.stop();
            } else if (vBat < 6.8) {
                Serial2.println("CMD:BATTERY_LOW");
            }
            lastBatteryCheck = millis();
        }
    }
    
    // 3. Command Processing with ACKs
    if (Serial2.available()) {
        String cmd = Serial2.readStringUntil('\n');
        cmd.trim();
        if (cmd.length() > 0) {
            Serial.println("Exec: " + cmd);
            Serial2.println("ACK:" + cmd); 
            processCommand(cmd);
        }
    }
    
    // 4. Telemetry & Safety
    float amps = (analogRead(CURRENT_PIN) / 4095.0) * 3.3 / 0.1; 
    if (amps > 3.0) { // Stall protection
        car.stop();
        Serial2.println("STATUS: MOTOR STALL! Emergency Stop.");
    }
    checkStuckStatus(amps);

    if (millis() - lastHeartbeatReceived > HEARTBEAT_TIMEOUT_MS && currentState != STATE_STAND) {
        car.stop();
        currentState = STATE_STAND;
    }
    

    // --- DYNAMIC OBSTACLE AVOIDANCE ---
    #if USE_ULTRASONIC
    // Tilt Compensation: Keep eyes level if robot is tilted
    if (currentState != STATE_FALLEN) {
        float pitch = balance.getPitch();
        int tiltAdjustment = map(pitch, -45, 45, -30, 30);
        obstacle.setTilt(90 + tiltAdjustment); 
    }

    if (isMovingForward && (currentState == STATE_CAR || currentState == STATE_WALK)) {
        if (obstacle.readFrontDistance() < 20) {
            Serial.println("[SAFETY] Emergency Stop: Obstacle detected while moving!");
            car.stop();
            isMovingForward = false;
            if (currentState == STATE_CAR) currentState = STATE_STAND;
        }
    }
    #endif

    // Gyro-Assisted Straight Driving
    if (isMovingForward && isAidingGyro) {
        float currentYaw = balance.getYaw();
        float yawError = currentYaw - targetYaw;
        int correction = yawError * 4; // Kp = 4
        car.moveForward(correction);
    }
    
    // Memory Decay and Non-Blocking Cliff Check
    #if USE_ULTRASONIC
    obstacle.decayMemoryIfNeeded();
    static unsigned long lastCliffCheck = 0;
    static bool cliffRisk = false;
    if (millis() - lastCliffCheck > 1000) {
        cliffRisk = obstacle.detectCliffOrDrop();
        lastCliffCheck = millis();
    }

    if (cliffRisk && currentState == STATE_AVOID_ADVANCED) {
        Serial.println("Cliff / drop risk detected -> stopping");
        car.stop();
        delay(100);
        car.moveBackward();
        delay(260);
        car.stop();
        delay(80);
        car.turnRight();
        delay(500);
        car.stop();
        obstacle.resetHead();
        cliffRisk = false; 
        return;
    }
    #endif
    
    switch (currentState) {
        case STATE_STAND: break;
        case STATE_WALK:
            #if ENABLE_WALKING
            servos.walkForward();
            #endif
            break;
        case STATE_CAR: break;
        case STATE_AVOID: {
            #if USE_ULTRASONIC
            int frontDistance = obstacle.readFrontDistance();
            int groundDistance = obstacle.readGroundDistance();
            
            if (groundDistance > 45) {
                // Hole detected
                car.stop();
                delay(200);
                car.moveBackward();
                delay(400);
                car.stop();
            } else if (frontDistance < 25) {
                // Obstacle detected
                car.stop();
                delay(200);
                car.moveBackward();
                delay(400);
                car.stop();
                
                int leftDist = obstacle.scanLeft();
                int rightDist = obstacle.scanRight();
                
                if (leftDist > rightDist) {
                    car.turnLeft();
                    delay(500);
                } else {
                    car.turnRight();
                    delay(500);
                }
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
                int speed = adaptiveForwardSpeed(frontDistance);
                car.setSpeed(speed);
                car.moveForward();
                delay(frontDistance > CAUTION_DISTANCE_CM ? 35 : 45);
            } else {
                escapeObstacle();
            }
            #endif
            break;
        }
        case STATE_FALLEN: {
            #if ENABLE_TRANSFORM
            servos.recoverFromFall(lastFall);
            currentState = STATE_STAND;
            #endif
            break;
        }
    }
    delay(5); // Small yield for watchdog
}
