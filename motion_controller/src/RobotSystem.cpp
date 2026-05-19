#include "RobotSystem.h"

RobotSystem::RobotSystem(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, ServoControl& servos) 
    : _car(car), _balance(balance), _obstacle(obstacle), _servos(servos) {}

void RobotSystem::i2cRecovery() {
    Serial.println("[HEAL] I2C Bus Lock detected. Clearing bus...");
    pinMode(SDA, INPUT_PULLUP);
    pinMode(SCL, OUTPUT);
    for (int i = 0; i < 10; i++) {
        digitalWrite(SCL, LOW); delayMicroseconds(5);
        digitalWrite(SCL, HIGH); delayMicroseconds(5);
    }
    Wire.begin();
}

void RobotSystem::runSelfTest() {
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
    int dist = _obstacle.readFrontDistance();
    if (dist > 0 && dist < 400) Serial.println("[PASS] Ultrasonic Sensor: " + String(dist) + "cm");
    else Serial.println("[FAIL] Ultrasonic Sensor Reading Invalid!");
    #endif

    // 3. Servo Sweep
    Serial.println("[TEST] Sweeping Head Servos...");
    _obstacle.setPan(45); delay(300);
    _obstacle.setPan(135); delay(300);
    _obstacle.setPan(90);
    Serial.println("[PASS] Servo Sweep Complete.");

    // 4. Motor & IMU Movement Test
    Serial.println("[TEST] Testing Motors & Accelerometer...");
    #if USE_MPU6050
    float startAccX = _balance.getPitch(); 
    #endif
    _car.moveForward();
    delay(400);
    _car.stop();
    #if USE_MPU6050
    float endAccX = _balance.getPitch();
    if (abs(endAccX - startAccX) > 0.01) Serial.println("[PASS] Motor Movement Detected (IMU).");
    else Serial.println("[FAIL] No IMU Movement Detected!");
    #endif

    Serial.println("[DIAGNOSTICS] System Test Complete.\n");
}

void RobotSystem::updateTelemetry() {
    if (millis() - _lastTelemetryUpdate > TELEMETRY_INTERVAL) {
        #if USE_ULTRASONIC
        int dist = _obstacle.readFrontDistance();
        Serial2.println("DISTANCE:" + String(dist));
        #endif
        
        float vBat = (analogRead(BATTERY_PIN) / 4095.0) * 3.3 * BATTERY_MULTIPLIER;
        Serial2.println("BATTERY:" + String(vBat, 2));
        
        float vCurr = (analogRead(CURRENT_PIN) / 4095.0) * 3.3;
        float amps = (vCurr - 1.65) / 0.1;
        Serial2.println("CURRENT:" + String(amps, 2));
        Serial2.println("ROUGHNESS:" + String(_balance.getTerrainRoughness(), 4));
        Serial2.println("YAW:" + String(_balance.getYaw(), 2));
        
        _lastTelemetryUpdate = millis();
    }
}

void RobotSystem::checkBatterySafety() {
    if (millis() - _lastBatteryCheck > 5000) {
        int batRaw = analogRead(BATTERY_PIN);
        float voltage = (batRaw / 4095.0) * 3.3 * BATTERY_MULTIPLIER;
        
        if (voltage < 6.4 && voltage > 1.0) {
            Serial2.println("CMD:BATTERY_CRITICAL");
            Serial.println("[HEAL] CRITICAL BATTERY!");
            #if CURRENT_HARDWARE_PROFILE != PROFILE_CAR_ONLY
            Serial.println("[HEAL] Entering Deep Sleep...");
            _car.stop();
            #if USE_SERVO_DRIVER
            _servos.standPosition();
            #endif
            delay(2000);
            esp_deep_sleep_start();
            #else
            Serial.println("[HEAL] Deep Sleep skipped for Car Profile.");
            #endif
        } else if (voltage < 6.8) {
            Serial2.println("CMD:BATTERY_LOW");
        }
        _lastBatteryCheck = millis();
    }
}
