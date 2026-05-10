# 🦾 SENTINEL TRANSFORMER - BUILD SCRIPT EXECUTION GUIDE

## 📋 Quick Start (3 Steps)

### Step 1: Open Fusion 360
- Launch **Autodesk Fusion 360**
- Create a **New Design** (File → New)
- Keep the design open and active

### Step 2: Load the Build Script
1. Go to **Scripts and Add-ons** (top menu)
2. Click **Create** → **Python** (or **New Script**)
3. Copy-paste the entire contents of `sentinel_transformer_complete_build.py`
4. Click **Run** (or press the green play button)

### Step 3: Review the Output
- The script will display a success message with the assembly structure
- Check the **Model Tree** (left panel) - you should see:
  ```
  ├─ 01_Torso_Chassis
  ├─ 02_Leg_1_Assembly
  ├─ 02_Leg_2_Assembly
  ├─ 02_Leg_3_Assembly
  ├─ 02_Leg_4_Assembly
  ├─ 03_Head_Gimbal_2DOF
  └─ 04_Transformation_Armor
  ```

---

## 🔧 Customization via User Parameters

Once the script runs, you can **resize ANY component instantly**:

### How to Modify Parameters:
1. **Model** tab → **Modify** → **Change Parameters**
2. Or right-click in the **Model Tree** → **Edit Parameters**

### Key Parameters You Can Adjust:

| Parameter | Default | Unit | Purpose |
| :--- | :--- | :--- | :--- |
| `CHASSIS_LENGTH` | 6.0 | cm | Torso length |
| `CHASSIS_WIDTH` | 4.0 | cm | Torso width |
| `CHASSIS_HEIGHT` | 5.0 | cm | Height for 3S battery (11.1V) |
| `WALL_THICKNESS` | 0.24 | cm | **FDM wall thickness (2.4mm)** |
| `UPPER_LEG_LENGTH` | 8.0 | cm | Upper leg segment (Hip to Knee) |
| `LOWER_LEG_LENGTH` | 6.0 | cm | Lower leg (Knee to Foot) |
| `LEG_WIDTH` | 1.5 | cm | Leg profile width |
| `LEG_DEPTH` | 1.2 | cm | Leg profile depth |
| `MG996R_LENGTH` | 4.1 | cm | High-torque servo for hips/knees |
| `MG996R_WIDTH` | 2.0 | cm | |
| `MG996R_HEIGHT` | 2.1 | cm | |
| `MG90S_LENGTH` | 2.3 | cm | Micro servo for ankles/head |
| `MG90S_WIDTH` | 1.1 | cm | |
| `MG90S_HEIGHT` | 1.2 | cm | |
| `MOTOR_WHEEL_DIAMETER` | 6.5 | cm | **65mm wheel for Yellow DC motors** |
| `MOTOR_MOUNT_LENGTH` | 4.0 | cm | Motor housing length |
| `HEAD_WIDTH` | 4.0 | cm | Head gimbal width |
| `HEAD_HEIGHT` | 3.0 | cm | Head gimbal height |
| `HEAD_DEPTH` | 3.0 | cm | Head gimbal depth |
| `ARMOR_THICKNESS` | 0.3 | cm | Armor plate thickness (3mm) |
| `ARMOR_CHAMFER` | 0.5 | cm | Chamfer for aerodynamic edges |
| `BATTERY_LENGTH` | 5.5 | cm | 3S battery pack length |
| `BATTERY_WIDTH` | 3.3 | cm | 3S battery pack width |
| `BATTERY_HEIGHT` | 2.0 | cm | 3S battery pack height |

**Example**: Need a smaller robot? Change `CHASSIS_LENGTH` from 6.0 to 4.0 cm → Everything scales automatically!

---

## 🎯 Assembly Breakdown

### 01_Torso_Chassis
**Purpose**: Main body + battery bay + internal ribs

**Features**:
- Hollow interior (2.4mm walls for FDM)
- Internal ribs for battery support (prevents sagging)
- Mountpoint for head gimbal (top)
- Leg attachment points (4 corners)

**Specifications**:
- **Dimensions**: 120mm (L) × 80mm (W) × 50mm (H)
- **Wall Thickness**: 2.4mm (optimized for FDM)
- **Battery Bay**: Houses 3S 11.1V pack (5.5×3.3×2.0cm)
- **Internal Ribs**: 2x horizontal + 2x vertical for reinforcement

**Components Inside**:
- 3S 11.1V Li-Ion Battery (3000mAh+)
- L298N Motor Driver (direct 11.1V input)
- 10A Buck Converter (11V → 5-6V for servos)
- 2× PCA9685 PWM Servo Drivers (on I2C bus)
- INA219 Current/Voltage Sensor
- ESP32 (Motion Controller) with voltage regulation
- ESP32-S3 (Comm Controller) with WiFi/Audio

---

### 02_Leg_X_Assembly (×4)
**Purpose**: 4-DOF articulated legs with motor drive wheels

**Kinematic Structure (Per Leg)**:

