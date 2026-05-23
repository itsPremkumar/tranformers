#include "CrawlerModeController.h"
#include "Config.h"

CrawlerModeController::CrawlerModeController(MotorControl& car, ServoControl& servos)
    : _car(car), _servos(servos) {}

void CrawlerModeController::begin() {
    _car.stop();
}

void CrawlerModeController::update() {
    // 1. Maintain motor speeds
    _car.update();
    
    // 2. Maintain active servo stance
    _servos.update();
}

bool CrawlerModeController::handleCommand(const String& cmd) {
    // Crawler uses wheeled drive, but limited to a safer slow speed
    if (cmd == "CMD:FORWARD") {
        _car.setSpeed(SPEED_SLOW);
        _car.moveForward();
        return true;
    }
    
    if (cmd == "CMD:BACKWARD") {
        _car.setSpeed(SPEED_SLOW);
        _car.moveBackward();
        return true;
    }
    
    if (cmd == "CMD:LEFT") {
        _car.setSpeed(SPEED_SLOW);
        _car.turnLeft();
        return true;
    }
    
    if (cmd == "CMD:RIGHT") {
        _car.setSpeed(SPEED_SLOW);
        _car.turnRight();
        return true;
    }
    
    return false;
}
