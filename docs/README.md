# 🦾 Omni-Class AUTONOMOUS TRANSFORMER
## Complete Build Documentation

---

## 📦 What You Have

This package contains **4 comprehensive documents** and **1 complete Python script** for building a fully functional Humanoid Transformer Robot in Fusion 360.

### File Inventory

```
📁 Omni-Morph_transformer_project/
│
├─ 🐍 Omni-Morph_transformer_complete_build.py
│  └─ Complete Fusion 360 Python script (executes in ~30 seconds)
│     • Creates 7 components (torso, 4 legs, head, armor)
│     • Adds 24 user parameters for full customization
│     • Optimized for FDM 3D printing
│
├─ 📋 Omni-Morph_BUILD_INSTRUCTIONS.md
│  └─ Step-by-step execution guide
│     • How to run the script in Fusion 360
│     • User parameter descriptions (complete reference)
│     • Assembly breakdown with specifications
│     • Export and slicing recommendations
│
├─ 🔌 SERVO_MOTOR_SPECIFICATIONS.md
│  └─ Detailed hardware specifications
│     • MG996R servo specs (12× for hips/knees)
│     • MG90S servo specs (6× for ankles/head)
│     • Yellow DC motor specs (4× for wheels)
│     • Complete wiring diagram (3-highway power)
│     • I2C bus configuration
│     • PWM channel mapping for all 18 DOF
│
├─ 🔄 TRANSFORMATION_SEQUENCE_AND_PRINTING.md
│  └─ Transformation logic & 3D printing guide
│     • Complete 8-phase transformation sequence
│     • Robot ↔ Car state machine (detailed timing)
│     • Pre-transformation checklist
│     • FDM printing guide (slicing settings, print order)
│     • Post-processing (support removal, finishing)
│     • Common print failures & solutions
│
├─ 🚀 advanced_features_v2.md
│  └─ Advanced Software Enhancements (v2.0)
│     • OTA Updates, Smart Battery Management
│     • Gyro-Assisted Drive, Terrain Detection
│     • Lip-Sync & Fall Recovery
│
└─ This README.md
   └─ Master navigation guide
```

---

## 🚀 Quick Start (5 Minutes)

### 1. Open Fusion 360
- Launch Autodesk Fusion 360
- Create **New Design** (File → New)

### 2. Run the Build Script
- **Scripts and Add-ons** → **Create** → **New Python Script**
- Copy-paste entire contents of `Omni-Morph_transformer_complete_build.py`
- Click **Run**

### 3. Review the Model Tree
You'll see this structure appear:
```
✓ 01_Torso_Chassis (120×80×50mm)
✓ 02_Leg_1_Assembly (4-DOF)
✓ 02_Leg_2_Assembly (4-DOF)
✓ 02_Leg_3_Assembly (4-DOF)
✓ 02_Leg_4_Assembly (4-DOF)
✓ 03_Head_Gimbal_2DOF (tuck-away)
✓ 04_Transformation_Armor (4 plates)
```

### 4. Customize (Optional)
- Right-click in Model Tree → **Edit Parameters**
- Adjust `CHASSIS_LENGTH`, `WALL_THICKNESS`, etc.
- Model updates in real-time

### 5. Export for 3D Printing
- Right-click each component → **Export** → **STL**
- Use Cura/PrusaSlicer with settings from **PRINTING GUIDE**

---

## 📚 Documentation Guide

### For Different Audiences

**"I just want to build it!"**
→ Read: `Omni-Morph_BUILD_INSTRUCTIONS.md` (Section: Quick Start + Assembly Breakdown)

**"I need to customize the dimensions"**
→ Read: `Omni-Morph_BUILD_INSTRUCTIONS.md` (Section: Customization via User Parameters)

**"I need wiring & electronics details"**
→ Read: `SERVO_MOTOR_SPECIFICATIONS.md` (all sections)

**"I need to 3D print the parts"**
→ Read: `TRANSFORMATION_SEQUENCE_AND_PRINTING.md` (Section: 3D Printing Guide)

**"How does the transformation work?"**
→ Read: `TRANSFORMATION_SEQUENCE_AND_PRINTING.md` (Section: State Machine & Transformation Sequence)

---

## 🏗️ Project Overview

### What is This?

