# 🔌 SENTINEL TRANSFORMER - SERVO & MOTOR SPECIFICATIONS

## 📋 Complete Servo Inventory (18-DOF)

### MG996R High-Torque Servos (12 total)
**Used for**: Hip Pan, Hip Tilt, Knee Flex (×3 servos per leg × 4 legs = 12 servos)

| Specification | Value |
| :--- | :--- |
| **Dimensions** | 41mm (L) × 20mm (W) × 21mm (H) |
| **Weight** | 55g |
| **Torque** | 13 kg·cm @ 6V |
| **Speed** | 0.18 sec/60° @ 6V |
| **Range** | ±45° to ±180° (varies by application) |
| **Operating Voltage** | 4.8V ~ 6.0V |
| **Connector** | JR (standard male connector) |
| **Mounting Holes** | M2 × 2 (on servo arms) |

**Mounting in Design**:
```
Hip Pan:   Servo base bolted to leg upper segment
Hip Tilt:  Servo base bolted to hip joint (between upper/lower leg)
Knee Flex: Servo base bolted to knee joint (primary transform articulation)

All 3 servos per leg driven via:
  PCA9685 PWM Driver #1 (Channels 0-11)
  ├─ Legs 1-4 Hip Pan (Channels 0-3)
  ├─ Legs 1-4 Hip Tilt (Channels 4-7)
  └─ Legs 1-4 Knee Flex (Channels 8-11)
```

**Cable Requirements**:
- **Signal**: 3 wires per servo (GND, 5V, PWM signal)
- **Power**: Shared 5-6V rail from Buck Converter
- **Total Amperage**: 12 servos × 0.3A (stall) = 3.6A max
- **Buck Converter**: 10A @ 5V/6V (ample headroom)

**Calibration Procedure**:
1. Power servos WITHOUT any load
2. Set all PWM to **1.5ms pulse** (90° center position)
3. Mount servo arms at 90° (perpendicular to servo body)
4. Install servo into bracket
5. Verify smooth ±45° range of motion

---

### MG90S Micro Servos (6 total)
**Used for**: Ankle Stabilizer (×1 per leg × 4 legs = 4 servos) + Head Pan/Tilt (×2 servos)

| Specification | Value |
| :--- | :--- |
| **Dimensions** | 23mm (L) × 11mm (W) × 12mm (H) |
| **Weight** | 9g |
| **Torque** | 2.4 kg·cm @ 6V |
| **Speed** | 0.12 sec/60° @ 6V |
| **Range** | ±45° to ±90° |
| **Operating Voltage** | 4.8V ~ 6.0V |
| **Connector** | JR (standard male connector) |
| **Mounting Holes** | Single M2 hole (on servo body) |

**Mounting in Design**:
```
Ankle Stabilizer: 4× MG90S (one per leg) → Motor foot leveling
  Driven via: PCA9685 #2 Channels 0-3
  Function: ±15° ankle pitch for stability in car mode

Head Pan:        1× MG90S → 180° left/right rotation
  Driven via: PCA9685 #2 Channel 4
  Function: Side-to-side head tracking

Head Tilt:       1× MG90S → 90° up/down rotation
  Driven via: PCA9685 #2 Channel 5
  Function: Head pitch for tuck-away in car mode
```

**Cable Requirements**:
- **Signal**: 3 wires per servo (GND, 5V, PWM signal)
- **Power**: Shared 5-6V rail
- **Total Amperage**: 6 servos × 0.15A (stall) = 0.9A max
- **Combined with MG996R**: 3.6A + 0.9A = 4.5A (well within 10A converter)

**Calibration Procedure**:
1. Connect to PCA9685 channel
2. Set PWM to 1.5ms (center position)
3. Mount servo arm horizontally
4. Install into bracket
5. Test ±45° range of motion

---

## 🏎️ Yellow DC Geared Motor Specifications

**Used for**: 4WD Drive System (one motor per leg foot)

