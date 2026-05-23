#ifndef SERVO_CONTROL_H
#define SERVO_CONTROL_H

#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>
#include "Balance.h"

/**
 * @enum ServoAction
 * @brief Represents active non-blocking multi-step sequences.
 */
enum ServoAction {
    ACTION_NONE,
    ACTION_WALK,
    ACTION_TRANSFORM_CAR,
    ACTION_TRANSFORM_CRAWLER,
    ACTION_PUSH,
    ACTION_KICK,
    ACTION_RECOVERY_FORWARD,
    ACTION_RECOVERY_BACKWARD,
    ACTION_RECOVERY_SHAKE
};

/**
 * @class ServoControl
 * @brief Coordinates the PCA9685 I2C servo driver for limbs and executes humanoid gait movements.
 * 
 * All long-running actions (walking, transforming, recovery sequences) are executed through a
 * time-sliced cooperative state machine to ensure loop responsiveness.
 */
class ServoControl {
public:
    ServoControl(uint8_t addr = 0x40);
    void begin();
    
    // --- Periodic Updates ---
    void update(); // Non-blocking interpolation and action sequence updates
    void updateSleep();
    void updateBreathing();
    void wakeServos();
    void setBreathing(bool enabled) { _breathingEnabled = enabled; }

    // --- High-level Non-blocking Triggers ---
    void standPosition();
    void walkForward();
    void transformToCar();
    void transformToCrawler();
    void pushMotion();
    void kickMotion();
    void recoverFromFall(FallDirection dir);
    void stopAction(); // Interrupts any running sequence and returns to neutral

    // --- Direct Joint Control ---
    void moveServoSmooth(int channel, int targetAngle, int speedDelay = 5);
    void moveGroup(int channels[], int targets[], int count);
    
    // --- Status ---
    ServoAction getActiveAction() const { return _currentAction; }
    bool isActionRunning() const { return _currentAction != ACTION_NONE; }

private:
    Adafruit_PWMServoDriver _pwm;
    
    static const int NUM_SERVOS = 16;
    static const int SERVOMIN = 100;
    static const int SERVOMAX = 500;
    
    int _servoPos[NUM_SERVOS];
    int _targetPos[NUM_SERVOS];
    int _moveSpeed[NUM_SERVOS]; 
    unsigned long _lastMoveTime[NUM_SERVOS];
    unsigned long _lastActivityTime = 0;
    bool _isAsleep = false;
    bool _breathingEnabled = true;
    
    // Cooperative Action Sequence State Variables
    ServoAction _currentAction = ACTION_NONE;
    int _actionStep = 0;
    unsigned long _lastActionStepTime = 0;
    int _shakeIteration = 0;

    int angleToPulse(int angle);
    void processActionStep();
};

#endif // SERVO_CONTROL_H
