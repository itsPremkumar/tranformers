#ifndef BLUETOOTH_AUDIO_H
#define BLUETOOTH_AUDIO_H

#include <Arduino.h>
#include "BluetoothA2DPSink.h"
#include "Config.h"

class BluetoothAudio {
public:
    BluetoothAudio();
    void begin(int bckPin, int wsPin, int dataOutPin);
    void end();
    bool isConnected();
    
    // Callbacks for metadata if needed
    static void avrc_metadata_callback(uint8_t id, const uint8_t *text);

private:
    BluetoothA2DPSink _a2dpSink;
    bool _isStarted;
};

#endif