| Specification | Value |
| :--- | :--- |
| **Motor Type** | DC Geared Motor |
| **Gear Ratio** | 1:48 (high-torque, low-speed) |
| **Operating Voltage** | 3V ~ 12V (recommend 11.1V for max speed) |
| **No-Load Speed (@ 12V)** | ~270 RPM |
| **Stall Torque (@ 12V)** | ~1200 mN·m (12 kg·cm) |
| **Current (@ 12V)** | ~0.35A (no-load), ~1.5A (stall) |
| **Shaft Diameter** | 2mm (typical D-shaft) |
| **Wheel Compatibility** | 65mm diameter (included) |
| **Mounting** | M3 bolt holes on motor case |

**Mounting in Design**:
```
Motor Foot Assembly (per leg):
  ├─ Yellow DC Motor (horizontal axis)
  ├─ 65mm wheel (4WD mobility)
  ├─ Bracket (3D-printed, M3 bolt mount)
  └─ Cable routing to L298N driver

Motor Placement (4WD Layout):
  Front-Right (Leg 1)  ←→  Front-Left (Leg 2)
       │                        │
   [11.1V                   11.1V]
       │                        │
   [L298N Driver]
       │                        │
  Rear-Right (Leg 3)  ←→  Rear-Left (Leg 4)

Driven via: L298N Dual H-Bridge
  Motor A: Front pair (Legs 1 & 2) → 1x motor
  Motor B: Rear pair (Legs 3 & 4) → 1x motor
  
Actually: 4 independent motors (all 4 wheels can spin independently)
  Each motor on separate H-bridge output
  GPIO control: IN1, IN2, EN pins on ESP32
```

**Power Delivery**:
- **Direct 11.1V**: Battery → L298N → Motors
- **Max Current**: 4 motors × 1.5A = 6A stall
- **Bus Voltage**: Stable 11.1V (no buck converter needed for motors)

**Motor Control**:
- **Direction**: H-bridge IN1/IN2 pins (forward/reverse)
- **Speed**: PWM on EN (Enable) pin (0-255 PWM levels)
- **Driver**: L298N Dual H-Bridge (2 motors per L298N, need 2× L298Ns for 4 motors)

---

## 🔌 Complete Wiring Schematic

### Power Rails