**Omni-Class Transformer** is an 11.1V (3S) Autonomous Humanoid Robot that physically converts into a car.

- **Robot Mode**: Upright humanoid with AI vision & interaction
- **Car Mode**: Low-profile 4WD vehicle optimized for racing

### Key Specifications

| Aspect | Details |
| :--- | :--- |
| **Power** | 11.1V 3S Li-Ion Battery (3000mAh+) |
| **Servo Actuators** | 18-DOF (12× MG996R + 6× MG90S) |
| **Drive Motors** | 4× Yellow DC Geared (1:48 ratio) |
| **Dimensions (Robot)** | 120mm (L) × 80mm (W) × 50mm (H) |
| **Dimensions (Car)** | 120mm × 80mm × 30mm (compressed profile) |
| **AI Controllers** | 2× ESP32 + 1× ESP32-CAM + PC backend |
| **Sensors** | IMU, Ultrasonic, OLED display, Camera |
| **Material** | PETG/PLA+ (FDM 3D printed) |
| **Wall Thickness** | 2.4mm (optimized for strength) |
| **Print Time** | ~55-75 hours total (all components) |

---

## 🎯 18-DOF Breakdown

### 4 Legs × 4-DOF Each = 16-DOF

```
Each Leg:
  1. Hip Pan (MG996R) ......... ±45° lateral steering
  2. Hip Tilt (MG996R) ....... ±30° body lift
  3. Knee Flex (MG996R) ...... 0-135° primary transform
  4. Ankle Stabilizer (MG90S) . ±15° foot leveling
  
Plus Motor Drive:
  × 1 Yellow DC Motor per foot → 4WD mobility
```

### 2-DOF Head Gimbal

```
Head:
  1. Pan (MG90S) ............. ±90° left/right
  2. Tilt (MG90S) ............ ±45° up/down
  
Components:
  • SSD1306 OLED (AI eyes)
  • ESP32-CAM (vision)
  • HC-SR04 Ultrasonic (safety)
```

---

## 📡 Electronics Architecture

### The 3-Highway Power System

```
Battery (11.1V)
    │
    ├─→ HIGHWAY A: Direct 11.1V → L298N → 4 DC Motors
    ├─→ HIGHWAY B: 5-6V Buck → PCA9685 → 18 Servos
    └─→ HIGHWAY C: 3.3V LDO → ESP32s + Sensors
```

### Servo Distribution

```
PCA9685 #1 (Address 0x40):        PCA9685 #2 (Address 0x42):
├─ Ch 0-3: Hip Pan (4 legs)       ├─ Ch 0-3: Ankle (4 legs)
├─ Ch 4-7: Hip Tilt (4 legs)      ├─ Ch 4: Head Pan
└─ Ch 8-11: Knee (4 legs)         └─ Ch 5: Head Tilt
```

### I2C Bus

```
Connected Devices (I2C Address):
• PCA9685 #1 (0x40) - PWM for hips/knees
• PCA9685 #2 (0x42) - PWM for ankles/head
• MPU6050 (0x68) - IMU balance sensor
• SSD1306 (0x3C) - OLED display
• INA219 (0x41) - Power monitor
```

---

## 🔄 Transformation: Robot ↔ Car

### Timeline: 45 seconds total

```
ROBOT MODE (Upright Humanoid)
  ↓
[1] Stop motors (3 sec)
[2] Tuck head down (5 sec)
[3] Center head pan (2 sec)
[4] Extend knees (10 sec)
[5] Raise hips (10 sec)
[6] Align wheel steering (5 sec)
[7] Level ankles (5 sec)
[8] Engage motors (2 sec)
  ↓
CAR MODE (Low-Profile Vehicle)
  ↓
[Reverse sequence to return]
  ↓
ROBOT MODE
```

---

## 🖨️ 3D Printing Summary

### Recommended Order

1. **Torso** (18 hours) → Foundation piece
2. **4 Legs** (8-10 hours each, parallel) → Main articulation
3. **Head** (4 hours) → AI interface
4. **Armor** (3 hours, 4 pieces) → Aesthetic/protection

### Print Settings by Component

| Component | Infill | Pattern | Time |
| :--- | :--- | :--- | :--- |
| Torso | 20% | Gyroid | 14-18h |
| Legs (×4) | 50% | Grid | 8-10h each |
| Head | 30% | Gyroid | 3-4h |
| Armor (×4) | 20% | Gyroid | 2-3h total |

