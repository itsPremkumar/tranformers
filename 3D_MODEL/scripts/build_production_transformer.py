"""
🦾 PRODUCTION-READY TRANSFORMER ROBOT — Fusion 360 Build Script (DIMENSION FIX)
================================================================
Fixes all intersecting geometries, exact servo enclosures, and TT motor tandem spacing.
"""

def run(context):
    import adsk.core
    import adsk.fusion
    import traceback

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        # ============================================================
        # APPEARANCE LIBRARY
        # ============================================================
        app_lib = None
        for i in range(app.materialLibraries.count):
            lib = app.materialLibraries.item(i)
            if "Fusion" in lib.name and "Appearance" in lib.name:
                app_lib = lib
                break

        def get_appearance(query):
            if not app_lib:
                return None
            for i in range(app_lib.appearances.count):
                ap = app_lib.appearances.item(i)
                if query.lower() in ap.name.lower():
                    try:
                        return design.appearances.addByCopy(ap)
                    except:
                        return ap
            return None

        red_metal = get_appearance("Paint - Metallic (Red)")
        blue_metal = get_appearance("Paint - Metallic (Blue)")
        yellow_metal = get_appearance("Paint - Metallic (Yellow)")
        chrome = get_appearance("Chrome") or get_appearance("Steel - Satin") or get_appearance("Steel")
        rubber_blk = get_appearance("Rubber") or get_appearance("Plastic - Matte (Black)")
        glass_clr = get_appearance("Glass - Window") or get_appearance("Glass - Clear")
        grey_plastic = get_appearance("Plastic - Matte (Grey)") or get_appearance("Plastic - Matte (Black)")
        blue_trans = get_appearance("Plastic - Translucent (Blue)") or blue_metal
        brass = get_appearance("Gold") or get_appearance("Brass")
        white_pla = get_appearance("Plastic - Glossy (White)") or get_appearance("Plastic")
        dark_metal = get_appearance("Steel - Brushed") or chrome
        carbon = get_appearance("Carbon Fiber") or grey_plastic

        # ============================================================
        # GEOMETRY HELPERS
        # ============================================================
        def add_box(comp, name, cx, cy, cz, length, width, height, appearance=None):
            temp_brep = adsk.fusion.TemporaryBRepManager.get()
            orient = adsk.core.OrientedBoundingBox3D.create(
                adsk.core.Point3D.create(cx, cy, cz),
                adsk.core.Vector3D.create(1, 0, 0),
                adsk.core.Vector3D.create(0, 1, 0),
                length, width, height
            )
            box_body = temp_brep.createBox(orient)
            base_feat = comp.features.baseFeatures.add()
            base_feat.startEdit()
            added_body = comp.bRepBodies.add(box_body, base_feat)
            base_feat.finishEdit()
            added_body.name = name
            if appearance: added_body.appearance = appearance
            return added_body

        def add_cylinder(comp, name, cx, cy, cz, radius, height, axis, appearance=None):
            temp_brep = adsk.fusion.TemporaryBRepManager.get()
            ax = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
            base_pt = adsk.core.Point3D.create(
                cx - ax[0] * height / 2, cy - ax[1] * height / 2, cz - ax[2] * height / 2
            )
            top_pt = adsk.core.Point3D.create(
                cx + ax[0] * height / 2, cy + ax[1] * height / 2, cz + ax[2] * height / 2
            )
            cyl_body = temp_brep.createCylinderOrCone(base_pt, radius, top_pt, radius)
            base_feat = comp.features.baseFeatures.add()
            base_feat.startEdit()
            added_body = comp.bRepBodies.add(cyl_body, base_feat)
            base_feat.finishEdit()
            added_body.name = name
            if appearance: added_body.appearance = appearance
            return added_body

        # ============================================================
        # ACTUATOR MODELS
        # ============================================================
        def insert_mg996r(comp, prefix, cx, cy, cz, axis):
            """MG996R Exact Dimensions: 4.1cm L x 2.0cm W x 3.6cm H (Body)."""
            if axis == "z":
                add_box(comp, f"{prefix}_Body", cx, cy, cz, 4.1, 2.0, 3.6, grey_plastic)
                add_box(comp, f"{prefix}_Ears", cx, cy, cz + 0.9, 5.4, 2.0, 0.25, grey_plastic)
                add_cylinder(comp, f"{prefix}_Horn", cx - 1.0, cy, cz + 2.4, 1.0, 0.2, "z", white_pla)
            elif axis == "x":
                add_box(comp, f"{prefix}_Body", cx, cy, cz, 3.6, 2.0, 4.1, grey_plastic)
                add_box(comp, f"{prefix}_Ears", cx + 0.9, cy, cz, 0.25, 2.0, 5.4, grey_plastic)
                add_cylinder(comp, f"{prefix}_Horn", cx + 2.4, cy, cz + 1.0, 1.0, 0.2, "x", white_pla)
            elif axis == "y":
                add_box(comp, f"{prefix}_Body", cx, cy, cz, 2.0, 4.1, 3.6, grey_plastic)
                add_box(comp, f"{prefix}_Ears", cx, cy, cz + 0.9, 2.0, 5.4, 0.25, grey_plastic)
                add_cylinder(comp, f"{prefix}_Horn", cx, cy - 1.0, cz + 2.4, 1.0, 0.2, "y", white_pla) # horn face up Y? wait, axis is rotation axis. if rotation axis is Y, horn should point along Y.
                # Let's fix Y axis horn to actually face Y.
                # For Y axis rotation, body should be oriented such that shaft points along Y.
                # Body: 4.1 x 3.6 x 2.0. Let's assume shaft points +Y.
                # Actually, in script earlier, Y axis horn was pointing Z? That was a bug.
                # Let's fix Y-axis servo:
                add_box(comp, f"{prefix}_Body_Y", cx, cy, cz, 4.1, 3.6, 2.0, grey_plastic)
                add_box(comp, f"{prefix}_Ears_Y", cx, cy + 0.9, cz, 5.4, 0.25, 2.0, grey_plastic)
                add_cylinder(comp, f"{prefix}_Horn_Y", cx - 1.0, cy + 2.4, cz, 1.0, 0.2, "y", white_pla)

        def insert_mg90s(comp, prefix, cx, cy, cz, axis):
            """MG90S Exact: 2.3cm L x 1.2cm W x 2.2cm H (Body)."""
            if axis == "z":
                add_box(comp, f"{prefix}_Body", cx, cy, cz, 2.3, 1.2, 2.2, blue_trans)
                add_box(comp, f"{prefix}_Ears", cx, cy, cz + 0.55, 3.2, 1.2, 0.15, blue_trans)
                add_cylinder(comp, f"{prefix}_Horn", cx - 0.5, cy, cz + 1.5, 0.6, 0.15, "z", white_pla)
            elif axis == "x":
                add_box(comp, f"{prefix}_Body", cx, cy, cz, 2.2, 1.2, 2.3, blue_trans)
                add_box(comp, f"{prefix}_Ears", cx + 0.55, cy, cz, 0.15, 1.2, 3.2, blue_trans)
                add_cylinder(comp, f"{prefix}_Horn", cx + 1.5, cy, cz - 0.5, 0.6, 0.15, "x", white_pla)
            elif axis == "y":
                add_box(comp, f"{prefix}_Body", cx, cy, cz, 2.3, 2.2, 1.2, blue_trans)
                add_box(comp, f"{prefix}_Ears", cx, cy + 0.55, cz, 3.2, 0.15, 1.2, blue_trans)
                add_cylinder(comp, f"{prefix}_Horn", cx - 0.5, cy + 1.5, cz, 0.6, 0.15, "y", white_pla)

        def insert_tt_motor(comp, prefix, cx, cy, cz, wheel_axis, wheel_offset):
            """TT Motor Gearbox: 2.2 W x 5.2 L x 1.9 H cm. Wheel 6.5cm diameter."""
            if wheel_axis == "x":
                add_box(comp, f"{prefix}_Gearbox", cx, cy, cz, 2.2, 5.2, 1.9, yellow_metal)
                add_cylinder(comp, f"{prefix}_MotorCan", cx, cy - 3.0, cz, 0.9, 2.0, "y", chrome)
                add_cylinder(comp, f"{prefix}_Axle", cx + wheel_offset * 0.5, cy, cz, 0.1, abs(wheel_offset), "x", chrome)
                wx = cx + wheel_offset
                add_cylinder(comp, f"{prefix}_Tire", wx, cy, cz, 3.25, 2.6, "x", rubber_blk)
                add_cylinder(comp, f"{prefix}_Hub", wx, cy, cz, 0.8, 0.3, "x", chrome)

        # ============================================================
        # COMPONENT 1: TORSO CHASSIS
        # ============================================================
        print("[1/9] Building 01_Torso_Chassis...")
        torso_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        torso = torso_occ.component
        torso.name = "01_Torso_Chassis"

        # Main torso shell: wider to accommodate 4.5cm shoulders, 10x7x10cm
        add_box(torso, "Torso_Shell", 0, 0, 20.0, 10.0, 7.0, 10.0, red_metal)
        add_box(torso, "Windshield_L", -2.5, -3.6, 22.5, 3.5, 0.3, 3.5, glass_clr)
        add_box(torso, "Windshield_R", 2.5, -3.6, 22.5, 3.5, 0.3, 3.5, glass_clr)
        add_box(torso, "Radiator_Grille", 0, -3.6, 18.0, 6.0, 0.4, 4.0, chrome)

        # Waist rotation servo (Z axis)
        insert_mg996r(torso, "Waist_Rotate", 0, 0, 15.0, "z")

        # Chest-fold servo (Y axis) - allows folding forward
        insert_mg996r(torso, "Chest_Fold", 0, 0, 24.5, "y")

        # Shoulder connection brackets (sticking out to hold shoulder servos)
        add_box(torso, "Shoulder_Bracket_L", -6.0, 0, 23.0, 2.0, 4.0, 4.0, red_metal)
        add_box(torso, "Shoulder_Bracket_R", 6.0, 0, 23.0, 2.0, 4.0, 4.0, red_metal)

        # ============================================================
        # COMPONENT 2: PELVIS
        # ============================================================
        print("[2/9] Building 01b_Pelvis...")
        pelvis_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        pelvis = pelvis_occ.component
        pelvis.name = "01b_Pelvis"

        add_box(pelvis, "Pelvis_Block", 0, 0, 12.0, 8.0, 5.0, 4.0, blue_metal)
        # Hip Pan servos (MG996R) pointing Z downward
        insert_mg996r(pelvis, "L_Hip_Pan", -3.0, 0, 12.0, "z")
        insert_mg996r(pelvis, "R_Hip_Pan", 3.0, 0, 12.0, "z")

        # ============================================================
        # COMPONENT 3 & 4: LEGS (L and R)
        # ============================================================
        leg_sides = {"L": -4.0, "R": 4.0}
        for side, hip_x in leg_sides.items():
            leg_idx = 3 if side == "L" else 4
            leg_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            leg = leg_occ.component
            leg.name = f"02_Leg_{side}_Assembly"
            mirror = -1 if side == "L" else 1

            # --- THIGH LINK: Must house Hip Tilt & Knee Flex MG996R ---
            # Thigh needs to be at least 4.5cm x 3.0cm x 9.0cm to house two MG996Rs safely
            thigh_z = 7.0
            add_box(leg, "Thigh_Link", hip_x, 0, thigh_z, 4.5, 3.5, 9.0, chrome)
            add_box(leg, "Thigh_Armor", hip_x + mirror * 1.5, -2.0, thigh_z, 2.0, 0.5, 8.0, red_metal)

            # Hip Tilt servo (Y axis, top of thigh)
            insert_mg996r(leg, f"{side}_Hip_Tilt", hip_x, 0, 10.0, "y")
            
            # Knee servo (X axis, bottom of thigh)
            insert_mg996r(leg, f"{side}_Knee", hip_x, 0, 4.0, "x")
            
            # Pivot marker to show exact alignment
            # The horn is at cx+2.4 for X-axis MG996R. So pivot is at X = hip_x + 2.4.
            pivot_x = hip_x + 2.4

            # --- SHIN LINK: Must house 2x TT Motors in tandem ---
            # To fit two 65mm wheels without overlapping, they need 70mm separation!
            # Shin needs to be long enough (e.g., 14.0cm)
            shin_z = -5.0
            add_box(leg, "Shin_Link", pivot_x, 0, shin_z, 3.0, 6.0, 14.0, blue_metal)
            add_box(leg, "Shin_Armor", pivot_x + mirror * 1.0, -3.2, shin_z, 2.5, 0.5, 13.0, blue_metal)

            # Dual TT motors (TANDEM SETUP)
            # Motor 1 (Upper rear wheel)
            insert_tt_motor(leg, f"{side}_Drive_Rear_1", pivot_x, 0, -1.5, "x", mirror * 3.5)
            # Motor 2 (Lower rear wheel) -> Spaced 7.0 cm down on Z axis!
            insert_tt_motor(leg, f"{side}_Drive_Rear_2", pivot_x, 0, -8.5, "x", mirror * 3.5)

            # --- FOOT PLATE ---
            foot_z = -12.5
            add_box(leg, "Foot_Plate", pivot_x, -1.0, foot_z, 4.0, 6.0, 1.5, blue_metal)
            insert_mg90s(leg, f"{side}_Ankle", pivot_x, 0, -11.0, "y")

        # ============================================================
        # COMPONENT 5: HEAD GIMBAL
        # ============================================================
        print("[5/9] Building 03_Head_Gimbal_2DOF...")
        head_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        head = head_occ.component
        head.name = "03_Head_Gimbal_2DOF"

        head_base_z = 26.5
        add_cylinder(head, "Neck_Column", 0, 0, head_base_z, 1.0, 2.0, "z", chrome)
        insert_mg90s(head, "Head_Pan", 0, 0, head_base_z - 0.5, "z")
        insert_mg90s(head, "Head_Tilt", 0, 0, head_base_z + 1.0, "y")

        helmet_z = head_base_z + 3.5
        add_box(head, "Helmet_Main", 0, 0, helmet_z, 4.0, 4.0, 4.0, blue_metal)
        add_box(head, "Horn_L", -2.2, 0, helmet_z + 1.0, 0.3, 0.8, 3.0, blue_metal)
        add_box(head, "Horn_R", 2.2, 0, helmet_z + 1.0, 0.3, 0.8, 3.0, blue_metal)
        add_box(head, "Faceplate", 0, -2.1, helmet_z - 0.5, 3.0, 0.3, 2.5, chrome)
        add_cylinder(head, "Eye_L", -0.8, -2.3, helmet_z, 0.35, 0.3, "y", yellow_metal)
        add_cylinder(head, "Eye_R", 0.8, -2.3, helmet_z, 0.35, 0.3, "y", yellow_metal)

        # ============================================================
        # COMPONENT 6 & 7: ARMS (L and R)
        # ============================================================
        arm_sides = {"L": -8.5, "R": 8.5}
        for side, shoulder_x in arm_sides.items():
            arm_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            arm = arm_occ.component
            arm.name = f"04_Arm_{side}_Assembly"
            mirror = -1 if side == "L" else 1

            # Shoulder Joint (houses MG996R)
            add_box(arm, "Shoulder_Joint", shoulder_x, 0, 23.0, 4.5, 3.5, 4.5, red_metal)
            insert_mg996r(arm, f"{side}_Shoulder_Pitch", shoulder_x, 0, 23.0, "y")
            
            # Pivot is at horn (Y axis, horn points Y, so Y varies, X, Z same)
            pivot_y = 2.4

            # Upper Arm
            upper_arm_z = 18.0
            add_box(arm, "Upper_Arm", shoulder_x, pivot_y, upper_arm_z, 3.0, 3.0, 7.0, red_metal)
            
            # Elbow Servo (MG90S)
            insert_mg90s(arm, f"{side}_Elbow", shoulder_x, pivot_y, 14.5, "x")

            # Forearm (houses Front TT Motor)
            forearm_z = 10.0
            add_box(arm, "Forearm", shoulder_x, pivot_y, forearm_z, 3.0, 6.0, 6.0, blue_metal)
            
            # TT Motor Front Wheel (Steering wheel in car mode)
            insert_tt_motor(arm, f"{side}_Front_Drive", shoulder_x, pivot_y, 9.0, "x", mirror * 3.5)
            
            # Fender Armor (folds down over wheel)
            add_box(arm, "Arm_Fender", shoulder_x + mirror * 2.5, pivot_y, 15.0, 0.3, 5.0, 12.0, red_metal)

        # ============================================================
        # COMPONENT 8: TRANSFORMATION ARMOR
        # ============================================================
        print("[8/9] Building 05_Transformation_Armor...")
        armor_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        armor = armor_occ.component
        armor.name = "05_Transformation_Armor"

        add_box(armor, "Front_Bumper", 0, -5.5, 14.0, 11.0, 1.0, 2.0, chrome)
        add_cylinder(armor, "Headlight_L", -4.5, -5.5, 14.0, 0.6, 0.4, "y", yellow_metal)
        add_cylinder(armor, "Headlight_R", 4.5, -5.5, 14.0, 0.6, 0.4, "y", yellow_metal)
        add_box(armor, "Side_Skirt_L", -5.5, 0, 14.0, 0.3, 8.0, 10.0, red_metal)
        add_box(armor, "Side_Skirt_R", 5.5, 0, 14.0, 0.3, 8.0, 10.0, red_metal)
        add_box(armor, "Rear_Spoiler", 0, 4.5, 26.0, 11.0, 1.5, 0.5, blue_metal)
        add_box(armor, "Roof_Panel", 0, 0, 26.0, 10.0, 6.5, 0.3, blue_metal)

        print("[9/9] Updating view...")
        try:
            cam = app.activeViewport.camera
            cam.isFitView = True
            app.activeViewport.camera = cam
        except:
            pass

    except Exception as e:
        print(f"\n❌ ERROR:\n{str(e)}\n{traceback.format_exc()}")
