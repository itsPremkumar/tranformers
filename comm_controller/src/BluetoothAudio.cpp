#include "BluetoothAudio.h"

BluetoothAudio::BluetoothAudio() {
    _isStarted = false;
}

void BluetoothAudio::begin(int bckPin, int wsPin, int dataOutPin) {
    #if USE_BLUETOOTH_AUDIO
    Serial.println("[BT-AUDIO] Starting Bluetooth A2DP Sink...");
    
    // Set custom I2S pins to match the existing AudioSystem
    i2s_pin_config_t my_pin_config = {
        .bck_io_num = bckPin,
        .ws_io_num = wsPin,
        .data_out_num = dataOutPin,
        .data_in_num = -1
    };
    
    _a2dpSink.set_pin_config(my_pin_config);
    _a2dpSink.set_i2s_port(I2S_NUM_1);
    
    // Start with the name defined in Config.h
    _a2dpSink.start(BT_DEVICE_NAME);
    
    _a2dpSink.set_avrc_metadata_callback(avrc_metadata_callback);
    
    _isStarted = true;
    Serial.println("[BT-AUDIO] Bluetooth Audio Ready as: " BT_DEVICE_NAME);
    #endif
}

void BluetoothAudio::end() {
    if (_isStarted) {
        _a2dpSink.end();
        _isStarted = false;
    }
}

bool BluetoothAudio::isConnected() {
    return _a2dpSink.is_connected();
}

void BluetoothAudio::avrc_metadata_callback(uint8_t id, const uint8_t *text) {
    // Optional: Log what's playing
    if (id == ESP_AVRC_MD_ATTR_TITLE) {
        Serial.print("[BT-AUDIO] Playing: ");
        Serial.println((char*)text);
    }
}