### Key Optimization

- **Torso**: 20% → Light but strong (ribs handle battery weight)
- **Legs**: 50% → High servo torque requires maximum structure
- **Head**: 30% → Balance weight (servo-driven)
- **Armor**: 20% → Non-critical, aesthetic only

---

## ✅ Pre-Assembly Verification

Before integrating electronics:

**Mechanical Assembly Complete?**
- [ ] All 7 components printed and cleaned
- [ ] Servo mounts fit MG996R (41×20×21mm) & MG90S (23×11×12mm)
- [ ] Motor feet accommodate Yellow motors + 65mm wheels
- [ ] Head gimbal tucking into torso cavity works smoothly
- [ ] Armor plates align flush in car mode

**Electronics Ready?**
- [ ] 11.1V 3S battery (3000mAh+) procured
- [ ] 10A Buck converter (11V → 5-6V) ready
- [ ] L298N motor driver tested
- [ ] 2× PCA9685 I2C drivers ready
- [ ] 2× ESP32 microcontrollers programmed
- [ ] All sensors (IMU, ultrasonic, OLED, camera) ready
- [ ] Wiring complete (per SERVO_MOTOR_SPECIFICATIONS.md)

---

## 📞 Usage Per Document

### Omni-Morph_BUILD_INSTRUCTIONS.md
- **Run the Fusion script step-by-step**
- Detailed parameter descriptions
- Assembly breakdown specifications
- Export workflow

### SERVO_MOTOR_SPECIFICATIONS.md
- **Electronics integration details**
- Servo mounting specifications (dimensions)
- Motor power requirements
- Complete wiring diagram
- I2C bus addresses
- PWM channel mapping
- Calibration procedures

### TRANSFORMATION_SEQUENCE_AND_PRINTING.md
- **Transformation automation logic**
- Robot/Car state machine
- Exact 8-phase sequence with timing
- Pre-transformation checklist
- **3D printing workflow**
- Slicing profiles
- Post-processing guide
- Print failure solutions

---

## 🎓 Learning Path

### Phase 1: CAD Design (Day 1)
1. Run `Omni-Morph_transformer_complete_build.py` in Fusion
2. Review the model tree structure
3. Explore user parameters
4. Export all 7 STL files

### Phase 2: 3D Printing (Days 2-7)
1. Slice components using Cura/PrusaSlicer
2. Print in order: Torso → Legs → Head → Armor
3. Clean up supports
4. Verify dimensions with calipers
5. Test servo mount fits

### Phase 3: Mechanical Assembly (Day 8)
1. Mount servos into brackets
2. Mount motors into feet
3. Test articulation ranges
4. Calibrate joint positions

### Phase 4: Electronics Integration (Days 9-10)
1. Solder power distribution (3-highway system)
2. Integrate controllers (ESP32s)
3. Connect I2C bus (sensors)
4. Test motor driver
5. Calibrate IMU

### Phase 5: Software & Testing (Days 11-14)
1. Flash ESP32 firmware
2. Test servo control via PCA9685
3. Verify motor operation
4. Calibrate transformation sequence
5. Test robot ↔ car conversion

### Phase 6: AI Integration (Days 15+)
1. Connect to PC backend
2. Enable vision processing
3. Test gesture recognition
4. Autonomous mode testing

---

## 🔗 File Dependencies

```
Omni-Morph_transformer_complete_build.py
  ↓
  Requires: Fusion 360 (with Python API)
  Produces: 7 3D components in model tree
  ↓
Omni-Morph_BUILD_INSTRUCTIONS.md
  ↓
  Reference for: Parameter meanings, assembly structure
  Produces: STL files for 3D printing
  ↓
SERVO_MOTOR_SPECIFICATIONS.md
  ↓
  Reference for: Electronics integration, wiring, calibration
  Used during: Phase 4 (Electronics Integration)
  ↓
TRANSFORMATION_SEQUENCE_AND_PRINTING.md
  ↓
  Reference for: 3D printing workflow + transformation logic
  Used during: Phase 2 (Printing) + Phase 5 (Software)
```

---

## 💡 Pro Tips

