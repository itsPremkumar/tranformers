#ifndef INTERACTION_H
#define INTERACTION_H

#include <Arduino.h>
#include "Config.h"
#include "Audio.h"
#include "Display.h"
#include "BluetoothAudio.h"
#include "RobotServer.h"

class Interaction {
public:
    Interaction(AudioSystem* audio, DisplayController* display, BluetoothAudio* bt, WebInterface& web);
    
    void begin();
    void update(int currentMood);
    void handleMoodChange(int& currentMood, String cmd);
    void triggerAiListening();
    void stopAiListening(int currentMood);
    
    bool isAiListening() const { return _isAiListening; }
    unsigned long getAiListenStartTime() const { return _aiListenStartTime; }

private:
    AudioSystem* _audio;
    DisplayController* _display;
    BluetoothAudio* _bt;
    WebInterface& _web;
    
    bool _isAiListening = false;
    unsigned long _aiListenStartTime = 0;
    unsigned long _lastDisplayUpdate = 0;
};

#endif
