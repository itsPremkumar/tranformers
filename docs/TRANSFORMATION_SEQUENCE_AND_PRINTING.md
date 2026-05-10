# 🔄 SENTINEL TRANSFORMER - CONVERSION SEQUENCE & POST-PROCESSING

## 🤖 STATE MACHINE: Robot ↔ Car Transformation

### Overview

The Sentinel operates in **3 primary states**:

```
┌──────────────────────────────────────────────────────┐
│               STATE_ROBOT (Default)                  │
│  - High center of gravity                            │
│  - Upright humanoid posture                          │
│  - Head gimbal pan/tilt enabled (vision tracking)    │
│  - Optimized for AI interaction & obstacle sensing   │
│  - Speed: Moderate (walking at 0.5 m/s max)         │
└──────────────────────────────────────────────────────┘
                         ↓ (User command: TRANSFORM)
                    STATE_TRANSFORM
              (Synchronized servo sequence)
                         ↓ (30-45 seconds)
┌──────────────────────────────────────────────────────┐
│                STATE_CAR (Target)                    │
│  - Low center of gravity                             │
│  - Horizontal vehicle profile (~6cm height)          │
│  - Head tucked into chest cavity                     │
│  - Armor plates aligned (aerodynamic form)           │
│  - Optimized for 4WD racing (2+ m/s sustained)      │
└──────────────────────────────────────────────────────┘
                         ↓ (User command: ROBOT)
                    STATE_TRANSFORM
              (Reverse servo sequence)
                         ↓ (30-45 seconds)
            Return to STATE_ROBOT (pose reset)
```

---

## 📋 ROBOT → CAR Transformation Sequence

This is the **exact order** that servos move during transformation. Execute sequentially to maintain stability.

### Phase 1: Safety Shutdown (0-3 seconds)
```
Action: Stop all wheel motors
Reason: Prevent movement during transformation
Command:
  L298N Motor A & B → PWM = 0 (No output)
  Result: All 4 wheels locked/braked
  
Status: ✓ Robot is stationary
```

### Phase 2: Head Tuck (3-8 seconds)
```
Servo: Head Tilt (MG90S on PCA9685 #2 Ch 5)
Target: 1000µs (fully tilted down)
Current: 1500µs (center/forward)
Motion: Head tilts down 90° to align with chest cavity

Timing:
  - Move at 45°/sec (reduces servo strain)
  - Duration: ~2 seconds
  - Final Position: Head hidden in chassis, OLED facing downward

Status: ✓ Head secured in chest cavity
Reason: Protects camera, ensures low profile for car mode
```

### Phase 3: Head Pan Neutral (8-10 seconds)
```
Servo: Head Pan (MG90S on PCA9685 #2 Ch 4)
Target: 1500µs (center neutral)
Current: Varies (previous state)
Motion: Head rotates to face forward

Timing:
  - Move at 45°/sec
  - Duration: ~1-2 seconds
  
Status: ✓ Head centered and tucked
Reason: Ensures symmetric profile for vehicle body
```

### Phase 4: Knee Extension (10-20 seconds)
```
Servos: Knee Flex (4× MG996R on PCA9685 #1 Ch 8-11)
        One per leg: Legs 1, 2, 3, 4
Target: 1350µs (135° extension)
Current: 1500µs (center position, ~90°)
Motion: All 4 knees simultaneously extend outward

Timing:
  - Move at 90°/sec (strong servo for smooth motion)
  - Duration: ~1-2 seconds per leg
  - All legs in parallel (synchronized)
  
Configuration After:
  - Legs now fully extended horizontally
  - Foot wheels perpendicular to torso
  - Ankle servos can now level wheels
  
Status: ✓ Legs fully extended
Reason: Flattens robot profile, prepares feet for motor drive
```

### Phase 5: Hip Tilt Raise (20-30 seconds)
```
Servos: Hip Tilt (4× MG996R on PCA9685 #1 Ch 4-7)
        One per leg: Legs 1, 2, 3, 4
Target: 1800µs (maximum tilt/raise)
Current: 1500µs (neutral)
Motion: All 4 legs simultaneously lift upward on hip joint

Timing:
  - Move at 90°/sec
  - Duration: ~2 seconds
  - All legs in parallel
  
Configuration After:
  - Torso and leg segments form compact vehicle chassis
  - Center of gravity drops significantly
  - Knees/ankles fully locked in extended position
  
Status: ✓ Body compressed into car profile
Reason: Lowers center of gravity, reduces vehicle height to ~3cm
```

