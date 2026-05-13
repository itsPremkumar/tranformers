#ifndef AUDIO_H
#define AUDIO_H

#include <Arduino.h>
#include <driver/i2s.h>
#include <freertos/ringbuf.h>

class AudioSystem {
public:
    AudioSystem(int bckPin = 26, int wsPin = 25, int dataInPin = 33, int dataOutPin = 22);
    void begin();
    void playTestTone();
    void processAudio();
    void playRawPCM(uint8_t* data, size_t len);
    
    // Background Feeder (static for FreeRTOS task)
    static void i2sFeederTask(void *pvParameters);

private:
    int _bckPin;
    int _wsPin;
    int _dataInPin;
    int _dataOutPin;
    
    RingbufHandle_t _audioBuffer;
    TaskHandle_t _feederTaskHandle;
    
    float _vadThreshold = 500.0f; // Adjusted for ambient noise
    bool isVoiceActive(int16_t* buffer, size_t samples);
    
    static const int RING_BUFFER_SIZE = 32 * 1024; // 32KB buffer
};

#endif
