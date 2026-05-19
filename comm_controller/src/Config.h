#ifndef CONFIG_H
#define CONFIG_H

// ==========================================
// 📶 NETWORK CREDENTIALS
// ==========================================
#define WIFI_SSID "one"          // Local Wi-Fi Network Name
#define WIFI_PASS "12345678"     // Local Wi-Fi Password
#define AP_SSID "Remote-car"     // Personal Hotspot Name (AP Mode)
#define AP_PASS "12345678"       // Personal Hotspot Password (AP Mode)
#define SIM7600_APN "internet"   // 4G LTE APN for SIM Card

// ==========================================
// 🚀 FEATURE TOGGLES
// ==========================================
#define USE_4G_FALLBACK  true    // Enable automatic LTE switch if Wi-Fi fails
#define USE_OLED_DISPLAY true    // Enable SSD1306 facial expressions
#define USE_AUDIO_SYSTEM true    // Enable I2S Microphone and Speaker
#define USE_WEBSOCKETS   true    // Enable low-latency remote control via WS
#define USE_AI_BRAIN     true    // Connect to the Python AI Backend
#define USE_BLUETOOTH_AUDIO false // Enable Bluetooth Speaker functionality
#define USE_EXTERNAL_BT_SPEAKER false // Connect to external BT speakers
#define USE_WIFI_LR          true    // Enable Long Range WiFi (up to 1km)
#define USE_BLE_PROXIMITY    false   // Enable BLE beacon for phone detection
#define USE_MDNS             true    // Enable omni.local access
#define USE_NET_SNIFFER      true    // Enable WiFi packet sniffing for security audit
#define USE_AUDIO_VISUALIZER true    // Enable OLED eyes dancing to music/voice
#define USE_DYNAMIC_AI_LINK  true    // Auto-switch between Local and Global(ngrok) AI
#define AI_BRAIN_LOCAL_HOST  "omni-brain.local" // Your laptop's mDNS name
#define AI_BRAIN_LOCAL_PORT  8000
#define AI_BRAIN_GLOBAL_HOST "your-ngrok-id.ngrok-free.app" // Your ngrok URL
#define AI_BRAIN_GLOBAL_PORT 80
#define BT_DEVICE_NAME   "Omni-Core-BT"
#define VISION_CAM_URL   "http://192.168.1.50/stream" // ESP32-CAM Address


// ==========================================
// 📌 PIN ASSIGNMENTS (Comm Controller)
// ==========================================
// I2S Audio Pins
#define I2S_BCK_PIN  26
#define I2S_WS_PIN   25
#define I2S_DIN_PIN  33
#define I2S_DOUT_PIN 22

// I2C OLED Pins
#define OLED_SDA_PIN 21
#define OLED_SCL_PIN 23          // GPIO 23 used to avoid conflict with I2S

// SIM7600 UART Pins
#define SIM_TX_PIN   17
#define SIM_RX_PIN   16

// Inter-Controller Serial Link
#define MOTION_LINK_RX 4         // Connect to Motion Controller TX
#define MOTION_LINK_TX 15        // Connect to Motion Controller RX

// ==========================================
// ⚙️ SYSTEM SETTINGS
// ==========================================
#define SERIAL_BAUD 115200       // Standard baud rate for all serial comms
#define WEB_PORT 80              // HTTP Server Port
#define WS_PORT 81               // WebSocket Server Port

// ==========================================
// 🛡️ STABILITY & DEBUGGING
// ==========================================
#define DEBUG_LEVEL 2            // 0: Silent, 1: Errors, 2: Full Info
#define MIN_FREE_MEMORY 20000    // Minimum bytes of RAM before auto-cleanup
#define I2C_TIMEOUT_MS  100      // Timeout for I2C recovery logic

// ==========================================
// 🤖 ROBOT IDENTITY (The 'Soul' of the Robot)
// ==========================================
#define ROBOT_NAME "Omni-Core"
#define ROBOT_PERSONA "A wise, heroic, and protective leader of the robots. You are serious but kind-hearted, always looking for a peaceful solution but ready to defend humanity."
#define ROBOT_VERSION "v2.1-AI"
#define ROBOT_LANGUAGE "en" // Set to "ta" for Tamil

#endif


