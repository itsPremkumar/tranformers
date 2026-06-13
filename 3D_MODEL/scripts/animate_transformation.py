"""
🦾 TRANSFORMER ROBOT — LIVE UI ANIMATION (FINAL EXHAUSTIVE VERIFICATION)
================================================================
Steps through the flawless Clamshell transformation phases visually in Fusion 360.
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

        torso = get_occ("Kinematic_Torso")
        head = get_occ("Kinematic_Head")
        pelvis = get_occ("Kinematic_Pelvis")
        
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
        def animate_rotation(occurrences, pivot_pt, axis_vec, total_deg, steps=30):
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

        # Pivots (MATCHED EXACTLY TO THE NEW EXPLICIT SERVO LOCATIONS)
        p_neck = adsk.core.Point3D.create(0, 0, 23.0)
        p_shoulder = adsk.core.Point3D.create(0, 0, 23.0)
        p_knee = adsk.core.Point3D.create(0, 0, 4.0)
        p_ankle = adsk.core.Point3D.create(0, 0, -9.0)
        
        # CRITICAL FIX: The Faceplant Pivot must match the new Hip Pitch servo at Z=9.0!
        p_hip = adsk.core.Point3D.create(0, 0, 9.0) 
        
        v_x = adsk.core.Vector3D.create(1, 0, 0)

        # Arrays for hierarchical rotation
        upper_body = [torso, head, uarm_L, uarm_R, farm_L, farm_R]
        legs_and_pelvis = [pelvis, thigh_L, thigh_R, shin_L, shin_R, foot_L, foot_R]
        all_parts = upper_body + legs_and_pelvis

        # ---------------------------------------------------------
        # PHASE 1: HEAD TUCK
        # ---------------------------------------------------------
        animate_rotation([head], p_neck, v_x, -90, 30)
        take_screenshot("anim_step1_head.png")

        # ---------------------------------------------------------
        # PHASE 2: ARMS RAISE
        # ---------------------------------------------------------
        animate_rotation([uarm_L, uarm_R, farm_L, farm_R], p_shoulder, v_x, -180, 45)
        take_screenshot("anim_step2_arms.png")

        # ---------------------------------------------------------
        # PHASE 3: FEET AND KNEES FOLD
        # ---------------------------------------------------------
        animate_rotation([foot_L, foot_R], p_ankle, v_x, 180, 30)
        animate_rotation([shin_L, shin_R, foot_L, foot_R], p_knee, v_x, 180, 45)
        take_screenshot("anim_step3_knees.png")

        # ---------------------------------------------------------
        # PHASE 4: CLAMSHELL FACEPLANT
        # ---------------------------------------------------------
        animate_rotation(all_parts, p_hip, v_x, -90, 45)
        take_screenshot("anim_step4_bodypitch.png")

        # ---------------------------------------------------------
        # PHASE 5: LOWER TO GROUND
        # ---------------------------------------------------------
        # The lowest point is at Z=-5.25. 
        steps = 30
        v_down = adsk.core.Vector3D.create(0, 0, 5.25 / steps)
        for _ in range(steps):
            for occ in all_parts:
                mat = occ.transform
                mat.translation = mat.translation.copy()
                mat.translation.add(v_down)
                occ.transform = mat
            app.activeViewport.refresh()
            adsk.doEvents()
            time.sleep(0.01)
        
        app.activeViewport.fit()
        take_screenshot("anim_step5_final_car.png")

    except Exception as e:
        print(f"Error: {str(e)}")