### Phase 6: Hip Pan Alignment (30-35 seconds)
```
Servos: Hip Pan (4× MG996R on PCA9685 #1 Ch 0-3)
        One per leg: Legs 1, 2, 3, 4
Target: 1500µs (neutral/forward alignment)
Current: Varies (previous state)
Motion: All 4 legs rotate to align wheels parallel

Timing:
  - Move at 45°/sec
  - Duration: ~1-2 seconds
  - All legs synchronized
  
Configuration After:
  - All 4 wheels aligned in same direction (0° relative to torso)
  - Ready for coordinated 4WD motion
  
Status: ✓ Wheel alignment completed
Reason: Ensures all motors spin same direction for forward/reverse
```

### Phase 7: Ankle Leveling (35-40 seconds)
```
Servos: Ankle Stabilizer (4× MG90S on PCA9685 #2 Ch 0-3)
        One per leg: Legs 1, 2, 3, 4
Target: 1500µs (perfectly level)
Current: Varies (likely already level from robot mode)
Motion: Fine adjustment of wheel pitch

Timing:
  - Move at 30°/sec (fine precision)
  - Duration: ~1 second
  - All legs synchronized
  
Configuration After:
  - All 4 wheels perfectly parallel to ground
  - No wheel toe-in or camber (critical for straight-line driving)
  - Vehicle ready for motor engagement
  
Status: ✓ Wheels level and ready for drive
Reason: Ensures maximum wheel contact for traction/speed
```

### Phase 8: Motor Engagement (40-45 seconds)
```
Action: Enable Yellow DC motors
Command:
  L298N Motor A (Front wheels): PWM = 200 (80% speed), IN1/IN2 = Forward
  L298N Motor B (Rear wheels):  PWM = 200 (80% speed), IN1/IN2 = Forward
  
Timing:
  - Gradual acceleration: 0 → 200 over 2 seconds
  - Smooth motion without traction loss
  - All 4 wheels spinning in unison
  
Final State:
  ✓ TRANSFORMATION COMPLETE
  ✓ Vehicle moving at ~1.2 m/s (constant 80% PWM)
  ✓ Ready for racing / autonomous navigation
  
Status: STATE_CAR ACTIVE
```

---

## 📊 Transformation Timeline

```
Time (sec)   Servo Action              Status
─────────────────────────────────────────────────────
0-3          Stop Motors              ✓ Safety
3-8          Head Tilt Down           ✓ Tucking
8-10         Head Pan Center          ✓ Alignment
10-20        Knee Extension           ✓ Profile flatten
20-30        Hip Tilt Raise           ✓ Height reduction
30-35        Hip Pan Align            ✓ Wheel coordination
35-40        Ankle Leveling           ✓ Final balance
40-45        Motor Engagement         ✓ TRANSFORMATION COMPLETE
─────────────────────────────────────────────────────
TOTAL DURATION: 45 seconds (worst-case, all sequential)
OPTIMAL DURATION: 20-30 seconds (with full parallelization)
```

---

## 🔙 CAR → ROBOT Reverse Sequence

Simply reverse all steps in opposite order with different PWM targets:

```
Phase 1: Motor Cutoff (0-2 sec)
  └─ L298N PWM → 0 (wheels brake)

Phase 2: Ankle Reset (2-4 sec)
  └─ Ankle servos → 1500µs (level)

Phase 3: Hip Pan Reset (4-6 sec)
  └─ Hip Pan → varies per leg (wheel orientation)

Phase 4: Hip Tilt Lower (6-15 sec)
  └─ Hip Tilt → 1200µs (lower body)

Phase 5: Knee Flex (15-25 sec)
  └─ Knees → 1500µs (bend back to 90°)

Phase 6: Head Pan Reset (25-27 sec)
  └─ Head Pan → 1500µs (center)

Phase 7: Head Tilt Up (27-32 sec)
  └─ Head Tilt → 1800µs (look forward)

Phase 8: Vision Ready (32-35 sec)
  └─ ESP32-CAM stream active, OLED displays face
  └─ Ready for AI interaction

TOTAL DURATION: 35 seconds → STATE_ROBOT ACTIVE
```

