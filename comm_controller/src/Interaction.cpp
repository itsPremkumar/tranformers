#include "Interaction.h"

Interaction::Interaction(AudioSystem* audio, DisplayController* display, BluetoothAudio* bt, WebInterface& web) 
    : _audio(audio), _display(display), _bt(bt), _web(web) {}

void Interaction::begin() {
    #if USE_AUDIO_SYSTEM
    if (_audio) _audio->begin();
    #endif
    
    #if USE_OLED_DISPLAY
    if (_display) _display->begin();
    #endif

    #if USE_BLUETOOTH_AUDIO
    if (_bt) {
        _bt->begin(I2S_BCK_PIN, I2S_WS_PIN, I2S_DOUT_PIN);
        #if USE_EXTERNAL_BT_SPEAKER
        if (_audio) _bt->setSharedBuffer(_audio->getBuffer());
        #endif
    }
    #endif
}

void Interaction::update(int currentMood) {
    #if USE_AUDIO_SYSTEM
    if (_audio && _audio->processAudio()) {
        triggerAiListening();
    }

    if (_audio && _audio->hasNoiseEvent()) {
        _web.broadcast("EVENT:LOUD_NOISE");
        Serial.println("[AUDIO] Loud noise detected! Alerting Brain...");
    }

    if (_isAiListening && (millis() - _aiListenStartTime > 10000)) {
        stopAiListening(currentMood);
    }
    #endif

    #if USE_OLED_DISPLAY
    if (_display && _audio) {
        // Compute real-time Wi-Fi Signal Percentage
        int wifiPercent = 0;
        if (WiFi.status() == WL_CONNECTED) {
            int rssi = WiFi.RSSI();
            wifiPercent = map(rssi, -100, -50, 0, 100);
            if (wifiPercent > 100) wifiPercent = 100;
            if (wifiPercent < 0) wifiPercent = 0;
        }
        // Feed the real-time values into status bar (using 92% as normal active battery)
        _display->updateSystemStatus(wifiPercent, 92, false);

        int amp = _audio->getRecentAmplitude();
        if (amp > 500) {
            #if USE_AUDIO_VISUALIZER
            _display->drawVisualizerFace(_audio->getLowEnergy(), _audio->getMidEnergy(), _audio->getHighEnergy());
            #else
            _display->drawTalkingMouth(amp);
            #endif
            _lastDisplayUpdate = millis();
        } else if (millis() - _lastDisplayUpdate > 3000) {
            _display->updateRandom();
            _lastDisplayUpdate = millis();
        }
    }
    #endif
}

void Interaction::handleMoodChange(int& currentMood, String cmd) {
    #if USE_OLED_DISPLAY
    if (!_display) return;
    String mood = cmd.substring(5);
    if (mood == "happy") { currentMood = 0; _display->SetState(FaceState::Idle); _display->happyFace(); }
    else if (mood == "sad") { currentMood = 1; _display->SetState(FaceState::Idle); _display->sadFace(); }
    else if (mood == "angry") { currentMood = 2; _display->SetState(FaceState::Idle); _display->angryFace(); }
    else if (mood == "hero") { currentMood = 3; _display->SetState(FaceState::Idle); _display->heroFace(); }
    else if (mood == "idle") { _display->SetState(FaceState::Idle); }
    else if (mood == "listening") { _display->SetState(FaceState::Listening); }
    else if (mood == "speaking") { _display->SetState(FaceState::Speaking); }
    else if (mood == "debug") { _display->SetState(FaceState::DebugHUD); }
    else if (mood.length() > 0 && isDigit(mood[0])) {
        currentMood = mood.toInt();
        _display->SetState(FaceState::Idle);
        _display->drawBitmapFace(currentMood);
    }
    #endif
}

void Interaction::triggerAiListening() {
    _isAiListening = true;
    _aiListenStartTime = millis();
    #if USE_OLED_DISPLAY
    if (_display) _display->heroFace();
    #endif
    _web.broadcast("STATUS: I am listening...");
    Serial.println("[AI] Wake Word Detected. Listening...");
}

void Interaction::stopAiListening(int currentMood) {
    _isAiListening = false;
    _web.broadcast("STATUS: Going to sleep...");
    #if USE_OLED_DISPLAY
    if (_display) _display->drawBitmapFace(currentMood);
    #endif
}
