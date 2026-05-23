#include "BipedModeController.h"
#include "Config.h"

BipedModeController::BipedModeController(ServoControl& servos, Balance& balance, TransformManager& transform)
    : _servos(servos), _balance(balance), _transform(transform) {}

void BipedModeController::begin() {
    _servos.standPosition();
}

void BipedModeController::update() {
    // 1. Update lower-level servo joint positions
    _servos.update();
    
    // 2. Fall Detection and Auto-Recovery (if MPU is enabled)
    #if USE_MPU6050
    if (_balance.isOnline() && !_transform.isTransitioning()) {
        FallDirection fall = _balance.checkFall();
        if (fall != NO_FALL) {
            Serial.printf("[BIPED] Fall detected (Direction: %d)! Triggering recovery.\n", (int)fall);
            _transform.recoverFromFall(fall);
        }
    }
    #endif
}

bool BipedModeController::handleCommand(const String& cmd) {
    if (cmd == "CMD:WALK") {
        #if ENABLE_WALKING
        Serial.println("[BIPED] Humanoid gait walk forward triggered.");
        _servos.walkForward();
        #endif
        return true;
    }
    
    if (cmd == "CMD:PUSH") {
        Serial.println("[BIPED] Pushing gesture triggered.");
        _servos.pushMotion();
        return true;
    }
    
    if (cmd == "CMD:KICK") {
        Serial.println("[BIPED] Kicking gesture triggered.");
        _servos.kickMotion();
        return true;
    }
    
    return false; // Command was not a stand/walk/biped command
}
