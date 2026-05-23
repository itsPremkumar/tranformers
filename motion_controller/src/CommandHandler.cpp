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
    _lastHeartbeatReceived = millis(); 
    
    if (cmd == "BEAT") return; 
    if (cmd == "CMD:TEST") { _system.runSelfTest(); return; }

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
        _car.stop();
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

    // Route command to the corresponding active controller first
    bool handled = false;
    if (_currentState == STATE_CAR || _currentState == STATE_AVOID || _currentState == STATE_AVOID_ADVANCED) {
        handled = _carMode.handleCommand(cmd);
        if (handled) {
            _isMovingForward = (cmd == "CMD:FORWARD");
            _isTurning = (cmd == "CMD:LEFT" || cmd == "CMD:RIGHT" || cmd.indexOf("PIVOT") >= 0 || cmd.indexOf("ZERO") >= 0);
            
            #if USE_MPU6050
            if (cmd == "CMD:FORWARD") {
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
    } else if (cmd.startsWith("PAN:")) {
        _head.setPan(cmd.substring(4).toInt());
    } else if (cmd.startsWith("TILT:")) {
        _head.setTilt(cmd.substring(5).toInt());
    } else if (cmd == "CMD:SUN_SEEK") {
        _currentState = STATE_SUN_SEEK;
        _isMovingForward = true;
        _isTurning = false;
    }
}

void CommandHandler::updateState() {
    // 1. Heartbeat Timeout
    if (millis() - _lastHeartbeatReceived > HEARTBEAT_TIMEOUT_MS && _currentState != STATE_STAND) {
        _car.stop();
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
        _car.moveForward(correction);
    }

    // 3. Fall Detection is handled by BipedModeController only when in Stand/Walk configuration
}
