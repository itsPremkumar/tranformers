#ifndef BLUETOOTH_AUDIO_H
#define BLUETOOTH_AUDIO_H

#include <Arduino.h>
#include "BluetoothA2DPSink.h"
#include "BluetoothA2DPSource.h"
#include "Config.h"

class BluetoothAudio {
public:
    BluetoothAudio();
    void begin(int bckPin, int wsPin, int dataOutPin);
    void beginSource(const char* targetName = "Omni-Speaker");
    void setSharedBuffer(RingbufHandle_t buf);
    void end();
    bool isConnected();
    
    // Callbacks
    static void avrc_metadata_callback(uint8_t id, const uint8_t *text);
    static int32_t get_data_callback(uint8_t *data, int32_t len);

private:
    BluetoothA2DPSink _a2dpSink;
    BluetoothA2DPSource _a2dpSource;
    bool _isStarted;
    bool _isSource;
};

#endif
