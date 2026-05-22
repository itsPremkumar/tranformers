#include "AudioSystem.h"
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <arduinoFFT.h>

// Note: We use the ESP32-audioI2S library's Audio class
#include "Audio.h" 
static Audio *mp3 = nullptr;

#define SAMPLES 128
#define SAMPLING_FREQ 16000
double vReal[SAMPLES];
double vImag[SAMPLES];
arduinoFFT FFT = arduinoFFT(vReal, vImag, SAMPLES, SAMPLING_FREQ);

AudioSystem::AudioSystem(int bckPin, int wsPin, int dataInPin, int dataOutPin) {
    _bckPin = bckPin;
    _wsPin = wsPin;
    _dataInPin = dataInPin;
    _dataOutPin = dataOutPin;
}

void AudioSystem::begin() {
    // 1. Setup I2S Drivers (Rx and Tx)
    i2s_config_t i2s_config_rx = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = 16000,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = 0,
        .dma_buf_count = 4,
        .dma_buf_len = 256,
        .use_apll = false
    };

    i2s_pin_config_t pin_config_rx = {
        .bck_io_num = _bckPin,
        .ws_io_num = _wsPin,
        .data_out_num = -1,
        .data_in_num = _dataInPin
    };

    i2s_driver_install(I2S_NUM_0, &i2s_config_rx, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config_rx);

    i2s_config_t i2s_config_tx = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = 16000,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = 0,
        .dma_buf_count = 8,  // Increased for smoother playback
        .dma_buf_len = 512,
        .use_apll = false
    };

    i2s_pin_config_t pin_config_tx = {
        .bck_io_num = _bckPin,
        .ws_io_num = _wsPin,
        .data_out_num = _dataOutPin,
        .data_in_num = -1
    };

    i2s_driver_install(I2S_NUM_1, &i2s_config_tx, 0, NULL);
    i2s_set_pin(I2S_NUM_1, &pin_config_tx);

    // 2. Initialize Ring Buffer for non-blocking playback
    _audioBuffer = xRingbufferCreate(RING_BUFFER_SIZE, RINGBUF_TYPE_BYTEBUF);
    if (_audioBuffer == NULL) {
        Serial.println("[AUDIO] Failed to create ring buffer!");
    }

    // 3. Start the background I2S Feeder Task
    xTaskCreate(this->i2sFeederTask, "i2s_feeder", 4096, this, 5, &_feederTaskHandle);
    
    // 4. Setup MP3 Streamer (Jarvis Voice)
    mp3 = new Audio(1);
    mp3->setPinout(_bckPin, _wsPin, _dataOutPin);
    mp3->setVolume(21); // 0...21
    
    Serial.println("[AUDIO] Non-blocking Audio System Initialized.");
}

void AudioSystem::update() {
    if (mp3) mp3->loop();
}

void AudioSystem::speak(String text) {
    if (!mp3) return;
    
    Serial.println("[JARVIS] Speaking: " + text);
    
    // Google Translate TTS URL (British English)
    String url = "http://translate.google.com/translate_tts?ie=UTF-8&q=";
    // Basic URL encoding for spaces
    String encodedText = text;
    encodedText.replace(" ", "%20");
    url += encodedText;
    url += "&tl=en-gb&client=tw-ob";
    
    mp3->connecttohost(url.c_str());
}

void AudioSystem::playTestTone() {
    Serial.println("[AUDIO] Buffering Test Tone...");
    int frequency = 440; // A4
    int sampleRate = 16000;
    size_t testLen = sampleRate / 2 * sizeof(int16_t);
    int16_t* testData = (int16_t*)malloc(testLen);
    
    for (int i = 0; i < sampleRate / 2; i++) {
        testData[i] = 10000 * sin(2 * PI * frequency * i / sampleRate);
    }
    
    playRawPCM((uint8_t*)testData, testLen);
    free(testData);
}