```
Hip Pan (MG996R, ±45°)
    ↓
Hip Tilt (MG996R, ±30°)
    ↓
Knee Flex (MG996R, 0-135°)
    ↓
Ankle Stabilizer (MG90S, ±15°)
    ↓
Motor Foot (Yellow DC Geared Motor + 65mm Wheel)
```

**Features**:
- **Hip Pan**: Servo mount for MG996R (lateral steering in Car Mode)
- **Hip Tilt**: Servo mount for MG996R (body lift in Robot Mode)
- **Knee Flex**: Servo mount for MG996R (primary transformation joint)
- **Ankle Stabilizer**: Servo mount for MG90S (foot leveling)
- **Motor Foot**: Housing for Yellow DC Motor + wheel axle

**Leg Positioning** (in Car Mode - Top-Down View):
```
      Front
     ┌─────┐
   ╱   │ │   ╲
  ╱ LF │ │ RF ╲
 ╱  1  │ │  2  ╲
│             │
│  [Torso]    │
│             │
 ╲  3  │ │  4  ╱
  ╲ LR │ │ RR ╱
   ╲   │ │   ╱
     ┌─────┐
      Rear

LF=Front-Left, RF=Front-Right, LR=Rear-Left, RR=Rear-Right
```

**FDM Printing Notes**:
- Print legs with **50% infill (Gyroid/Grid)** for servo torque resistance
- Support orientation: Wheel axis horizontal
- No support needed inside servo mounts (internal geometry)

---

### 03_Head_Gimbal_2DOF
**Purpose**: Articulated head for AI interaction, tucks into chassis for car mode

**2-DOF Structure**:

```
Pan Servo (MG90S, ±90°)  → Left/Right head rotation
    ↓
Tilt Servo (MG90S, ±45°) → Up/Down head tilt
    ↓
Face Plate (40×30mm) → Mounts OLED + ESP32-CAM
```

**Front-Facing Components**:
- **SSD1306 0.96" OLED**: AI "eyes" + mood display
- **ESP32-CAM**: Vision for gesture recognition + face tracking
- **HC-SR04 Ultrasonic**: Personal space safety (front sensing)

**Tuck-Away Mechanism**:
- In **CAR MODE**: Head tilts down & pan rotates to align with chest cavity
- In **ROBOT MODE**: Head tilts up & pans to track objects/faces
- Internal ribs in chassis hold head when tucked

**Specifications**:
- **Head Frame**: 40mm (W) × 30mm (H) × 30mm (D)
- **Pan Range**: ±90° (full side-to-side)
- **Tilt Range**: ±45° (can tuck flat)
- **Servo**: 2× MG90S (micro servos for light weight)

---

### 04_Transformation_Armor
**Purpose**: Aerodynamic armor plates that align into vehicle body in Car Mode

**Plate Configuration** (3-piece system):

```
ROBOT MODE (Standing):
     [Head]
    [Armor_Front]
  [Armor_Left][Armor_Right]
  [Armor_Rear]
  [Legs×4]

CAR MODE (Low-Profile):
  Armor plates align → forms Vehicle Chassis
  Head tucked into chest
  Legs retracted/leveled
  ~6cm×4cm×3cm profile (low center of gravity)
```

**Armor Pieces**:

1. **Front Wedge Plate** (Nose Cone)
   - Chamfered edge for aerodynamics
   - Aligns with torso front
   - Houses ultrasonic sensor (obstacle avoidance)

2. **Left & Right Side Plates**
   - Parallel to torso sides
   - 6.0cm × 0.5cm × 2.4mm thickness
   - Covers leg internals when aligned

3. **Rear Wedge Plate** (Tail)
   - Chamfered edge for aerodynamics
   - Aligns with torso rear
   - Completes vehicle profile

