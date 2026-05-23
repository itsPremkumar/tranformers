#include "CarModeController.h"
#include "Config.h"

CarModeController::CarModeController(MotorControl& car, ObstacleAvoidance& obstacle, Balance& balance, Navigation& nav)
    : _car(car), _obstacle(obstacle), _balance(balance), _nav(nav) {}

void CarModeController::begin() {
    _car.stop();
}

void CarModeController::update() {
    // 1. Always update motor ramping speeds
    _car.update();
    
    // 2. Always update the escape state machine if active
    if (_nav.isEscaping()) {
        _nav.updateEscape();
        return;
    }
    
    // 3. Update Waypoint Navigation if active
    if (_nav.isNavigating()) {
        _nav.processNavigation(_balance.getYaw());
        
        // Measure current for stuck detection
        float vCurr = (analogRead(CURRENT_PIN) / 4095.0) * 3.3;
        float amps = (vCurr - 1.65) / 0.1;
        _nav.checkStuckStatus(amps);
    }
}

bool CarModeController::handleCommand(const String& cmd) {
    if (cmd == "CMD:FORWARD") {
        #if USE_ULTRASONIC
        if (_obstacle.readFrontDistance() > 20) {
            _nav.setTargetSpeeds(SPEED_FAST, SPEED_FAST);
        } else {
            Serial.println("[CAR] Obstacle blocked forward movement!");
            _car.stop();
        }
        #else
        _nav.setTargetSpeeds(SPEED_FAST, SPEED_FAST);
        #endif
        return true;
    } 
    
    if (cmd == "CMD:BACKWARD") {
        _nav.setTargetSpeeds(-SPEED_NORMAL, -SPEED_NORMAL);
        return true;
    } 
    
    if (cmd == "CMD:LEFT") {
        _nav.setTargetSpeeds(-SPEED_TURN, SPEED_TURN);
        return true;
    } 
    
    if (cmd == "CMD:RIGHT") {
        _nav.setTargetSpeeds(SPEED_TURN, -SPEED_TURN);
        return true;
    } 
    
    if (cmd == "CMD:LEFT_PIVOT") {
        _car.turnLeftPivot();
        return true;
    } 
    
    if (cmd == "CMD:RIGHT_PIVOT") {
        _car.turnRightPivot();
        return true;
    } 
    
    if (cmd == "CMD:LEFT_PIVOT_BACK") {
        _car.turnLeftPivotBack();
        return true;
    } 
    
    if (cmd == "CMD:RIGHT_PIVOT_BACK") {
        _car.turnRightPivotBack();
        return true;
    } 
    
    if (cmd == "CMD:LEFT_ZERO") {
        _car.turnLeftZero();
        return true;
    } 
    
    if (cmd == "CMD:RIGHT_ZERO") {
        _car.turnRightZero();
        return true;
    }
    
    return false; // Command was not a wheeled drive command
}
