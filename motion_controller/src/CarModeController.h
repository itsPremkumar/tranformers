#ifndef CAR_MODE_CONTROLLER_H
#define CAR_MODE_CONTROLLER_H

#include <Arduino.h>
#include "MotorControl.h"
#include "ObstacleAvoidance.h"
#include "Balance.h"
#include "Navigation.h"

/**
 * @class CarModeController
 * @brief Manages the robot's behaviors, navigation, and obstacle avoidance while in Car Configuration.
 */
class CarModeController {
public:
    CarModeController(MotorControl& car, ObstacleAvoidance& obstacle, Balance& balance, Navigation& nav);
    void begin();
    
    /**
     * @brief Periodic update function. Runs waypoint navigation and safety scans.
     */
    void update();
    
    /**
     * @brief Handles commands specific to Car Mode operations.
     */
    bool handleCommand(const String& cmd);

private:
    MotorControl& _car;
    ObstacleAvoidance& _obstacle;
    Balance& _balance;
    Navigation& _nav;
};

#endif // CAR_MODE_CONTROLLER_H