---

## 🧪 Pre-Transformation Checklist

Before executing STATE_TRANSFORM:

1. **Wheel Contact**
   - [ ] All 4 wheels touching ground (not tilted)
   - [ ] Weight distributed evenly on all 4 feet
   - [ ] No obstructions under chassis

2. **Servo Health**
   - [ ] All 18 servos responsive to test pulse
   - [ ] No audible grinding/buzzing from servos
   - [ ] Power draw <8A (confirmed with INA219)

3. **Motor Status**
   - [ ] All 4 wheel motors spin freely (no locked wheels)
   - [ ] Wheel alignment verified (pan at 1500µs)
   - [ ] L298N receives 11.1V input (confirmed with DMM)

4. **IMU Calibration**
   - [ ] MPU6050 mounted perfectly level
   - [ ] No tilt detected when stationary
   - [ ] Gyro drift <0.5°/sec

5. **Head Gimbal**
   - [ ] Head tilt servo can reach 1000µs (fully down)
   - [ ] Head pan servo can reach 1500µs (center)
   - [ ] No cable entanglement in servo arms

6. **Safety Systems**
   - [ ] Ultrasonic sensor (HC-SR04) functional
   - [ ] 30cm obstacle detection working
   - [ ] Emergency stop (GPIO) wired and tested

---

## 🖨️ 3D PRINTING GUIDE: From STL to Finished Part

### Preparation Phase

#### 1. STL Export & Validation
```
In Fusion 360:
  ├─ Right-click component → Export
  ├─ Format: STL (Binary)
  ├─ Refinement: HIGH (0.1mm tolerance)
  ├─ Single file per component
  └─ Save to: /output/stl_files/

STL Files to Export (in order):
  1. 01_Torso_Chassis.stl (largest)
  2. 02_Leg_1_Assembly.stl
  3. 02_Leg_2_Assembly.stl
  4. 02_Leg_3_Assembly.stl
  5. 02_Leg_4_Assembly.stl
  6. 03_Head_Gimbal_2DOF.stl
  7. 04_Transformation_Armor.stl (4 pieces)

Validate in Slicing Software:
  ├─ Load STL into Cura/PrusaSlicer
  ├─ Check for non-manifold geometry (repair if needed)
  ├─ Verify no thin walls (<2.4mm)
  └─ Auto-orient for optimal support placement
```

#### 2. Slicing Configuration (Cura / PrusaSlicer)

**Material**: PETG or PLA+ (PETG recommended for servo torque)

**Global Settings**:
```
Layer Height:         0.2mm (balance speed/detail)
Wall Thickness:       2.4mm (≥4 perimeters @ 0.6mm nozzle)
Top/Bottom Thickness: 1.2mm (6 layers)
```

**Component-Specific Settings**:

| Component | Infill | Pattern | Supports | Orientation |
| :--- | :--- | :--- | :--- | :--- |
| **Torso** | 20% | Gyroid | YES (ribs) | Flat base down |
| **Legs** | 50% | Grid | Minimal | Wheel axis horiz |
| **Head** | 30% | Gyroid | YES (gimbal) | Face down |
| **Armor** | 20% | Gyroid | Minimal | Flat surfaces down |

**Support Settings**:
```
Support Type:        Tree (uses less material)
Support Density:     15% (reduces cleanup)
Support Pattern:     Linear (easier removal)
Min Angle:           45° (support only where needed)
XY Separation:       0.2mm (clean breakaway)
```

**Adhesion**:
```
Type:         Brim (easy removal, prevents warping)
Width:        5mm (adequate for large parts)
```

---

### Printing Phase

#### Print Order Recommendation

**Group A (Priority 1)**: Torso Chassis
```
Est. Time: 14-18 hours @ 200µm
Filament: ~250g (test-print small bracket first)
Temp:     240°C nozzle, 80°C bed
Fan:      100% (after first 2 layers)
Notes:    - Watch for layer adhesion at 50% print
          - Internal ribs may need support cleanup
          - Cool fully before removing supports
```

