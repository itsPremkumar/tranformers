"""
🚶 HUMAN ROBOT — WALKING SIMULATION
================================================================
Animates a kinematic bipedal walking gait cycle in Fusion 360.
Captures screenshots of each walking phase.
"""

def run(context):
    import adsk.core
    import adsk.fusion
    import time
    import math
    import os

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        img_dir = r"C:\Users\PREM KUMAR\.gemini\antigravity\brain\b190ced2-aeac-4aa0-b4b4-450e86c3ff87\3D_MODEL\images"
        if not os.path.exists(img_dir): os.makedirs(img_dir)

        def take_screenshot(name):
            app.activeViewport.refresh()
            app.activeViewport.saveAsImageFile(os.path.join(img_dir, name), 1920, 1080)

        # ---------------------------------------------------------
        # FIND ALL KINEMATIC COMPONENTS
        # ---------------------------------------------------------
        def get_occ(name_pattern):
            for i in range(root.occurrences.count):
                occ = root.occurrences.item(i)
                if name_pattern in occ.name: return occ
            return None

        thigh_L = get_occ("Kinematic_Thigh_L")
        thigh_R = get_occ("Kinematic_Thigh_R")
        shin_L = get_occ("Kinematic_Shin_L")
        shin_R = get_occ("Kinematic_Shin_R")
        foot_L = get_occ("Kinematic_Foot_L")
        foot_R = get_occ("Kinematic_Foot_R")

        uarm_L = get_occ("Kinematic_UpperArm_L")
        uarm_R = get_occ("Kinematic_UpperArm_R")
        farm_L = get_occ("Kinematic_Forearm_L")
        farm_R = get_occ("Kinematic_Forearm_R")

        # ---------------------------------------------------------
        # ANIMATION HELPER
        # ---------------------------------------------------------
        def animate_rotation(occurrences, pivot_pt, axis_vec, total_deg, steps=10):
            rad_step = math.radians(total_deg / steps)
            for _ in range(steps):
                for occ in occurrences:
                    mat = occ.transform
                    rot = adsk.core.Matrix3D.create()
                    rot.setToRotation(rad_step, axis_vec, pivot_pt)
                    mat.transformBy(rot)
                    occ.transform = mat
                app.activeViewport.refresh()
                adsk.doEvents()
                time.sleep(0.01)

        v_x = adsk.core.Vector3D.create(1, 0, 0)
        
        # Static Pivots relative to Torso
        p_hip_L = adsk.core.Point3D.create(-6, 0, 9)
        p_hip_R = adsk.core.Point3D.create(6, 0, 9)
        p_shoulder_L = adsk.core.Point3D.create(-5, 0, 23)
        p_shoulder_R = adsk.core.Point3D.create(5, 0, 23)

        # Dynamic Knee Pivot Calculator
        def get_dyn_knee(hip_x, pitch_deg):
            dist = 5.0 # Z=9 to Z=4
            rad = math.radians(pitch_deg)
            new_y = dist * math.sin(rad)
            new_z = 9.0 - dist * math.cos(rad)
            return adsk.core.Point3D.create(hip_x, new_y, new_z)

        # ---------------------------------------------------------
        # WALKING CYCLE (TREADMILL)
        # ---------------------------------------------------------
        # Set Isometric Camera
        try:
            cam = app.activeViewport.camera
            cam.eye = adsk.core.Point3D.create(-40, -40, 30)
            cam.target = adsk.core.Point3D.create(0, 0, 10)
            cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
            cam.isSmoothTransition = False
            app.activeViewport.camera = cam
        except: pass

        take_screenshot("walk_0_neutral.png")

        cycles = 1 # Do 1 full cycle for screenshots
        for c in range(cycles):
            # Phase 1: Right Leg Steps Forward, Left Arm Swings Forward
            animate_rotation([thigh_R, shin_R, foot_R], p_hip_R, v_x, -30, 15)
            animate_rotation([thigh_L, shin_L, foot_L], p_hip_L, v_x, 15, 10)
            animate_rotation([uarm_L, farm_L], p_shoulder_L, v_x, -30, 10)
            animate_rotation([uarm_R, farm_R], p_shoulder_R, v_x, 30, 10)
            
            p_knee_R_dyn = get_dyn_knee(6, -30)
            animate_rotation([shin_R, foot_R], p_knee_R_dyn, v_x, 30, 10)
            take_screenshot(f"walk_{c}_step1_right_up.png")
            
            # Phase 2: Right Leg Plants
            animate_rotation([shin_R, foot_R], p_knee_R_dyn, v_x, -30, 10)
            animate_rotation([thigh_R, shin_R, foot_R], p_hip_R, v_x, 30, 15)
            animate_rotation([thigh_L, shin_L, foot_L], p_hip_L, v_x, -15, 10)
            animate_rotation([uarm_L, farm_L], p_shoulder_L, v_x, 30, 10)
            animate_rotation([uarm_R, farm_R], p_shoulder_R, v_x, -30, 10)
            take_screenshot(f"walk_{c}_step2_right_down.png")
            
            # Phase 3: Left Leg Steps Forward, Right Arm Swings Forward
            animate_rotation([thigh_L, shin_L, foot_L], p_hip_L, v_x, -30, 15)
            animate_rotation([thigh_R, shin_R, foot_R], p_hip_R, v_x, 15, 10)
            animate_rotation([uarm_R, farm_R], p_shoulder_R, v_x, -30, 10)
            animate_rotation([uarm_L, farm_L], p_shoulder_L, v_x, 30, 10)
            
            p_knee_L_dyn = get_dyn_knee(-6, -30)
            animate_rotation([shin_L, foot_L], p_knee_L_dyn, v_x, 30, 10)
            take_screenshot(f"walk_{c}_step3_left_up.png")
            
            # Phase 4: Left Leg Plants
            animate_rotation([shin_L, foot_L], p_knee_L_dyn, v_x, -30, 10)
            animate_rotation([thigh_L, shin_L, foot_L], p_hip_L, v_x, 30, 15)
            animate_rotation([thigh_R, shin_R, foot_R], p_hip_R, v_x, -15, 10)
            animate_rotation([uarm_R, farm_R], p_shoulder_R, v_x, 30, 10)
            animate_rotation([uarm_L, farm_L], p_shoulder_L, v_x, -30, 10)
            take_screenshot(f"walk_{c}_step4_left_down.png")

        print("Walking animation complete!")

    except Exception as e:
        import traceback
        print(f"Error: {str(e)}\n{traceback.format_exc()}")
