#include <Arduino.h>
#include "Config.h"
#include "MotorControl.h"
#include "ServoControl.h"
#include "Balance.h"
#include "ObstacleAvoidance.h"

MotorControl car(MOTOR_IN1, MOTOR_IN2, MOTOR_IN3, MOTOR_IN4, MOTOR_ENA, MOTOR_ENB);
ServoControl servos;
Balance balance;
ObstacleAvoidance obstacle(TRIG_PIN, ECHO_PIN, PAN_SERVO_PIN, TILT_SERVO_PIN);

enum RobotState {
    STATE_STAND,
    STATE_WALK,
    STATE_CAR,
    STATE_AVOID,
    STATE_FALLEN
};

RobotState currentState = STATE_STAND;
bool isMovingForward = false; 

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
        } else {
            Serial.println("[SAFETY] Blocked Forward move: Object too close!");
            car.stop();
            isMovingForward = false;
        }
        #else
        car.moveForward();
        currentState = STATE_CAR;
        isMovingForward = true;
        #endif
    } else if (cmd == "CMD:BACKWARD") {
        car.moveBackward();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:LEFT") {
        car.turnLeft();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:RIGHT") {
        car.turnRight();
        currentState = STATE_CAR;
        isMovingForward = false;
    } else if (cmd == "CMD:STOP") {
        car.stop();
        currentState = STATE_STAND;
        isMovingForward = false;
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
    } else if (cmd == "CMD:AUTO") {
        #if USE_ULTRASONIC
        currentState = STATE_AVOID;
        #endif
    } else if (cmd.startsWith("PAN:")) {
        obstacle.setPan(cmd.substring(4).toInt());
    } else if (cmd.startsWith("TILT:")) {
        obstacle.setTilt(cmd.substring(5).toInt());
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial2.begin(SERIAL_BAUD, SERIAL_8N1, COMM_LINK_RX, COMM_LINK_TX); 
    
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
    lastHeartbeatReceived = millis();
}

unsigned long lastTelemetryUpdate = 0;
const int TELEMETRY_INTERVAL = 500; // 500ms

void loop() {
    #if USE_MPU6050
    balance.update();
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
        
        lastTelemetryUpdate = millis();
    }
    
    if (Serial2.available()) {
        String cmd = Serial2.readStringUntil('\n');
        processCommand(cmd);
    }
    
    if (millis() - lastHeartbeatReceived > HEARTBEAT_TIMEOUT_MS && currentState != STATE_STAND) {
        car.stop();
        currentState = STATE_STAND;
    }
    
    #if USE_MPU6050
    FallDirection fall = balance.checkFall();
    if (fall != NO_FALL) {
        car.stop();
        currentState = STATE_FALLEN;
        isMovingForward = false;
    }
    #endif

    // --- DYNAMIC OBSTACLE AVOIDANCE ---
    #if USE_ULTRASONIC
    if (isMovingForward && (currentState == STATE_CAR || currentState == STATE_WALK)) {
        if (obstacle.readFrontDistance() < 20) {
            Serial.println("[SAFETY] Emergency Stop: Obstacle detected while moving!");
            car.stop();
            isMovingForward = false;
            if (currentState == STATE_CAR) currentState = STATE_STAND;
        }
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
        case STATE_FALLEN: break;
    }
    delay(5); // Small yield for watchdog
}
