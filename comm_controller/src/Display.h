#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

enum class FaceState { Idle, Listening, Speaking, DebugHUD, Transforming };

class DisplayController {
public:
    DisplayController(uint8_t address = 0x3C, int width = 128, int height = 64);
    void begin();
    
    // Core Actions
    void clearFace();
    void showFace();
    void updateRandom();
    
    // FaceState Management
    void SetState(FaceState state);
    FaceState GetState() const { return _state; }
    void updateFaceEngine();
    void updateSystemStatus(int wifi, int battery, bool muted);
    
    // Expressions
    void happyFace();
    void sadFace();
    void angryFace();
    void peaceFace();
    void heroFace();
    void loveFace();
    void fearFace();
    void disgustFace();
    void wonderFace();
    void sleepMode();
    void warningFace();
    void showProgress(String label, int percent);
    void talkingAnimation();
    void drawTalkingMouth(int amplitude);
    void drawVisualizerFace(float low, float mid, float high);
    void drawBitmapFace(int index);
    void SetSubtitle(String text);

private:
    Adafruit_SSD1306 _display;
    uint8_t _address;
    
    // System Status Bar Variables
    int _wifiPercent = 85;
    int _batteryPercent = 95;
    bool _isMuted = false;
    
    void drawTopStatusBar(int wifiPercent, int batteryPercent, bool isMuted);
    void drawScrollingSubtitle();
    
    // New FaceEngine States & Offsets
    FaceState _state = FaceState::Idle;
    int _blinkPhase = 0;
    int _idleOffsetX = 0;
    int _idleOffsetY = 0;
    unsigned long _lastBlinkUpdate = 0;
    unsigned long _lastSpeakUpdate = 0;
    unsigned long _transformStartTime = 0;
    int _speakMouthTarget = 4;
    int _speakMouthCurrent = 4;

    // Chat Scrolling Subtitles (Xiaozhi Inspired)
    String _chatSubtitle = "";
    int _scrollOffset = 0;
    unsigned long _lastScrollUpdate = 0;

    // New FaceEngine Behaviors
    void IdleBehavior(int eyeHeight);
    void ListeningBehavior(int eyeHeight);
    void SpeakingBehavior(int eyeHeight);
    void TransformingBehavior();
    void drawDebugHUD();
    
    // Drawing helpers
    void drawNormalEyes(int leftX, int rightX, int y = 24);
    void drawClosedEyes();
    void drawSmile();
    void drawSadMouth();
    void drawStraightMouth();
    void drawHeart(int x, int y);
    
    // Animations
    void randomBlink();
    void thinkingAnimation();
};

#endif