```
3S Li-Po Battery (11.1V, 3000mAh+)
│
├─── HIGHWAY A (11.1V DIRECT) ───────────────────┐
│                                                 │
└─ L298N Motor Driver                            │
   ├─ Ground (GND) ──────────────────────────────┤
   ├─ +12V (from battery) ───────────────────────┤
   ├─ Motor A Output (Legs 1&2 front wheels)     │
   └─ Motor B Output (Legs 3&4 rear wheels)      │
                                                  │
                                                  │
├─── HIGHWAY B (5-6V via 10A Buck) ──┐           │
│                                     │           │
│  INPUT: 11.1V ────→ [Buck Converter]←─ GND ────┤
│                     └─ OUTPUT: 5-6V │           │
│                                     │           │
│  To PCA9685 #1 (Channels 0-11)      │           │
│  │ ├─ Hip Pan servos (Ch 0-3)       │           │
│  │ ├─ Hip Tilt servos (Ch 4-7)      │           │
│  │ └─ Knee Flex servos (Ch 8-11)    │           │
│  │                                  │           │
│  │ To PCA9685 #2 (Channels 0-5)     │           │
│  │ ├─ Ankle servos (Ch 0-3)         │           │
│  │ ├─ Head Pan (Ch 4)               │           │
│  │ └─ Head Tilt (Ch 5)              │           │
│  │                                  │           │
│  └─ GND ─────────────────────────────┤           │
│                                                  │
├─── HIGHWAY C (3.3V Logic) ────────┐             │
│                                   │             │
│  FROM 5V Rail [LDO Reg] → 3.3V   │             │
│  │                               │             │
│  ├─ ESP32 (Motion Controller)    │             │
│  │  ├─ VCC (3.3V) ──────────────┤             │
│  │  ├─ GND ──────────────────────┤             │
│  │  ├─ GPIO 21 (SDA) ───→ I2C    │             │
│  │  └─ GPIO 22 (SCL) ───→ I2C    │             │
│  │                               │             │
│  ├─ ESP32-S3 (Comm Controller)   │             │
│  │  ├─ VCC (3.3V) ──────────────┤             │
│  │  ├─ GND ──────────────────────┤             │
│  │  ├─ GPIO 21 (SDA) ───→ I2C    │             │
│  │  └─ GPIO 22 (SCL) ───→ I2C    │             │
│  │                               │             │
│  ├─ MPU6050 (IMU) [Torso Center] │             │
│  │  ├─ VCC (3.3V) ──────────────┤             │
│  │  ├─ GND ──────────────────────┤             │
│  │  ├─ SDA ──────→ I2C Bus       │             │
│  │  └─ SCL ──────→ I2C Bus       │             │
│  │                               │             │
│  ├─ SSD1306 OLED (Head Face)     │             │
│  │  ├─ VCC (3.3V) ──────────────┤             │
│  │  ├─ GND ──────────────────────┤             │
│  │  ├─ SDA ──────→ I2C Bus       │             │
│  │  └─ SCL ──────→ I2C Bus       │             │
│  │                               │             │
│  ├─ HC-SR04 Ultrasonic (Front)   │             │
│  │  ├─ VCC (5V from buck) ──────────────┐     │
│  │  ├─ GND ──────────────────────┤      │     │
│  │  ├─ TRIG → GPIO 12 (ESP32) ────┐     │     │
│  │  └─ ECHO → GPIO 13 (ESP32) ────┤     │     │
│  │                               │     │     │
│  ├─ INA219 (Power Monitor)       │     │     │
│  │  ├─ VCC (3.3V) ──────────────┤     │     │
│  │  ├─ GND ──────────────────────┤     │     │
│  │  ├─ SDA ──────→ I2C Bus       │     │     │
│  │  └─ SCL ──────→ I2C Bus       │     │     │
│  │                               │     │     │
│  └─ MAX98357A (Audio Amp)        │     │     │
│     ├─ VCC (5V) ──────────────────────┤     │
│     ├─ GND ──────────────────────┤    │     │
│     ├─ BCLK (I2S) → GPIO 26      │    │     │
│     ├─ DIN (I2S)  → GPIO 25      │    │     │
│     ├─ LRCLK (I2S)→ GPIO 27      │    │     │
│     └─ Speaker Out → 3W Speaker  │    │     │
│                                  └────┴─────┤
└──────────────────────────────────────────────┘
```

---

## 📡 I2C Bus Configuration

```
I2C Master (ESP32 Pins 21/22)
│
├─ 4.7kΩ pull-up resistor (SDA to 3.3V)
├─ 4.7kΩ pull-up resistor (SCL to 3.3V)
│
└─ Slave Devices (addresses):
   │
   ├─ PCA9685 #1 (Address: 0x40)
   │  ├─ SDA ←→ ESP32 GPIO 21
   │  ├─ SCL ←→ ESP32 GPIO 22
   │  ├─ A0-A5 jumpers: All LOW (default address 0x40)
   │  └─ Serves Channels 0-15 (Hip Pan/Tilt/Knee)
   │
   ├─ PCA9685 #2 (Address: 0x41)
   │  ├─ SDA ←→ ESP32 GPIO 21
   │  ├─ SCL ←→ ESP32 GPIO 22
   │  ├─ A0 jumper: HIGH (address 0x41)
   │  └─ Serves Channels 0-15 (Ankle/Head/Reserved)
   │
   ├─ MPU6050 (Address: 0x68)
   │  ├─ SDA ←→ ESP32 GPIO 21
   │  ├─ SCL ←→ ESP32 GPIO 22
   │  └─ AD0 pin: GND (default address 0x68)
   │
   ├─ SSD1306 OLED (Address: 0x3C)
   │  ├─ SDA ←→ ESP32 GPIO 21
   │  ├─ SCL ←→ ESP32 GPIO 22
   │  └─ I2C address: 0x3C (OLED default)
   │
   └─ INA219 (Address: 0x40)
      ├─ SDA ←→ ESP32 GPIO 21
      ├─ SCL ←→ ESP32 GPIO 22
      └─ A0-A1 jumpers: Both LOW (default 0x40)
         
      ⚠️  CONFLICT: PCA9685 #1 and INA219 both use 0x40!
      Solution: Set INA219 address to 0x41 (A0 HIGH) and change PCA9685 #2 to 0x42
```