**FDM Printing Notes**:
- Print armor plates with **20% infill** (they're primarily structural)
- **Chamfer angle**: 45° → smooth aerodynamic flow
- **Wall thickness**: 2.4mm (matches vehicle body specs)
- Consider flexible TPU for edges (impact protection)

---

## 🔋 Power & Electronics Integration

### Power Distribution Plan

```
11.1V 3S Battery
        │
        ├─→ L298N Motor Driver (11.1V DIRECT)
        │        └─→ 4× Yellow DC Motors
        │
        ├─→ 10A Buck Converter
        │        └─→ 5-6V Rail
        │             ├─→ PCA9685 #1 (Channels 0-15)
        │             │    ├─→ Hip Pan (Ch 0-3: Legs 1-4)
        │             │    ├─→ Hip Tilt (Ch 4-7)
        │             │    └─→ Knee Flex (Ch 8-11)
        │             │
        │             └─→ PCA9685 #2 (Channels 0-15)
        │                  ├─→ Ankle Stabilizer (Ch 0-3)
        │                  ├─→ Head Pan/Tilt (Ch 4-5)
        │                  └─→ [Reserved for expansion] (Ch 6-15)
        │
        └─→ 3.3V LDO (from 5V rail)
                 ├─→ ESP32 (Motion Controller)
                 ├─→ ESP32-S3 (Comm Controller)
                 ├─→ MPU6050 IMU (Geometric Center of Torso)
                 ├─→ INA219 Current/Voltage Sensor
                 ├─→ SSD1306 OLED (I2C)
                 ├─→ HC-SR04 Ultrasonic (GPIO)
                 └─→ MAX98357A I2S Audio (Voice)
```

### I2C Bus (Internal Network)
```
SDA (Pin 21) ────┬─→ PCA9685 #1 (Address: 0x40)
SCL (Pin 22) ────┤─→ PCA9685 #2 (Address: 0x41)
                 ├─→ MPU6050 (Address: 0x68)
                 └─→ SSD1306 OLED (Address: 0x3C)

⚠️  NOTE: Keep I2C wires SHORT (<15cm) to avoid signal noise
```

---

## 📤 Exporting for 3D Printing

### Export Steps:
1. **Select component** in Model Tree
2. **File** → **Export** → **STL**
3. **Choose settings**:
   - **Refinement**: High (0.1mm tolerance)
   - **Single file**: YES (for each component)

### Recommended Print Order:

1. **Torso_Chassis** (largest, print first)
   - Infill: 20% (Gyroid)
   - Supports: YES (for battery ribs)
   - Time: ~12-16 hours @ 200 microns

2. **Leg_1, Leg_2, Leg_3, Leg_4** (in parallel if possible)
   - Infill: 50% (Grid/Gyroid) ← **IMPORTANT for servo torque**
   - Supports: Minimal (wheel axle holes)
   - Time: ~8-10 hours each

3. **Head_Gimbal_2DOF**
   - Infill: 30%
   - Supports: YES (servo mounts)
   - Time: ~3-4 hours

4. **Transformation_Armor** (4 pieces)
   - Infill: 20% (Gyroid)
   - Supports: Minimal
   - Time: ~2-3 hours total

**Total Print Time**: ~50-60 hours (if sequential)

---

## ⚙️ Servo Mounting Verification

After printing, **verify servo clearances**:

### Hip Pan Servo (MG996R)
- Mount point: Upper leg base
- **Verify**: 4.1cm × 2.0cm × 2.1cm fits in mounting bracket
- **Cable routing**: Route toward hip joint

### Hip Tilt Servo (MG996R)
- Mount point: Hip joint (between upper & lower leg)
- **Verify**: Clearance for ±30° tilt motion
- **Cable routing**: Route downward along leg

### Knee Flex Servo (MG996R)
- Mount point: Knee joint
- **Verify**: Primary articulation point, needs full clearance
- **Cable routing**: Route toward ankle

### Ankle Stabilizer (MG90S)
- Mount point: Foot/motor mount
- **Verify**: 2.3cm × 1.1cm × 1.2cm servo fits
- **Cable routing**: Route to motor foot

### Head Pan/Tilt Servos (2× MG90S)
- Mount points: Head gimbal pan axis + tilt axis
- **Verify**: 180° pan range, 90° tilt range
- **Cable routing**: Route to head frame exit

---

## 🧪 Testing Checklist

Before assembly:

- [ ] All prints are clean (no stringy bits)
- [ ] Servo mounts fit actual MG996R/MG90S servos
- [ ] Motor foot wheelbase supports 65mm wheel diameter
- [ ] Torso battery bay fits 3S pack (5.5×3.3×2.0cm)
- [ ] Head gimbal pan servo can rotate 180°
- [ ] Leg segments stack smoothly without binding
- [ ] Armor plates align flush in car mode
- [ ] All clearances meet 2.4mm wall thickness spec

---

## 💡 Pro Tips

1. **Use nylon screws** (M2 × 8mm) for servo mounts → prevents stripping
2. **Servo lubricant**: Light machine oil on servo arms before mounting
3. **Cable management**: Use 3mm spiral wrap in all components
4. **Waterproofing**: Coat 3S battery terminals with hot glue (prevents shorts)
5. **IMU placement**: MPU6050 must be **perfectly level** in torso geometric center
6. **Transformation sequence**: Test in reverse order (Armor → Ankles → Knees → Hips → Head)

---

## 📞 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| Script won't run | Ensure Fusion is fully open & active; try restarting Fusion |
| User Parameters not created | Check UI message box for errors; run script again |
| Leg components missing | Some sketches may fail; manually add missing segments |
| Armor plates misaligned | Verify `CHASSIS_LENGTH/WIDTH` match armor plate dimensions |
| Head gimbal won't tuck | Check `HEAD_HEIGHT` parameter vs torso cavity size |
| Motor foot too large | Reduce `MOTOR_WHEEL_DIAMETER` parameter |

---

## 📚 Next Steps

1. ✅ Run build script (creates parametric assembly)
2. ✅ Review Model Tree structure
3. ✅ Adjust User Parameters as needed
4. ✅ Export each component as STL
5. ✅ Slice for 3D printer (Cura/PrusaSlicer)
6. ✅ Print components in recommended order
7. ✅ Assemble servos → test DOF ranges
8. ✅ Mount motors → test wheels
9. ✅ Integrate electronics → test power/I2C
10. ✅ Perform transformation sequence → validate car/robot mode

---

**Mission Status**: Ready for fabrication. 🚀

Happy building!
