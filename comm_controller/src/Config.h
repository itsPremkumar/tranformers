#ifndef CONFIG_H
#define CONFIG_H

// ==========================================
// 📶 NETWORK CREDENTIALS
// ==========================================
#define WIFI_SSID "one"          // Local Wi-Fi Network Name
#define WIFI_PASS "12345678"     // Local Wi-Fi Password
#define SIM7600_APN "internet"   // 4G LTE APN for SIM Card

// ==========================================
// 🚀 FEATURE TOGGLES
// ==========================================
#define USE_4G_FALLBACK  true    // Enable automatic LTE switch if Wi-Fi fails
#define USE_OLED_DISPLAY true    // Enable SSD1306 facial expressions
#define USE_AUDIO_SYSTEM true    // Enable I2S Microphone and Speaker
#define USE_WEBSOCKETS   true    // Enable low-latency remote control via WS
#define USE_AI_BRAIN     true    // Connect to the Python AI Backend
#define USE_BLUETOOTH_AUDIO true // Enable Bluetooth Speaker functionality
#define BT_DEVICE_NAME   "Omni-Core-BT"
#define AI_BRAIN_HOST    "192.168.1.100" // IP Address of your PC
#define AI_BRAIN_PORT    8000            // FastAPI Port
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
// 🤖 ROBOT IDENTITY (The 'Soul' of the Robot)
// ==========================================
#define ROBOT_NAME "Omni-Core"
#define ROBOT_PERSONA "A wise, heroic, and protective leader of the robots. You are serious but kind-hearted, always looking for a peaceful solution but ready to defend humanity."
#define ROBOT_VERSION "v2.1-AI"
#define ROBOT_LANGUAGE "en" // Set to "ta" for Tamil

#endif