void AudioSystem::playChime(int type) {
    Serial.printf("[AUDIO] Playing native chime type %d...\n", type);
    int sampleRate = 16000;
    float duration = 0.3; // 300 ms duration
    size_t samples = sampleRate * duration;
    size_t bufLen = samples * sizeof(int16_t);
    int16_t* buf = (int16_t*)malloc(bufLen);
    if (buf == NULL) return;
    
    if (type == 0) { // Boot Chirp (Upward Frequency Sweep)
        for (size_t i = 0; i < samples; i++) {
            float freq = 440.0 + (880.0 - 440.0) * (float)i / samples;
            buf[i] = 8000 * sin(2 * PI * freq * i / sampleRate);
        }
        playRawPCM((uint8_t*)buf, bufLen);
    } else if (type == 1) { // Double Beep Success
        size_t half = samples / 2;
        for (size_t i = 0; i < half; i++) {
            buf[i] = 10000 * sin(2 * PI * 880.0 * i / sampleRate);
        }
        for (size_t i = half; i < samples; i++) {
            buf[i] = 10000 * sin(2 * PI * 1760.0 * i / sampleRate);
        }
        playRawPCM((uint8_t*)buf, bufLen);
    } else if (type == 2) { // Warning/Error Low Buzzer
        for (size_t i = 0; i < samples; i++) {
            buf[i] = 12000 * sin(2 * PI * 180.0 * i / sampleRate);
        }
        playRawPCM((uint8_t*)buf, bufLen);
    }
    free(buf);
}


bool AudioSystem::isVoiceActive(int16_t* buffer, size_t samples) {
    long long sum = 0;
    for (size_t i = 0; i < samples; i++) {
        sum += abs(buffer[i]);
    }
    float averageEnergy = (float)sum / samples;
    return averageEnergy > _vadThreshold;
}

bool AudioSystem::checkForWakeWord(int16_t* buffer, size_t samples) {
    long long sum = 0;
    bool peakDetected = false;
    for (size_t i = 0; i < samples; i++) {
        int absVal = abs(buffer[i]);
        sum += absVal;
        if (absVal > CLAP_THRESHOLD) peakDetected = true;
    }
    float energy = (float)sum / samples;

    // Adaptive noise floor (Slowly tracks room volume)
    _noiseFloor = (_noiseFloor * 0.99f) + (energy * 0.01f);

    if (peakDetected) {
        unsigned long now = millis();
        unsigned long diff = now - _lastClapTime;

        if (diff < 150) return false; // Ignore echo

        if (_clapCount == 0) {
            _clapCount = 1;
            _lastClapTime = now;
            Serial.println("[WAKE] First clap detected...");
        } else if (_clapCount == 1) {
            if (diff > 200 && diff < 800) {
                Serial.println("[WAKE] Double-Clap MATCHED! Waking up AI...");
                _clapCount = 0;
                _lastClapTime = 0;
                return true;
            } else {
                _lastClapTime = now;
                _clapCount = 1;
            }
        }
    } else {
        if (_clapCount > 0 && (millis() - _lastClapTime > 1000)) {
            _clapCount = 0;
        }
    }
    return false;
}

size_t AudioSystem::getMicData(int16_t* buffer, size_t maxSamples) {
    size_t bytesRead;
    esp_err_t res = i2s_read(I2S_NUM_0, buffer, maxSamples * sizeof(int16_t), &bytesRead, 0); // No wait
    if (res == ESP_OK) return bytesRead / sizeof(int16_t);
    return 0;
}

bool AudioSystem::processAudio() {
    #if USE_AUDIO_SYSTEM
    int16_t readBuffer[512];
    size_t bytesRead;
    
    // Read from Microphone (I2S_NUM_0)
    esp_err_t res = i2s_read(I2S_NUM_0, readBuffer, sizeof(readBuffer), &bytesRead, 10);
    
    if (res == ESP_OK && bytesRead > 0) {
        size_t samples = bytesRead / sizeof(int16_t);
        
        // 1. Check for Offline Wake Word (Double Clap)
        if (checkForWakeWord(readBuffer, samples)) {
            return true; 
        }

        // 2. VAD & Noise Detection
        int maxAmp = 0;
        for (int i = 0; i < samples; i++) {
            if (abs(readBuffer[i]) > maxAmp) maxAmp = abs(readBuffer[i]);
        }
        _currentAmplitude = maxAmp;

        static unsigned long lastNoise = 0;
        if (maxAmp > 12000 && millis() - lastNoise > 3000) { // Loud threshold
            _hasNoiseEvent = true;
            lastNoise = millis();
        }

        if (isVoiceActive(readBuffer, samples)) {
            // Here you would normally send the buffer to your AI backend
        }
    }
    #endif
    return false;
}