**Group B (Parallel)**: All 4 Legs
```
Est. Time: 8-10 hours each
Filament: ~60g each
Temp:     240°C nozzle, 80°C bed
Fan:      80% (servo mounts are tight tolerance)
Notes:    - Print all 4 legs simultaneously if printer allows
          - Use same spool batch for color consistency
          - Servo mounts need precise dimensions
```

**Group C (After A & B)**: Head Gimbal
```
Est. Time: 3-4 hours
Filament: ~30g
Temp:     240°C nozzle, 80°C bed
Fan:      100% (small parts need good cooling)
Notes:    - Servo gimbal axis must be smooth (check diameter)
          - Support cleanup is critical here
```

**Group D (Minimal Time)**: Armor Plates
```
Est. Time: 2-3 hours (4 pieces)
Filament: ~40g total
Temp:     240°C nozzle, 80°C bed
Fan:      100%
Notes:    - Chamfered edges should be clean
          - Print all 4 pieces in one batch
          - Less critical than mechanical parts
```

**Total Print Time**: 55-75 hours (parallelized)

---

### Post-Processing Phase

#### Step 1: Support Removal (Patience Required)
```
For each part:
  1. Allow to cool to room temperature (easier removal)
  2. Use needle-nose pliers to break supports at base
  3. Sand removal marks with 120-grit sandpaper (circular motion)
  4. Repeat with 220-grit for smooth finish
  5. For servo mounts: Use small rotary tool to clean
  
⚠️  Critical: Don't damage servo mounting surfaces!
     Use light pressure on servo mount areas
```

#### Step 2: Dimensional Verification
```
For each component, verify with digital calipers:

Torso:
  ├─ Length (should be 120mm): Accept if 119-121mm
  ├─ Width (should be 80mm): Accept if 79-81mm
  ├─ Height (should be 50mm): Accept if 49-51mm
  └─ Wall thickness (should be 2.4mm): Accept if 2.2-2.6mm

Leg Servo Mounts:
  ├─ MG996R cavity (should be 41×20×21mm)
  │  └─ Accept if within 40-42mm length
  ├─ MG90S cavity (should be 23×11×12mm)
  │  └─ Accept if within 22-24mm length
  └─ Test-fit actual servos (should be snug, not loose)

Motor Foot Wheel Cavity:
  ├─ Diameter (should fit 65mm wheel): Accept if 64-66mm
  └─ Depth (should accommodate motor shaft): Accept if 3.8-4.2mm
```

#### Step 3: Servo Mount Preparation
```
For each servo mount cavity:

1. Clean cavity with compressed air
2. Test-fit servo (should be tight but not forced)
3. If loose:
   - Wrap servo body with electrical tape (0.1mm per wrap)
   - Re-test fit (should grip firmly)
   - Use as shim if cavity is oversized

4. If tight:
   - Sand interior with 220-grit on dowel
   - Test-fit again
   - ⚠️  Do NOT over-sand (will become useless)

5. Mark servo orientation:
   - Use paint pen to mark servo cable direction
   - Ensures cable routing is consistent during assembly
```

#### Step 4: Motor Foot Preparation
```
For each leg's motor foot:

1. Clean wheel cavity with compressed air
2. Test-fit 65mm wheel on motor shaft
3. If wheel binds:
   - Expand cavity diameter with rotary file (small increments)
   - Test between each pass
   - Goal: Wheel spins freely on shaft

4. Create mounting hole pattern for motor:
   - Motor has M3 bolt holes
   - Use M3 threaded inserts (heat-set) or direct tapping
   - Test-fit motor (should mount flush)

5. Cable routing groove:
   - If not printed, create groove with rotary tool
   - Route motor wires along leg to servo mounts
   - Use 3mm spiral wrap
```

