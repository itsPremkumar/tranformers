#include "CommandHandler.h"

CommandHandler::CommandHandler(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, 
                              ServoControl& servos, Navigation& nav, RobotSystem& system)
    : _car(car), _balance(balance), _obstacle(obstacle), _servos(servos), _nav(nav), _system(system) {
    _lastHeartbeatReceived = millis();

    // Set Initial Hardware State based on Profile
    #if CURRENT_HARDWARE_PROFILE == PROFILE_CAR_ONLY
    _currentState = STATE_CAR;
    #elif CURRENT_HARDWARE_PROFILE == PROFILE_BIPED_ONLY
    _currentState = STATE_STAND;
    #elif CURRENT_HARDWARE_PROFILE == PROFILE_CRAWLER_ONLY
    _currentState = STATE_CRAWLER;
    #else
    _currentState = STATE_STAND; // Full Transformer defaults to Stand
    #endif
}

void CommandHandler::processCommand(String cmd) {
    cmd.trim();
    _lastHeartbeatReceived = millis(); 
    
    if (cmd == "BEAT") return; 
    if (cmd == "CMD:TEST") { _system.runSelfTest(); return; }

    if (cmd.startsWith("GOTO:")) {
        int commaIdx = cmd.indexOf(',');
        if (commaIdx > 0) {
            float tx = cmd.substring(5, commaIdx).toFloat();
            float ty = cmd.substring(commaIdx + 1).toFloat();
            _nav.setNavigationTarget(tx, ty);
            Serial.printf("[NAV] New Target Set: %.1f, %.1f\n", tx, ty);
            Serial2.println("STATUS: Navigation Started");
        }
        return;
    }

    if (cmd == "CMD:FORWARD") {
        #if USE_ULTRASONIC
        if (_obstacle.readFrontDistance() > 20) {
            _nav.setTargetSpeeds(SPEED_FAST, SPEED_FAST);
            _currentState = STATE_CAR;
            _isMovingForward = true;
            #if USE_MPU6050
            _targetYaw = _balance.getYaw();
            _isAidingGyro = true;
            #endif
        } else {
            Serial.println("[SAFETY] Blocked Forward move!");
            _nav.setTargetSpeeds(0, 0);
            _isMovingForward = false;
        }
        #else
        _nav.setTargetSpeeds(SPEED_FAST, SPEED_FAST);
        _currentState = STATE_CAR;
        _isMovingForward = true;
        #endif
    } else if (cmd == "CMD:BACKWARD") {
        _nav.setTargetSpeeds(-SPEED_NORMAL, -SPEED_NORMAL);
        _currentState = STATE_CAR;
        _isMovingForward = false;
        _isAidingGyro = false;
    } else if (cmd == "CMD:LEFT") {
        _nav.setTargetSpeeds(-SPEED_TURN, SPEED_TURN);
        _currentState = STATE_CAR;
        _isMovingForward = false;
        _isAidingGyro = false;
    } else if (cmd == "CMD:RIGHT") {
        _nav.setTargetSpeeds(SPEED_TURN, -SPEED_TURN);
        _currentState = STATE_CAR;
        _isMovingForward = false;
        _isAidingGyro = false;
    } else if (cmd == "CMD:RIGHT_PIVOT") {
        _car.turnRightPivot();
        _currentState = STATE_CAR;
        _isMovingForward = false;
    } else if (cmd == "CMD:LEFT_PIVOT_BACK") {
        _car.turnLeftPivotBack();
        _currentState = STATE_CAR;
        _isMovingForward = false;
    } else if (cmd == "CMD:RIGHT_PIVOT_BACK") {
        _car.turnRightPivotBack();
        _currentState = STATE_CAR;
        _isMovingForward = false;
    } else if (cmd == "CMD:LEFT_ZERO") {
        _car.turnLeftZero();
        _currentState = STATE_CAR;
        _isMovingForward = false;
    } else if (cmd == "CMD:RIGHT_ZERO") {
        _car.turnRightZero();
        _currentState = STATE_CAR;
        _isMovingForward = false;
    } else if (cmd == "CMD:STOP") {
        _nav.setTargetSpeeds(0, 0);
        #if CURRENT_HARDWARE_PROFILE == PROFILE_CAR_ONLY
        _currentState = STATE_CAR;
        #else
        _currentState = STATE_STAND;
        #endif
        _isMovingForward = false;
        _isAidingGyro = false;
        _nav.stopNavigation();
    } else if (cmd == "CMD:WALK") {
        #if CURRENT_HARDWARE_PROFILE == PROFILE_OMNI_MORPH || CURRENT_HARDWARE_PROFILE == PROFILE_BIPED_ONLY
        #if ENABLE_WALKING
        _currentState = STATE_WALK;
        _isMovingForward = true;
        #endif
        #endif
    } else if (cmd == "CMD:TRANSFORM") {
        #if CURRENT_HARDWARE_PROFILE == PROFILE_OMNI_MORPH
        #if ENABLE_TRANSFORM
        _servos.transformToCar();
        _currentState = STATE_CAR;
        _isMovingForward = false;
        #endif
        #endif
    } else if (cmd == "CMD:PUSH") {
        _servos.pushMotion();
    } else if (cmd == "CMD:KICK") {
        _servos.kickMotion();
        #if USE_ULTRASONIC
        _currentState = STATE_AVOID;
        #endif
    } else if (cmd == "CMD:CRAWLER") {
        #if CURRENT_HARDWARE_PROFILE == PROFILE_OMNI_MORPH || CURRENT_HARDWARE_PROFILE == PROFILE_CRAWLER_ONLY
        #if ENABLE_TRANSFORM
        _servos.transformToCrawler();
        _currentState = STATE_CRAWLER;
        _isMovingForward = false;
        #endif
        #endif
    } else if (cmd == "CMD:AUTO_ADV") {
        #if USE_ULTRASONIC
        _currentState = STATE_AVOID_ADVANCED;
        #endif
    } else if (cmd.startsWith("PAN:")) {
        _obstacle.setPan(cmd.substring(4).toInt());
    } else if (cmd.startsWith("TILT:")) {
        _obstacle.setTilt(cmd.substring(5).toInt());
    }
}

void CommandHandler::updateState() {
    // 1. Heartbeat Timeout
    if (millis() - _lastHeartbeatReceived > HEARTBEAT_TIMEOUT_MS && _currentState != STATE_STAND) {
        _car.stop();
        _nav.setTargetSpeeds(0, 0);
        #if CURRENT_HARDWARE_PROFILE == PROFILE_CAR_ONLY
        _currentState = STATE_CAR;
        #else
        _currentState = STATE_STAND;
        #endif
    }

    // 2. Gyro Assistance
    if (_isMovingForward && _isAidingGyro) {
        float currentYaw = _balance.getYaw();
        float yawError = currentYaw - _targetYaw;
        int correction = yawError * 4;
        _car.moveForward(correction); // This bypasses smoothing, maybe should adjust targets instead?
                                      // But for now keeping original logic.
    }

    // 3. Fall Detection
    #if USE_MPU6050
    FallDirection fall = _balance.checkFall();
    if (fall != NO_FALL && _currentState != STATE_FALLEN) {
        Serial.println("[IMU] Fall detected!");
        _currentState = STATE_FALLEN;
        _car.stop();
        _nav.setTargetSpeeds(0, 0);
        // We'll need a way to pass fall direction to recoverFromFall in loop
    }
    #endif
}
