#ifndef BIPED_MODE_CONTROLLER_H
#define BIPED_MODE_CONTROLLER_H

#include <Arduino.h>
#include "ServoControl.h"
#include "Balance.h"
#include "TransformManager.h"

/**
 * @class BipedModeController
 * @brief Manages balance, gaits, physical gestures, and fall checks while in Stand/Walk configuration.
 */
class BipedModeController {
public:
    BipedModeController(ServoControl& servos, Balance& balance, TransformManager& transform);
    void begin();
    
    /**
     * @brief Periodic update function. Checks for falls and coordinates biped gaits.
     */
    void update();
    
    /**
     * @brief Handles commands specific to Biped Mode operations.
     */
    bool handleCommand(const String& cmd);

private:
    ServoControl& _servos;
    Balance& _balance;
    TransformManager& _transform;
};

#endif // BIPED_MODE_CONTROLLER_H