#### Step 5: Surface Finishing (Optional)
```
For better aesthetics:

1. Vapor Smoothing (Acetone - PETG only):
   - Place part in sealed container with acetone vapor
   - 5-10 minutes exposure (don't oversoak)
   - Result: Glossy finish, improved appearance
   - ⚠️  May slightly shrink dimensions

2. Sanding & Painting:
   - Light sand with 400-grit for paint adhesion
   - Prime with gray plastic primer
   - Paint with automotive acrylic (metallic gray recommended)
   - Clear coat with matte varnish

3. Armor Plate Weathering (Optional):
   - Add black wash to chamfered edges
   - Dry-brush silver on raised surfaces
   - Result: Sci-fi military appearance
```

#### Step 6: Final Assembly Prep
```
1. Torso:
   - [ ] Verify internal ribs intact (no print failures)
   - [ ] Clean battery bay: use soft brush
   - [ ] Test battery pack fit (5.5×3.3×2.0cm)
   - [ ] Verify servo mount points (4 corners)

2. All Legs:
   - [ ] Verify servo mount fit with actual servos
   - [ ] Test motor mount with actual motor
   - [ ] Check wheel clearance (no rubbing on leg)
   - [ ] Verify servo cable exit points

3. Head Gimbal:
   - [ ] Test pan servo range (180°)
   - [ ] Test tilt servo range (90°)
   - [ ] Verify OLED face mounting area
   - [ ] Check tuck-away fit into torso cavity

4. Armor Plates:
   - [ ] Check alignment flush against torso
   - [ ] Verify chamfer edges are smooth
   - [ ] No gaps or misalignment in car mode
```

---

## ⚡ Quick Print Settings Reference

**Cura Profiles for Sentinel**:
```
Sentinel_Torso:
  - Layer Height: 0.2mm
  - Infill: 20% Gyroid
  - Wall Thickness: 2.4mm
  - Nozzle: 240°C, Bed: 80°C
  - Speed: 50mm/s

Sentinel_Legs:
  - Layer Height: 0.2mm
  - Infill: 50% Grid
  - Wall Thickness: 2.4mm
  - Nozzle: 240°C, Bed: 80°C
  - Speed: 45mm/s (slower for servo mount precision)

Sentinel_Head:
  - Layer Height: 0.15mm (finer detail)
  - Infill: 30% Gyroid
  - Wall Thickness: 2.4mm
  - Nozzle: 240°C, Bed: 80°C
  - Speed: 40mm/s (fine details)

Sentinel_Armor:
  - Layer Height: 0.2mm
  - Infill: 20% Gyroid
  - Wall Thickness: 2.0mm (non-critical)
  - Nozzle: 240°C, Bed: 80°C
  - Speed: 50mm/s
```

Save these profiles in Cura → Add profiles by name

---

## 🔍 Common Print Failures & Solutions

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| Warped leg base | Bed adhesion loss | Increase brim width to 8mm, raise bed temp to 85°C |
| Servo mount too loose | Over-extrusion, insufficient infill | Reduce nozzle temp by 2°C, increase infill to 55% |
| Servo mount too tight | Under-extrusion, too much infill | Increase nozzle temp by 2°C, reduce infill to 45% |
| Cracked servo bracket | Impact stress during print | Use 30% infill instead of 50%, add support under bracket |
| Motor wheel cavity uneven | Print wobble at Z-axis | Recalibrate bed leveling, reduce first layer speed to 20mm/s |
| Long stringing between parts | Retraction settings | Enable retraction, set distance to 5mm, speed 40mm/s |
| Broken support cleanup | Aggressive removal | Let part cool fully, use fine pliers, small circular motions |

---

## ✅ Pre-Assembly Final Checklist

Before moving to servo/motor integration:

- [ ] All 7 STL files printed and cleaned
- [ ] Support removal complete (no marks on critical surfaces)
- [ ] Dimensional verification passed for all components
- [ ] Servo mounts test-fit with actual MG996R & MG90S servos
- [ ] Motor feet test-fit with actual yellow motors
- [ ] Wheel cavity diameter verified (64-66mm)
- [ ] Head gimbal tuck-away tested in torso cavity
- [ ] Armor plates align flush in car mode
- [ ] All cable routing grooves clear and accessible
- [ ] No sharp edges or burrs (sand as needed)
- [ ] Components ready for electronics integration

---

**You are now ready for servo/motor mounting and electronic integration!** 🦾

Continue to: `SERVO_MOTOR_SPECIFICATIONS.md` for final wiring and calibration.