---

## 🎮 PWM Channel Mapping (PCA9685)

### PCA9685 #1 (Address: 0x40) - Hip & Knee Servos

| Channel | Servo | Leg | Function | Range (1000-2000µs) |
| :--- | :--- | :--- | :--- | :--- |
| **0** | MG996R | Leg 1 (FR) | Hip Pan | 1000-2000 |
| **1** | MG996R | Leg 2 (FL) | Hip Pan | 1000-2000 |
| **2** | MG996R | Leg 3 (RR) | Hip Pan | 1000-2000 |
| **3** | MG996R | Leg 4 (RL) | Hip Pan | 1000-2000 |
| **4** | MG996R | Leg 1 (FR) | Hip Tilt | 1000-2000 |
| **5** | MG996R | Leg 2 (FL) | Hip Tilt | 1000-2000 |
| **6** | MG996R | Leg 3 (RR) | Hip Tilt | 1000-2000 |
| **7** | MG996R | Leg 4 (RL) | Hip Tilt | 1000-2000 |
| **8** | MG996R | Leg 1 (FR) | Knee Flex | 1000-2000 |
| **9** | MG996R | Leg 2 (FL) | Knee Flex | 1000-2000 |
| **10** | MG996R | Leg 3 (RR) | Knee Flex | 1000-2000 |
| **11** | MG996R | Leg 4 (RL) | Knee Flex | 1000-2000 |
| **12-15** | — | — | **RESERVED** | — |

### PCA9685 #2 (Address: 0x42) - Ankle & Head Servos

| Channel | Servo | Function | Range (1000-2000µs) |
| :--- | :--- | :--- | :--- |
| **0** | MG90S | Leg 1 (FR) Ankle | 1200-1800 |
| **1** | MG90S | Leg 2 (FL) Ankle | 1200-1800 |
| **2** | MG90S | Leg 3 (RR) Ankle | 1200-1800 |
| **3** | MG90S | Leg 4 (RL) Ankle | 1200-1800 |
| **4** | MG90S | Head Pan | 1000-2000 |
| **5** | MG90S | Head Tilt | 1000-2000 |
| **6-15** | — | **RESERVED** | — |

---

## 🎯 Servo Calibration & Pulse Widths

### Standard Servo Pulse Widths

| Position | Pulse Width | Notes |
| :--- | :--- | :--- |
| **Full Left/Back** | 1000µs | -90° from center |
| **Left/Back** | 1250µs | -45° from center |
| **Center/Neutral** | 1500µs | 0° (home position) |
| **Right/Forward** | 1750µs | +45° from center |
| **Full Right/Forward** | 2000µs | +90° from center |

### Motor Speed Control (L298N PWM)

```
PWM Value (0-255)  →  Motor Speed
    0                 Stopped
   64                 25% speed
  128                 50% speed
  192                 75% speed
  255                 100% speed

Direction Control (GPIO pins):
  IN1=HIGH, IN2=LOW   → Forward
  IN1=LOW, IN2=HIGH   → Reverse
  IN1=LOW, IN2=LOW    → Brake
  IN1=HIGH, IN2=HIGH  → Brake
```

---

## ✅ Pre-Assembly Checklist

- [ ] All servos tested individually at 90° (1.5ms)
- [ ] MG996R: 4.1cm × 2.0cm × 2.1cm mounts verified
- [ ] MG90S: 2.3cm × 1.1cm × 1.2cm mounts verified
- [ ] Yellow DC motors: 65mm wheel compatibility confirmed
- [ ] L298N connections tested with 11.1V input
- [ ] Buck converter output: 5.0-6.0V stable @ 10A draw
- [ ] PCA9685 #1 & #2: I2C addresses configured (0x40 & 0x42)
- [ ] MPU6050: Mounted perfectly level in torso geometric center
- [ ] All wires color-coded (Red=5V, Black=GND, Yellow=Signal)
- [ ] I2C bus: Pull-up resistors (4.7kΩ each on SDA/SCL)

---

**Next Step**: Proceed to assembly with servo mounting verification! 🦾

