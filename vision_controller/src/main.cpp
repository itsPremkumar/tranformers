#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <esp_now.h>

// WiFi Sync Data Structure
struct WiFiSync {
    char ssid[32];
    char pass[64];
};

Preferences prefs;

// Default Fallback (Your original credentials preserved)
const char* default_ssid = "one";
const char* default_password = "12345678";

#define WIFI_TIMEOUT 30000

// ==========================================
// 📌 AI Thinker ESP32-CAM Pin Map
// ==========================================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define FLASH_GPIO_NUM     4
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ESP-NOW Callback for Wireless WiFi Syncing
void onDataReceive(const uint8_t * mac, const uint8_t *incomingData, int len) {
    if (len == sizeof(WiFiSync)) {
        WiFiSync sync;
        memcpy(&sync, incomingData, sizeof(WiFiSync));
        
        Serial.println("[SYNC] Received New WiFi Credentials!");
        prefs.begin("wifi", false);
        prefs.putString("ssid", sync.ssid);
        prefs.putString("pass", sync.pass);
        prefs.end();
        
        Serial.println("[SYNC] Credentials Saved. Restarting Robot Eye...");
        delay(1000);
        ESP.restart();
    }
}

WebServer server(80);

void handleJPGStream() {
    WiFiClient client = server.client();
    String header = "HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
    server.sendContent(header);

    while (client.connected()) {
        camera_fb_t* fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("ERROR: Camera frame capture failed");
            break;
        }

        String partHeader = "--frame\r\nContent-Type: image/jpeg\r\n\r\n";
        server.sendContent(partHeader);

        size_t fb_len = fb->len;
        if (client.write(fb->buf, fb_len) != fb_len) {
            esp_camera_fb_return(fb);
            break;
        }

        server.sendContent("\r\n");
        esp_camera_fb_return(fb);
        delay(10);
    }
}

void handleRoot() {
    String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Transformer Vision Stream</title></head><body style='background-color:#111;color:#fff;text-align:center;'>";
    html += "<h1>🤖 Transformer Eye</h1>";
    html += "<img src='/stream' style='width:100%;max-width:800px;border-radius:10px;' />";
    html += "</body></html>";
    server.send(200, "text/html", html);
}

void handleFlash() {
    if (server.hasArg("val")) {
        int val = server.arg("val").toInt();
        digitalWrite(FLASH_GPIO_NUM, val ? HIGH : LOW);
        server.send(200, "text/plain", val ? "FLASH ON" : "FLASH OFF");
    } else {
        server.send(400, "text/plain", "MISSING VAL");
    }
}

void setup() {
    Serial.begin(115200);
    
    // 1. Load Saved WiFi or use Defaults
    prefs.begin("wifi", false);
    String ssid = prefs.getString("ssid", default_ssid);
    String pass = prefs.getString("pass", default_password);
    
    // 2. Initialize ESP-NOW Sync Listener
    WiFi.mode(WIFI_AP_STA);
    if (esp_now_init() == ESP_OK) {
        esp_now_register_recv_cb(onDataReceive);
        Serial.println("[SYNC] Wireless Sync Listener Active.");
    }

    // 3. Detailed Camera Initialization (RESTORED)
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    if (psramFound()) {
        config.frame_size = FRAMESIZE_SVGA;
        config.jpeg_quality = 10;
        config.fb_count = 2;
    } else {
        config.frame_size = FRAMESIZE_CIF;
        config.jpeg_quality = 12;
        config.fb_count = 1;
    }

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x\n", err);
        delay(3000);
        ESP.restart();
    }
    
    // 4. WiFi Connection Loop (Improved for Syncing)
    Serial.println("[WIFI] Connecting to: " + ssid);
    WiFi.begin(ssid.c_str(), pass.c_str());
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi Connected. IP: " + WiFi.localIP().toString());
        server.on("/", HTTP_GET, handleRoot);
        server.on("/stream", HTTP_GET, handleJPGStream);
        server.on("/flash", HTTP_GET, handleFlash);
        server.begin();
        Serial.println("Vision Stream Server Started.");
    } else {
        Serial.println("\n[WIFI] Connection Failed. Staying in Wireless Sync Mode...");
    }
    
    pinMode(FLASH_GPIO_NUM, OUTPUT);
    digitalWrite(FLASH_GPIO_NUM, LOW);
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        // Advanced: Auto-Bandwidth for 4G Hotspot
        static bool isOn4G = false;
        sensor_t * s = esp_camera_sensor_get();
        
        if (WiFi.SSID() == "Omni-Gateway" && !isOn4G) {
            s->set_framesize(s, FRAMESIZE_CIF);
            s->set_quality(s, 15);
            isOn4G = true;
            Serial.println("[VISION] 4G Mode Active: Lowering resolution to CIF.");
        } else if (WiFi.SSID() != "Omni-Gateway" && isOn4G) {
            s->set_framesize(s, FRAMESIZE_SVGA);
            s->set_quality(s, 10);
            isOn4G = false;
            Serial.println("[VISION] WiFi Mode Active: Restoring SVGA resolution.");
        }
        
        server.handleClient();
    }
}
