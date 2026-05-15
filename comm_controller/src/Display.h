#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

class DisplayController {
public:
    DisplayController(uint8_t address = 0x3C, int width = 128, int height = 64);
    void begin();
    
    // Core Actions
    void clearFace();
    void showFace();
    void updateRandom();
    
    // Expressions
    void happyFace();
    void sadFace();
    void angryFace();
    void peaceFace();
    void heroFace();
    void sleepMode();
    void warningFace();
    void talkingAnimation();
    void drawTalkingMouth(int amplitude);
    void drawVisualizerFace(float low, float mid, float high);
    void drawBitmapFace(int index);

private:
    Adafruit_SSD1306 _display;
    uint8_t _address;
    
    // Drawing helpers
    void drawNormalEyes(int leftX, int rightX, int y = 24);
    void drawClosedEyes();
    void drawSmile();
    void drawSadMouth();
    void drawStraightMouth();
    
    // Animations
    void randomBlink();
    void thinkingAnimation();
};

#endif
