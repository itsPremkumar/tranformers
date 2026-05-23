#ifndef CONFIG_H
#define CONFIG_H

#define WIFI_SSID "one"          // Local Wi-Fi Network Name
#define WIFI_PASS "12345678"
#define DIAG_SSID "Omni-Motion-Test"  // Standalone diagnostic SSID
#define DIAG_PASS "12345678"          // Standalone diagnostic Password
#define USE_OTA   true           // Enable wireless updates

// ==========================================
// 🚀 FEATURE TOGGLES
// ==========================================
#define USE_MPU6050      true    // Enable 6-axis IMU for balance and fall detection
#define USE_ULTRASONIC   true    // Enable HC-SR04 for obstacle and hole detection
#define USE_SERVO_DRIVER true    // Enable PCA9685 I2C driver for limbs
#define ENABLE_WALKING   true    // Enable humanoid gait algorithms
#define ENABLE_TRANSFORM true    // Enable mechanical transformation sequence
#define USE_WDT          true    // Hardware Watchdog Protection
#define USE_SERVO_SLEEP  true    // Anti-Zitter (disable servos when idle)
#define USE_SOFT_START   true    // Ramped acceleration to protect battery
#define USE_I2C_HEALER   true    // Auto-recovery for I2C bus locks

// ==========================================
// 🏎️ ACKERMANN STEERING CONFIGURATION
// ==========================================
#define USE_ACKERMANN_STEERING true    // Set to true to use Servo + Motor instead of Differential
#define STEER_SERVO_PIN        2       // GPIO pin for steering servo
#define STEER_ANGLE_CENTER     90      // Centered position of steering servo (degrees)
#define STEER_ANGLE_MAX_LEFT   55      // Max left turn limit of steering servo (degrees)
#define STEER_ANGLE_MAX_RIGHT  125     // Max right turn limit of steering servo (degrees)


// ==========================================
// 🏗️ HARDWARE PROFILES
// ==========================================
#define PROFILE_CAR_ONLY    0   // Permanent 4-wheel robot
#define PROFILE_BIPED_ONLY  1   // Permanent Bipedal robot
#define PROFILE_CRAWLER_ONLY 2  // Permanent Crawler robot
#define PROFILE_OMNI_MORPH  3   // Full Transformer (Default)

// SET YOUR PROFILE HERE:
#define CURRENT_HARDWARE_PROFILE PROFILE_CAR_ONLY 

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
#define BATTERY_MULTIPLIER 4.0   // Calibration for voltage divider
#define CURRENT_PIN 35           // Analog current sensor
#define HEARTBEAT_TIMEOUT_MS 2500 // Safety halt if no comms for 2.5s

// Advanced Obstacle Avoidance Thresholds
#define SAFE_DISTANCE_CM    38
#define MIN_STOP_DISTANCE   15
#define CAUTION_DISTANCE_CM 55
#define BLOCK_DISTANCE_CM   26
#define MAX_DISTANCE_CM     250
#define REVERSE_TIME_MS     280
#define TURN_BASE_MS_MIN    170
#define TURN_BASE_MS_MAX    540
#define SERVO_STEP_DELAY_MS 8

// 🏎️ MOTOR SPEED PRESETS
#define SPEED_FAST          220  // Full speed cruising
#define SPEED_NORMAL        185  // Standard movement
#define SPEED_SLOW          145  // Cautious movement
#define SPEED_TURN          165  // Pivot/Turning power
#define SPEED_NAV_TARGET    190  // Auto-navigation speed

// Organic Motion Dynamics
#define ACCEL_LIMIT 10           // PWM units per update (Acceleration)
#define SMOOTHING_ALPHA 0.12     // Low-pass filter for jitter reduction

#endif

