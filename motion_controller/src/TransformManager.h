#ifndef TRANSFORM_MANAGER_H
#define TRANSFORM_MANAGER_H

#include <Arduino.h>
#include "ServoControl.h"
#include "Balance.h"

enum TransitionState {
    TRANSITION_NONE,
    TRANSITION_TO_CAR,
    TRANSITION_TO_CRAWLER,
    TRANSITION_RECOVER_FORWARD,
    TRANSITION_RECOVER_BACKWARD,
    TRANSITION_RECOVER_SHAKE
};

/**
 * @class TransformManager
 * @brief Handles transitions between different robot configurations (Car, Biped, Crawler) and fall recoveries.
 * 
 * Separates physical shape-shifting sequences from low-level joint interpolation (ServoControl).
 */
class TransformManager {
public:
    TransformManager(ServoControl& servos);
    void begin();
    
    /**
     * @brief Periodic update for non-blocking shape transformations.
     */
    void update();

    // --- Transition Triggers ---
    void transformToCar();
    void transformToCrawler();
    void recoverFromFall(FallDirection dir);
    void stopTransition();

    // --- Status ---
    TransitionState getTransitionState() const { return _currentState; }
    bool isTransitioning() const { return _currentState != TRANSITION_NONE; }

private:
    ServoControl& _servos;
    TransitionState _currentState = TRANSITION_NONE;
    int _step = 0;
    unsigned long _lastStepTime = 0;
    int _shakeIteration = 0;

    void processTransitionStep();
};

#endif // TRANSFORM_MANAGER_H
