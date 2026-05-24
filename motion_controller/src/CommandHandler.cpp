#include "CommandHandler.h"
#include "CarModeController.h"
#include "BipedModeController.h"
#include "CrawlerModeController.h"
#include "TransformManager.h"

CommandHandler::CommandHandler(MotorControl& car, Balance& balance, ObstacleAvoidance& obstacle, 
                               ServoControl& servos, Navigation& nav, RobotSystem& system, HeadControl& head,
                               CarModeController& carMode, BipedModeController& bipedMode,
                               CrawlerModeController& crawlerMode, TransformManager& transform)
    : _car(car), _balance(balance), _obstacle(obstacle), _servos(servos), _nav(nav), _system(system), _head(head),
      _carMode(carMode), _bipedMode(bipedMode), _crawlerMode(crawlerMode), _transform(transform) {
    _lastHeartbeatReceived = millis();
    _isMomentary = true;
    _car.setAccelerationLimit(25); // Snappy acceleration by default for momentary mode

    // Set Initial Hardware State based on Profile
    #if CURRENT_HARDWARE_PROFILE == PROFILE_CAR_ONLY
    _currentState = STATE_CAR;
    #elif CURRENT_HARDWARE_PROFILE == PROFILE_BIPED_ONLY
    _currentState = STATE_STAND;
    #elif CURRENT_HARDWARE_PROFILE == PROFILE_CRAWLER_ONLY
    _currentState = STATE_CRAWLER;
    #else
    _currentState = STATE_STAND; 
    #endif
}

