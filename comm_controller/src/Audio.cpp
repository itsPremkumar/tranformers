#include "Audio.h"

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
        .communication_format = I2S_COMM_FORMAT_I2S,
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
        .communication_format = I2S_COMM_FORMAT_I2S,
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
    Serial.println("[AUDIO] Non-blocking Audio System Initialized.");
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

void AudioSystem::processAudio() {
    // Simplified: Just passthrough if needed, but usually AI handles this now
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

void AudioSystem::i2sFeederTask(void *pvParameters) {
    AudioSystem *self = (AudioSystem *)pvParameters;
    size_t item_size;
    
    while (true) {
        // Receive data from the ring buffer
        uint8_t *data = (uint8_t *)xRingbufferReceive(self->_audioBuffer, &item_size, portMAX_DELAY);
        
        if (data != NULL) {
            size_t bytesWritten;
            // Write to I2S. This task can block, but it won't affect the main Arduino loop.
            i2s_write(I2S_NUM_1, data, item_size, &bytesWritten, portMAX_DELAY);
            
            // Return the item to the ring buffer
            vRingbufferReturnItem(self->_audioBuffer, (void *)data);
        }
    }
}