### Fusion 360 Design
1. **Parametric is powerful**: Change one value, everything updates
2. **Internal ribs are critical**: Prevent sag under servo torque
3. **Wall thickness (2.4mm)**: Minimum for FDM structural integrity

### 3D Printing
1. **Leg infill (50%)**: Non-negotiable for MG996R servo torque
2. **Print in stages**: Easier to troubleshoot issues
3. **Support cleanup**: Use needle pliers + light sanding

### Servo Mounting
1. **Test-fit every servo**: Print-to-CAD tolerance matters
2. **Smooth servo arms**: Light machine oil on rotation points
3. **Cable routing**: Plan before mounting (no pinching)

### Motor Integration
1. **Verify 11.1V delivery**: Measure at L298N inputs
2. **Wheel alignment**: Critical for straight-line driving
3. **Current monitoring**: INA219 sensor catches shorts

---

## 📜 Document Status

| Document | Status | Last Updated | Completeness |
| :--- | :--- | :--- | :--- |
| Build Script | ✅ Complete | 2026-05-05 | 100% |
| Build Instructions | ✅ Complete | 2026-05-05 | 100% |
| Servo/Motor Specs | ✅ Complete | 2026-05-05 | 100% |
| Transformation & Printing | ✅ Complete | 2026-05-05 | 100% |
| Master Documentation | ✅ Complete | 2026-05-05 | 100% |

---

## 🎯 Success Criteria

You'll know the project is complete when:

1. ✅ Fusion model fully parametric with all 24 user parameters
2. ✅ All 7 STL components export without errors
3. ✅ All parts 3D printed with correct infill densities
4. ✅ All 18 servos mounted and calibrated
5. ✅ All 4 motors spinning with coordinated control
6. ✅ Power system stable at 11.1V, 5-6V, 3.3V rails
7. ✅ Transformation sequence executes in 45 seconds
8. ✅ Robot mode: AI vision + gesture recognition active
9. ✅ Car mode: 4WD racing capability (2+ m/s sustained)
10. ✅ Seamless Robot ↔ Car conversion

---

## 🚀 Next Steps

**Immediately:**
1. Open `Omni-Morph_transformer_complete_build.py`
2. Run in Fusion 360
3. Check Model Tree for 7 components

**This Week:**
1. Review `Omni-Morph_BUILD_INSTRUCTIONS.md`
2. Export all STL files
3. Prepare slicing configuration

**Next Week:**
1. Start 3D printing in recommended order
2. Follow `TRANSFORMATION_SEQUENCE_AND_PRINTING.md` (Printing Guide section)

**Following Weeks:**
1. Assemble mechanics
2. Integrate electronics
3. Test transformation sequence
4. Deploy AI backend

---

## 📞 Troubleshooting Quick Links

**Script won't run?**
→ See Omni-Morph_BUILD_INSTRUCTIONS.md: Troubleshooting section

**Servo mount dimensions wrong?**
→ See SERVO_MOTOR_SPECIFICATIONS.md: Servo Inventory section

**3D print failed?**
→ See TRANSFORMATION_SEQUENCE_AND_PRINTING.md: Common Print Failures

**Transformation sequence timing?**
→ See TRANSFORMATION_SEQUENCE_AND_PRINTING.md: Transformation Timeline

**Wiring diagram?**
→ See SERVO_MOTOR_SPECIFICATIONS.md: Complete Wiring Schematic

---

## 🏆 Credits & Specifications

**Design Basis**:
- Omni-Class Autonomous Transformer (Master Architecture)
- 18-DOF Hybrid Four-Legged Chassis
- Dual-Mode Operation (Robot & Car)

**Target Components**:
- 12× MG996R High-Torque Servos
- 6× MG90S Micro Servos
- 4× Yellow DC Geared Motors (1:48)
- 2× ESP32 + 1× ESP32-CAM
- 11.1V 3S Li-Ion Battery System

**Optimization Goals**:
- Full FDM 3D printability
- Parametric customization
- 45-second transformation
- AI-powered autonomous operation

---

## 📄 License & Usage

All documentation and code are provided as-is for educational and hobby robotics use.

**No warranty is provided.** Use at your own risk, and always verify mechanical/electrical safety before operation.

---

**Happy building! 🦾**

*Mission: Build an autonomous humanoid robot that transforms into a car.*
*Status: Ready for fabrication.*