void CommandHandler::processCommand(String cmd) {
    cmd.trim();
    if (cmd == "CMD:EMERGENCY_STOP" || cmd == "CMD:STOP") {
        _car.emergencyBrake();
        _nav.stopNavigation();
        _servos.stopAction(); 
        _transform.stopTransition();
        #if CURRENT_HARDWARE_PROFILE == PROFILE_CAR_ONLY
        _currentState = STATE_CAR;
        #else
        _currentState = STATE_STAND;
        #endif
        _isMovingForward = false;
        _isTurning = false;
        _isAidingGyro = false;
        _lastHeartbeatReceived = millis(); 
        return;
    }
    if (cmd == "CMD:FALL_RECOVERY") {
        #if USE_MPU6050
        FallDirection fall = _balance.checkFall();
        if (fall == NO_FALL) {
            fall = UNKNOWN_FALL;
        }
        _transform.recoverFromFall(fall);
        #else
        _transform.recoverFromFall(UNKNOWN_FALL);
        #endif
        _lastHeartbeatReceived = millis(); 
        return;
    }

    _lastHeartbeatReceived = millis(); 
    
    if (cmd == "BEAT") return; 
    if (cmd == "CMD:TEST") { _system.runSelfTest(); return; }

    // Configuration Commands for Control Modes
    if (cmd == "CMD:MODE_MOMENTARY") {
        _isMomentary = true;
        _car.setAccelerationLimit(25); // Snappy response for momentary taps
        Serial.println("[SYSTEM] Mode changed to MOMENTARY");
        return;
    }
    if (cmd == "CMD:MODE_LATCHING") {
        _isMomentary = false;
        _car.setAccelerationLimit(10); // Smooth ramping for continuous cruise
        Serial.println("[SYSTEM] Mode changed to LATCHING");
        return;
    }

    // Speed Preset Selection & Variable Speed Slider Commands
    if (cmd.startsWith("CMD:SPEED=")) {
        int val = cmd.substring(10).toInt();
        _car.setSpeed(constrain(val, 0, 255));
        Serial.println("[SYSTEM] Speed updated to: " + String(_car.getSpeed()));
        return;
    }
    if (cmd.startsWith("CMD:ACCEL=")) {
        int val = cmd.substring(10).toInt();
        _car.setAccelerationLimit(constrain(val, 1, 50));
        Serial.println("[SYSTEM] Acceleration Limit updated to: " + String(_car.getAccelerationLimit()));
        return;
    }
    if (cmd == "CMD:SPEED_SLOW") {
        _car.setSpeed(SPEED_SLOW);
        Serial.println("[SYSTEM] Speed set to SLOW");
        return;
    }
    if (cmd == "CMD:SPEED_NORMAL") {
        _car.setSpeed(SPEED_NORMAL);
        Serial.println("[SYSTEM] Speed set to NORMAL");
        return;
    }
    if (cmd == "CMD:SPEED_FAST") {
        _car.setSpeed(SPEED_FAST);
        Serial.println("[SYSTEM] Speed set to FAST");
        return;
    }

    // Shape-Shifting & Mode Selection Commands
    if (cmd == "CMD:TRANSFORM") {
        #if CURRENT_HARDWARE_PROFILE == PROFILE_OMNI_MORPH
        #if ENABLE_TRANSFORM
        _transform.transformToCar(); 
        _currentState = STATE_CAR;
        _isMovingForward = false;
        _isTurning = false;
        #endif
        #endif
        return;
    } 
    
    if (cmd == "CMD:CRAWLER") {
        #if CURRENT_HARDWARE_PROFILE == PROFILE_OMNI_MORPH || CURRENT_HARDWARE_PROFILE == PROFILE_CRAWLER_ONLY
        #if ENABLE_TRANSFORM
        _transform.transformToCrawler(); 
        _currentState = STATE_CRAWLER;
        _isMovingForward = false;
        _isTurning = false;
        #endif
        #endif
        return;
    }

    if (cmd == "CMD:STOP") {
        if (_isMomentary) {
            _car.emergencyBrake(); // Lock wheels instantly in momentary mode
        } else {
            _car.stop(); // Glide to a stop in latching mode to protect gears
        }
        _nav.stopNavigation();
        _servos.stopAction(); 
        _transform.stopTransition();
        
        #if CURRENT_HARDWARE_PROFILE == PROFILE_CAR_ONLY
        _currentState = STATE_CAR;
        #else
        _currentState = STATE_STAND;
        #endif
        
        _isMovingForward = false;
        _isTurning = false;
        _isAidingGyro = false;
        return;
    }

    // Waypoint Navigation target setting
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

    if (cmd == "CMD:CALIBRATE_YAW") {
        #if USE_MPU6050
        _targetYaw = _balance.getYaw();
        Serial.println("[SYSTEM] Gyro Yaw calibrated. New target: " + String(_targetYaw));
        #endif
        return;
    }

    // Route command to the corresponding active controller first
    bool handled = false;
    if (_currentState == STATE_CAR || _currentState == STATE_AVOID || _currentState == STATE_AVOID_ADVANCED) {
        handled = _carMode.handleCommand(cmd);
        if (handled) {
            _isMovingForward = (cmd == "CMD:FORWARD");
            _isTurning = (cmd == "CMD:LEFT" || cmd == "CMD:RIGHT" || cmd.indexOf("PIVOT") >= 0 || cmd.indexOf("ZERO") >= 0);
            
            #if USE_MPU6050
            if (cmd == "CMD:FORWARD" || cmd == "CMD:BACKWARD") {
                _targetYaw = _balance.getYaw();
                _isAidingGyro = true;
            } else {
                _isAidingGyro = false;
            }
            #endif
        }
    } else if (_currentState == STATE_WALK || _currentState == STATE_STAND) {
        handled = _bipedMode.handleCommand(cmd);
        if (handled) {
            if (cmd == "CMD:WALK") {
                _currentState = STATE_WALK;
                _isMovingForward = true;
                _isTurning = false;
            }
        }
    } else if (_currentState == STATE_CRAWLER) {
        handled = _crawlerMode.handleCommand(cmd);
        if (handled) {
            _isMovingForward = (cmd == "CMD:FORWARD");
            _isTurning = (cmd == "CMD:LEFT" || cmd == "CMD:RIGHT");
        }
    }

    if (handled) return;

    // Fallbacks for general sensor control commands
    if (cmd == "CMD:AUTO_ADV") {
        #if USE_ULTRASONIC
        _currentState = STATE_AVOID_ADVANCED;
        #endif
    } else if (cmd.startsWith("PAN:") || cmd.startsWith("CMD:PAN:")) {
        int idx = cmd.indexOf(':');
        _head.setPan(cmd.substring(idx + 1).toInt());
    } else if (cmd.startsWith("TILT:") || cmd.startsWith("CMD:TILT:")) {
        int idx = cmd.indexOf(':');
        _head.setTilt(cmd.substring(idx + 1).toInt());
    } else if (cmd == "CMD:SUN_SEEK") {
        _currentState = STATE_SUN_SEEK;
        _isMovingForward = true;
        _isTurning = false;
    }
}

void CommandHandler::updateState() {
    // 1. Heartbeat Timeout
    if (millis() - _lastHeartbeatReceived > HEARTBEAT_TIMEOUT_MS && _currentState != STATE_STAND) {
        _car.emergencyBrake();
        #if CURRENT_HARDWARE_PROFILE == PROFILE_CAR_ONLY
        _currentState = STATE_CAR;
        #else
        _currentState = STATE_STAND;
        #endif
    }

    // 2. Gyro Assistance (Course Locking with shortest-path wrap-around correction)
    if (_isAidingGyro) {
        #if USE_MPU6050
        float currentYaw = _balance.getYaw();
        float yawError = currentYaw - _targetYaw;
        
        // Normalize error to shortest path (-180 to 180 degrees)
        while (yawError > 180.0f) yawError -= 360.0f;
        while (yawError < -180.0f) yawError += 360.0f;
        
        int correction = yawError * 4;
        if (_isMovingForward) {
            _car.moveForward(correction);
        } else {
            _car.moveBackward(correction);
        }
        #endif
    }

    // 3. Fall Detection is handled by BipedModeController only when in Stand/Walk configuration
}
