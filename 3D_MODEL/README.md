# 🦾 Omni-Morph 3D Model: Production Transformer Robot

This directory contains the fully verified, mechanically-perfect 3D CAD design for the Omni-Morph Transformer Robot. It is modeled specifically for **Autodesk Fusion 360** and generated procedurally using the Autodesk Fusion API.

## 📂 Directory Structure

```text
3D_MODEL/
├── README.md                           # This documentation
├── images/
│   ├── transformer_fusion360_model.png # Render of the Humanoid CAD
│   ├── view_iso.png                    # Render of the Car Mode
│   └── ...                             # Multi-angle renders
├── scripts/
│   ├── build_production_transformer.py # Static Humanoid generation
│   ├── build_car_mode_transformer.py   # Static Car Mode generation
│   ├── build_kinematic_transformer.py  # Builds robot with independent components
│   └── animate_transformation.py       # Live UI Animation script
└── docs/
    └── MECHANICAL_DIMENSIONS.md        # Detailed dimensional breakdown
```

## 🎬 Live UI Transformation Animation

To verify that the robot's limbs do not collide during the physical transformation arc, a live kinematic animation script is provided.

**How to watch the animation in Fusion 360:**
1. Open **Autodesk Fusion 360**.
2. Run `build_kinematic_transformer.py`. This builds the robot, but separates the Thighs, Shins, Arms, and Head into independent Occurrences.
3. Once built, run `animate_transformation.py`.
4. A message box will appear. Click OK. 
5. The script will apply rotation matrices in a mathematical loop, physically folding the robot step-by-step on your screen exactly as the ESP32 will drive the real servos!

## 🛠️ How to Generate the Static 3D Models

**Method 1: Direct Execution in Fusion 360 (Recommended)**
1. Open **Autodesk Fusion 360**.
2. Go to **Utilities** → **Add-Ins** → **Scripts and Add-Ins** (or press `Shift + S`).
3. Click the `+` icon next to "My Scripts" to add a new script folder.
4. Navigate to `c:\one\tranformers\3D_MODEL\scripts\` and select the `build_production_transformer.py` file.
5. Select the script in the list and click **Run**.
6. The script will take ~30-60 seconds to build the entire 16-servo robot.

## ⚙️ Robot Architecture & Kinematics

The robot is a Humanoid-to-Car transformer utilizing **22 Degrees of Freedom (DOF)**.

### Component Breakdown
The generated model is organized into 9 top-level mechanical assemblies in the Fusion 360 browser tree:
1. `01_Torso_Chassis`: The core. Houses the 3S LiPo battery, ESP32, and features Optimus Prime chest aesthetics.
2. `01b_Pelvis`: The hip junction.
3. `02_Leg_L_Assembly` & `02_Leg_R_Assembly`: The lower limbs containing the dual-motor 4WD tandem drive train.
4. `03_Head_Gimbal_2DOF`: The pan/tilt articulating head.
5. `04_Arm_L_Assembly` & `04_Arm_R_Assembly`: The arms containing the front steering drive wheels.
6. `05_Transformation_Armor`: The exterior vehicle shell panels (bumper, skirts, spoiler).

### Actuator Inventory
- **10× MG996R Servos (High Torque)**: Shoulders, Hips, Knees, Waist, Chest-Fold.
- **6× MG90S Servos (Micro Precision)**: Elbows, Ankles, Head Pan/Tilt.
- **6× TT Gear Motors (Yellow)**: 2 on the forearms (front wheels), 4 on the shins (rear tandem wheels).

## 📐 Dimensional Fixes & Clearances

This production model has been rigorously validated for physical clearances:

1. **Tandem Wheel Spacing (Rear Legs):**
   - **Problem:** Two 65mm wheels placed too close together will intersect and grind.
   - **Solution:** The lower leg (Shin) was extended to **14.0cm**. The two TT motors are mounted at Z-offsets of -1.5cm and -8.5cm. This exactly **7.0cm distance** guarantees a perfect **5mm gap** between the 65mm diameter tires.

2. **Servo Cavity Encapsulation:**
   - **Problem:** MG996R bodies (41x20x21mm) were clipping through thin 25mm structural brackets.
   - **Solution:** Structural brackets (Thighs, Shoulders) were increased to **45mm × 35mm** cross-sections. This allows the servos to sit completely enclosed without compromising structural integrity.

3. **Pivot Point Alignment:**
   - **Problem:** Joints must hinge exactly on the servo output shaft (horn).
   - **Solution:** The mathematical center of rotation for all overlapping brackets (like the knee joint between the Thigh and Shin) has been mathematically mapped to the `cx, cy, cz` offset of the servo horn. When the servo turns 135 degrees, the leg folds perfectly without the metal/plastic geometries clipping.

## 🖨️ Exporting for 3D Printing

Once generated in Fusion 360:
1. Right-click any of the 9 top-level components (e.g., `01_Torso_Chassis`).
2. Select **Save As Mesh** (or Export as STL).
3. Set Refinement to **High**.
4. Import into Cura or PrusaSlicer.
5. Print heavy load-bearing joints (Legs, Pelvis) with **50% Infill**. Print armor panels with **20% Infill**.
