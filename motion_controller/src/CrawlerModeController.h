#ifndef CRAWLER_MODE_CONTROLLER_H
#define CRAWLER_MODE_CONTROLLER_H

#include <Arduino.h>
#include "MotorControl.h"
#include "ServoControl.h"

/**
 * @class CrawlerModeController
 * @brief Handles robot locomotion and configuration adjustments while in Crawler Configuration.
 */
class CrawlerModeController {
public:
    CrawlerModeController(MotorControl& car, ServoControl& servos);
    void begin();
    
    /**
     * @brief Periodic update function. Keeps crawler stance stabilized and updates motor ramping.
     */
    void update();
    
    /**
     * @brief Handles commands specific to Crawler Mode operations.
     */
    bool handleCommand(const String& cmd);

private:
    MotorControl& _car;
    ServoControl& _servos;
};

#endif // CRAWLER_MODE_CONTROLLER_H
