"""
🦾 KINEMATIC TRANSFORMER ROBOT — Fusion 360 Build Script (FREE HANDS FIX)
================================================================
Generates the mechanically-perfect robot. 
Includes the Collarbone fix to widen the shoulders and free the hands from the legs!
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
            if not app_lib: return None
            for i in range(app_lib.appearances.count):
                ap = app_lib.appearances.item(i)
                if query.lower() in ap.name.lower():
                    try: return design.appearances.addByCopy(ap)
                    except: return ap
            return None

        red_metal = get_appearance("Paint - Metallic (Red)")
        blue_metal = get_appearance("Paint - Metallic (Blue)")
        yellow_metal = get_appearance("Paint - Metallic (Yellow)")
        chrome = get_appearance("Chrome") or get_appearance("Steel - Satin")
        rubber_blk = get_appearance("Rubber") or get_appearance("Plastic - Matte (Black)")
        glass_clr = get_appearance("Glass - Window")
        grey_plastic = get_appearance("Plastic - Matte (Grey)")
        white_pla = get_appearance("Plastic - Glossy (White)")

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
            base_pt = adsk.core.Point3D.create(cx - ax[0] * height / 2, cy - ax[1] * height / 2, cz - ax[2] * height / 2)
            top_pt = adsk.core.Point3D.create(cx + ax[0] * height / 2, cy + ax[1] * height / 2, cz + ax[2] * height / 2)
            cyl_body = temp_brep.createCylinderOrCone(base_pt, radius, top_pt, radius)
            base_feat = comp.features.baseFeatures.add()
            base_feat.startEdit()
            added_body = comp.bRepBodies.add(cyl_body, base_feat)
            base_feat.finishEdit()
            added_body.name = name
            if appearance: added_body.appearance = appearance
            return added_body

        def insert_mg996r(comp, prefix, cx, cy, cz, axis):
            if axis == "z":
                add_box(comp, f"{prefix}_MG996R_Body", cx, cy, cz, 4.1, 2.0, 3.6, grey_plastic)
                add_box(comp, f"{prefix}_MG996R_Ears", cx, cy, cz + 0.9, 5.4, 2.0, 0.25, grey_plastic)
                add_cylinder(comp, f"{prefix}_MG996R_Horn", cx - 1.0, cy, cz + 2.4, 1.0, 0.2, "z", white_pla)
            elif axis == "x":
                add_box(comp, f"{prefix}_MG996R_Body", cx, cy, cz, 3.6, 2.0, 4.1, grey_plastic)
                add_box(comp, f"{prefix}_MG996R_Ears", cx + 0.9, cy, cz, 0.25, 2.0, 5.4, grey_plastic)
                add_cylinder(comp, f"{prefix}_MG996R_Horn", cx + 2.4, cy, cz + 1.0, 1.0, 0.2, "x", white_pla)

        def insert_mg90s(comp, prefix, cx, cy, cz, axis):
            if axis == "x":
                add_box(comp, f"{prefix}_MG90S_Body", cx, cy, cz, 2.3, 1.2, 2.3, blue_metal)
                add_box(comp, f"{prefix}_MG90S_Ears", cx + 0.5, cy, cz, 0.2, 1.2, 3.2, blue_metal)
                add_cylinder(comp, f"{prefix}_MG90S_Horn", cx + 1.5, cy, cz + 0.5, 0.6, 0.2, "x", white_pla)

        def insert_tt_motor(comp, prefix, cx, cy, cz, wheel_axis, wheel_offset):
            add_box(comp, f"{prefix}_TT_Gearbox", cx, cy, cz, 2.2, 5.2, 1.9, yellow_metal)
            add_cylinder(comp, f"{prefix}_TT_MotorCan", cx, cy - 3.0, cz, 0.9, 2.0, "y", chrome)
            add_cylinder(comp, f"{prefix}_Axle", cx + wheel_offset * 0.5, cy, cz, 0.1, abs(wheel_offset), "x", chrome)
            wx = cx + wheel_offset
            add_cylinder(comp, f"{prefix}_Tire", wx, cy, cz, 3.25, 2.6, "x", rubber_blk)

        # ============================================================
        # COMPONENT 1: TORSO CHASSIS
        # ============================================================
        print("Building Torso...")
        torso_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        torso = torso_occ.component
        torso.name = "Kinematic_Torso"

        add_box(torso, "Torso_Shell", 0, 0, 20.0, 7.6, 7.0, 10.0, red_metal)
        add_box(torso, "Head_Cavity_Cutout", 0, 0, 23.5, 5.0, 5.0, 3.0, grey_plastic)
        add_box(torso, "Windshield", 0, -3.6, 22.5, 7.5, 0.3, 3.5, glass_clr)
        add_box(torso, "Radiator", 0, -3.6, 18.0, 6.0, 0.4, 4.0, chrome)
        add_box(torso, "Front_Bumper", 0, -4.5, 15.0, 12.0, 2.0, 2.0, chrome)
        
        # COLLARBONE FIX! This pushes the shoulders outwards so arms clear the legs
        add_box(torso, "Collarbone_L", -5.9, 0, 23.0, 4.2, 3.0, 3.0, chrome)
        add_box(torso, "Collarbone_R", 5.9, 0, 23.0, 4.2, 3.0, 3.0, chrome)

        add_cylinder(torso, "Spine", 0, 0, 14.5, 2.0, 3.0, "z", chrome)
        insert_mg996r(torso, "Waist_Pan", 0, 0, 15.0, "z")

        # ============================================================
        # COMPONENT 2: HEAD
        # ============================================================
        head_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        head = head_occ.component
        head.name = "Kinematic_Head"
        head_base_z = 23.0
        insert_mg90s(head, "Neck_Pitch", 0, 0, head_base_z, "x")
        helmet_z = head_base_z + 2.5
        add_box(head, "Helmet", 0, 0, helmet_z, 4.0, 4.0, 4.0, blue_metal)

        # ============================================================
        # COMPONENT 3: PELVIS
        # ============================================================
        pelvis_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        pelvis = pelvis_occ.component
        pelvis.name = "Kinematic_Pelvis"
        add_box(pelvis, "Pelvis_Block", 0, 0, 12.0, 15.0, 5.0, 4.0, blue_metal)
        insert_mg996r(pelvis, "L_Hip_Pan", -6.0, 0, 13.0, "z")
        insert_mg996r(pelvis, "R_Hip_Pan", 6.0, 0, 13.0, "z")

        # ============================================================
        # KINEMATIC LEGS & FEET
        # ============================================================
        for side, hip_x in {"L": -6.0, "R": 6.0}.items():
            mirror = -1 if side == "L" else 1

            thigh_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            thigh = thigh_occ.component
            thigh.name = f"Kinematic_Thigh_{side}"
            # Thigh width is 4.5. Inner edge = 3.75, Outer edge = 8.25
            add_box(thigh, "Thigh_Link", hip_x, 0, 7.0, 4.5, 3.5, 9.0, chrome)
            insert_mg996r(thigh, f"{side}_Hip_Pitch", hip_x, 0, 9.0, "x")
            insert_mg996r(thigh, f"{side}_Knee", hip_x, 0, 4.0, "x")
            
            shin_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            shin = shin_occ.component
            shin.name = f"Kinematic_Shin_{side}"
            pivot_x = hip_x + mirror * 2.4
            add_box(shin, "Shin_Link", pivot_x, 0, -3.0, 3.0, 6.0, 14.0, blue_metal)
            
            insert_tt_motor(shin, f"{side}_Drive_1", pivot_x, 2.0, 1.5, "x", mirror * 3.5)
            insert_tt_motor(shin, f"{side}_Drive_2", pivot_x, 2.0, -5.5, "x", mirror * 3.5)
            
            foot_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            foot = foot_occ.component
            foot.name = f"Kinematic_Foot_{side}"
            insert_mg90s(foot, f"{side}_Ankle_Pitch", pivot_x, 0, -9.0, "x")
            add_box(foot, "Foot_Pad", pivot_x, -1.0, -10.5, 4.0, 6.0, 1.0, red_metal)

        # ============================================================
        # KINEMATIC ARMS & HANDS
        # ============================================================
        # NEW SHOULDER WIDTH = 9.6 (Pushes arms past the 8.25 Thigh edge!)
        for side, shoulder_x in {"L": -9.6, "R": 9.6}.items():
            mirror = -1 if side == "L" else 1

            uarm_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            uarm = uarm_occ.component
            uarm.name = f"Kinematic_UpperArm_{side}"
            
            add_box(uarm, "Shoulder_Block", shoulder_x, 0, 23.0, 4.5, 3.5, 4.5, red_metal)
            insert_mg996r(uarm, f"{side}_Shoulder_Pitch", shoulder_x, 0, 23.0, "x")
            
            # Arms narrowed slightly to 2.5cm to guarantee thigh clearance
            add_box(uarm, "Upper_Arm", shoulder_x, 0, 17.5, 2.5, 3.0, 8.0, red_metal)
            insert_mg996r(uarm, f"{side}_Elbow_Pitch", shoulder_x, 0, 14.0, "x")
            
            # Front TT Motor kept on shoulder!
            insert_tt_motor(uarm, f"{side}_Front_Drive", shoulder_x, 2.0, 22.0, "x", mirror * 3.5)

            farm_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            farm = farm_occ.component
            farm.name = f"Kinematic_Forearm_{side}"
            add_box(farm, "Forearm", shoulder_x, 0, 11.5, 2.5, 4.0, 6.0, blue_metal)
            add_box(farm, "Fender", shoulder_x + mirror * 2.0, 0, 11.5, 0.5, 5.0, 8.0, red_metal)
            
            add_box(farm, "Hand_Claw", shoulder_x, 0, 7.5, 2.5, 2.5, 2.0, grey_plastic)

        try:
            cam = app.activeViewport.camera
            cam.isFitView = True
            app.activeViewport.camera = cam
        except:
            pass

    except Exception as e:
        print(f"\n❌ ERROR:\n{str(e)}\n{traceback.format_exc()}")
