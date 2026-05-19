#include "BluetoothAudio.h"
#include "AudioSystem.h"

// Static reference for callback
static RingbufHandle_t _sharedAudioBuffer = nullptr;

BluetoothAudio::BluetoothAudio() {
    _isStarted = false;
    _isSource = false;
}

void BluetoothAudio::begin(int bckPin, int wsPin, int dataOutPin) {
    #if USE_BLUETOOTH_AUDIO && !USE_EXTERNAL_BT_SPEAKER
    Serial.println("[BT-AUDIO] Starting Bluetooth A2DP Sink...");
    
    i2s_pin_config_t my_pin_config = {
        .bck_io_num = bckPin,
        .ws_io_num = wsPin,
        .data_out_num = dataOutPin,
        .data_in_num = -1
    };
    
    _a2dpSink.set_pin_config(my_pin_config);
    _a2dpSink.set_i2s_port(I2S_NUM_1);
    _a2dpSink.start(BT_DEVICE_NAME);
    _a2dpSink.set_avrc_metadata_callback(avrc_metadata_callback);
    
    _isStarted = true;
    _isSource = false;
    Serial.println("[BT-AUDIO] Bluetooth Sink Ready as: " BT_DEVICE_NAME);
    #endif

    #if USE_EXTERNAL_BT_SPEAKER
    beginSource();
    #endif
}

void BluetoothAudio::beginSource(const char* targetName) {
    #if USE_EXTERNAL_BT_SPEAKER
    const char* target = (targetName && strlen(targetName) > 0) ? targetName : "Omni-Speaker";
    Serial.printf("[BT-SOURCE] Starting Bluetooth A2DP Source targeting: %s\n", target);
    
    _a2dpSource.start_raw(target, get_data_callback);
    _isStarted = true;
    _isSource = true;
    Serial.println("[BT-SOURCE] Scanning for External Speakers...");
    #endif
}

void BluetoothAudio::setSharedBuffer(RingbufHandle_t buf) {
    _sharedAudioBuffer = buf;
}

int32_t BluetoothAudio::get_data_callback(uint8_t *data, int32_t len) {
    if (!_sharedAudioBuffer) {
        memset(data, 0, len);
        return len;
    }

    size_t item_size;
    // Try to get data from the ring buffer
    uint8_t *buffer_data = (uint8_t *)xRingbufferReceiveUpTo(_sharedAudioBuffer, &item_size, 0, len);
    
    if (buffer_data != NULL) {
        memcpy(data, buffer_data, item_size);
        vRingbufferReturnItem(_sharedAudioBuffer, (void *)buffer_data);
        
        // If we got less than requested, fill the rest with zeros
        if (item_size < len) {
            memset(data + item_size, 0, len - item_size);
        }
        return len;
    } else {
        memset(data, 0, len);
        return len;
    }
}

void BluetoothAudio::end() {
    if (_isStarted) {
        if (_isSource) _a2dpSource.end();
        else _a2dpSink.end();
        _isStarted = false;
    }
}

bool BluetoothAudio::isConnected() {
    if (_isSource) return _a2dpSource.is_connected();
    return _a2dpSink.is_connected();
}

void BluetoothAudio::avrc_metadata_callback(uint8_t id, const uint8_t *text) {
    if (id == ESP_AVRC_MD_ATTR_TITLE) {
        Serial.print("[BT-AUDIO] Playing: ");
        Serial.println((char*)text);
    }
}