void AudioSystem::playRawPCM(uint8_t* data, size_t len) {
    if (_audioBuffer == NULL) return;
    
    // Push data to ring buffer. Use NO_WAIT to ensure it's non-blocking for the main loop.
    // If the buffer is full, we might lose some audio, but the robot stays responsive.
    BaseType_t res = xRingbufferSend(_audioBuffer, data, len, 0); 
    if (res != pdTRUE) {
        // If it failed to send immediately, try a small wait (10ms) to avoid dropping too much
        xRingbufferSend(_audioBuffer, data, len, pdMS_TO_TICKS(10));
    }
}

void AudioSystem::performFFT(int16_t* samples, size_t count) {
    if (count < SAMPLES) return;
    
    for (int i = 0; i < SAMPLES; i++) {
        vReal[i] = samples[i];
        vImag[i] = 0;
    }

    FFT.Windowing(FFT_WIN_TYP_HAMMING, FFT_FORWARD);
    FFT.Compute(FFT_FORWARD);
    FFT.ComplexToMagnitude();

    // Sum energies in 3 bands (approximate for 16kHz)
    // Band 0 (Bass): 0 - 500 Hz (bins 0-4)
    // Band 1 (Mid): 500 - 4000 Hz (bins 5-32)
    // Band 2 (High): 4000 - 8000 Hz (bins 33-63)
    
    _lowEnergy = 0; _midEnergy = 0; _highEnergy = 0;
    for (int i = 2; i < 5; i++) _lowEnergy += vReal[i];
    for (int i = 5; i < 33; i++) _midEnergy += vReal[i];
    for (int i = 33; i < 64; i++) _highEnergy += vReal[i];

    // Normalize (very rough scaling)
    _lowEnergy /= 3000.0;
    _midEnergy /= 8000.0;
    _highEnergy /= 5000.0;
}

void AudioSystem::i2sFeederTask(void *pvParameters) {
    AudioSystem *self = (AudioSystem *)pvParameters;
    if (self->_audioBuffer == NULL) {
        Serial.println("[AUDIO ERROR] Feeder Task aborted: Ring buffer is NULL!");
        vTaskDelete(NULL);
        return;
    }
    size_t item_size;
    
    while (true) {
        // Receive data from the ring buffer
        uint8_t *data = (uint8_t *)xRingbufferReceive(self->_audioBuffer, &item_size, portMAX_DELAY);
        
        if (data != NULL) {
            size_t bytesWritten;
            
            // Calculate amplitude and FFT for Visualizer
            int16_t *samples = (int16_t *)data;
            size_t numSamples = item_size / sizeof(int16_t);
            
            #if USE_AUDIO_VISUALIZER
            self->performFFT(samples, numSamples);
            #endif

            int maxAmp = 0;
            for (size_t i = 0; i < numSamples; i += 4) { 
                int val = abs(samples[i]);
                if (val > maxAmp) maxAmp = val;
            }
            self->_currentAmplitude = maxAmp;

            // Write to I2S.
            #if !USE_EXTERNAL_BT_SPEAKER
            i2s_write(I2S_NUM_1, data, item_size, &bytesWritten, portMAX_DELAY);
            #endif
            
            vRingbufferReturnItem(self->_audioBuffer, (void *)data);
        } else {
            self->_currentAmplitude = 0;
            self->_lowEnergy = 0; self->_midEnergy = 0; self->_highEnergy = 0;
        }
    }
}
