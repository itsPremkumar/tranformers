#ifndef CONFIG_H
#define CONFIG_H

#define WIFI_SSID "one"          // Local Wi-Fi Network Name
#define WIFI_PASS "12345678"     // Local Wi-Fi Password
#define USE_OTA   true           // Enable wireless updates

// ==========================================
// 🚀 FEATURE TOGGLES
// ==========================================
#define USE_MPU6050      true    // Enable 6-axis IMU for balance and fall detection
#define USE_ULTRASONIC   true    // Enable HC-SR04 for obstacle and hole detection
#define USE_SERVO_DRIVER true    // Enable PCA9685 I2C driver for limbs
#define ENABLE_WALKING   true    // Enable humanoid gait algorithms
#define ENABLE_TRANSFORM true    // Enable mechanical transformation sequence

// ==========================================
// 📌 PIN ASSIGNMENTS (Motion Controller)
// ==========================================
// L298N DC Motor Driver Pins
#define MOTOR_IN1 27
#define MOTOR_IN2 26
#define MOTOR_IN3 25
#define MOTOR_IN4 33
#define MOTOR_ENA 14             // PWM for speed control A
#define MOTOR_ENB 12             // PWM for speed control B

// HC-SR04 & Head Servos
#define TRIG_PIN 5               // Ultrasonic Trigger
#define ECHO_PIN 18              // Ultrasonic Echo
#define PAN_SERVO_PIN 13         // Head Pan (GPIO 13)
#define TILT_SERVO_PIN 16        // Head Tilt (GPIO 16)

// ==========================================
// ⚙️ SYSTEM SETTINGS
// ==========================================
#define SERIAL_BAUD 115200       // Standard baud rate
#define COMM_LINK_RX 4           // Connect to Comm Controller TX
#define COMM_LINK_TX 15          // Connect to Comm Controller RX
#define BATTERY_PIN 34           // Analog battery voltage sensor
#define CURRENT_PIN 35           // Analog current sensor
#define HEARTBEAT_TIMEOUT_MS 2500 // Safety halt if no comms for 2.5s

// Advanced Obstacle Avoidance Thresholds
#define SAFE_DISTANCE_CM    38
#define CAUTION_DISTANCE_CM 55
#define BLOCK_DISTANCE_CM   26
#define MAX_DISTANCE_CM     250
#define REVERSE_TIME_MS     280
#define TURN_BASE_MS_MIN    170
#define TURN_BASE_MS_MAX    540
#define SERVO_STEP_DELAY_MS 8

#endif

