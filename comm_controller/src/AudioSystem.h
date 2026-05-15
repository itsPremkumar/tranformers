#ifndef AUDIO_SYSTEM_H
#define AUDIO_SYSTEM_H

#include <Arduino.h>
#include <driver/i2s.h>
#include <freertos/ringbuf.h>

class AudioSystem {
public:
    AudioSystem(int bckPin = 26, int wsPin = 25, int dataInPin = 33, int dataOutPin = 22);
    void begin();
    void playTestTone();
    bool processAudio();
    void playRawPCM(uint8_t* data, size_t len);
    void speak(String text);
    void update(); // Add update for MP3 streaming
    int getRecentAmplitude() { return _currentAmplitude; }
    bool checkForWakeWord(int16_t* buffer, size_t samples);
    
    // Background Feeder (static for FreeRTOS task)
    static void i2sFeederTask(void *pvParameters);

private:
    int _bckPin, _wsPin, _dataInPin, _dataOutPin;
    RingbufHandle_t _audioBuffer;
    TaskHandle_t _feederTaskHandle;
    
    float _vadThreshold = 500.0f;
    bool isVoiceActive(int16_t* buffer, size_t samples);
    
    // Wake Word State
    unsigned long _lastClapTime = 0;
    int _clapCount = 0;
    float _noiseFloor = 1000.0f;
    const int CLAP_THRESHOLD = 15000; 
    
    volatile int _currentAmplitude = 0;
    static const int RING_BUFFER_SIZE = 32 * 1024; 
};

#endif
