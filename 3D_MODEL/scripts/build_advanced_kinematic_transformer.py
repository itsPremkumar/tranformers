"""
KINEMATIC TRANSFORMER ROBOT — ADVANCED Fusion 360 Build Script
---------------------------------------------------------------
Goals:
- cleaner geometry organization
- better proportions
- stronger internal frame concept
- clearer servo / motor / bearing placeholders
- transformation-style panels and wheel pods
- better space planning for real hardware

Important:
This is still a CAD generator, not a finished motion-ready transformer.
Actual joints, motion constraints, fasteners, bearing fits, and electronics
must be refined in Fusion 360 after generation.
"""

def run(context):
    import adsk.core
    import adsk.fusion
    import traceback

    app = None
    ui = None
    doc = None
    design = None
    root = None

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        # ============================================================
        # APPEARANCES
        # ============================================================
        app_lib = None
        for i in range(app.materialLibraries.count):
            lib = app.materialLibraries.item(i)
            if "Fusion" in lib.name and "Appearance" in lib.name:
                app_lib = lib
                break

        def get_appearance(query, fallback=None):
            if not app_lib:
                return fallback
            for i in range(app_lib.appearances.count):
                ap = app_lib.appearances.item(i)
                if query.lower() in ap.name.lower():
                    try:
                        return design.appearances.addByCopy(ap)
                    except:
                        return ap
            return fallback

        red_metal     = get_appearance("Paint - Metallic (Red)")
        blue_metal    = get_appearance("Paint - Metallic (Blue)")
        yellow_metal  = get_appearance("Paint - Metallic (Yellow)")
        chrome        = get_appearance("Chrome") or get_appearance("Steel - Satin")
        rubber_blk    = get_appearance("Rubber") or get_appearance("Plastic - Matte (Black)")
        glass_clr     = get_appearance("Glass - Window")
        grey_plastic  = get_appearance("Plastic - Matte (Grey)")
        dark_grey     = get_appearance("Plastic - Matte (Dark Grey)") or grey_plastic
        white_pla     = get_appearance("Plastic - Glossy (White)")
        black_plastic = get_appearance("Plastic - Matte (Black)")

        # ============================================================
        # HELPERS
        # ============================================================
        def new_component(name):
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = name
            return comp

        def set_appearance(body, appearance):
            if body and appearance:
                try:
                    body.appearance = appearance
                except:
                    pass

        def add_box(comp, name, cx, cy, cz, lx, ly, lz, appearance=None):
            temp = adsk.fusion.TemporaryBRepManager.get()
            obb = adsk.core.OrientedBoundingBox3D.create(
                adsk.core.Point3D.create(cx, cy, cz),
                adsk.core.Vector3D.create(1, 0, 0),
                adsk.core.Vector3D.create(0, 1, 0),
                lx, ly, lz
            )
            shape = temp.createBox(obb)
            bf = comp.features.baseFeatures.add()
            bf.startEdit()
            body = comp.bRepBodies.add(shape, bf)
            bf.finishEdit()
            body.name = name
            set_appearance(body, appearance)
            return body

        def add_cylinder(comp, name, cx, cy, cz, radius, height, axis, appearance=None):
            temp = adsk.fusion.TemporaryBRepManager.get()
            ax = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
            p1 = adsk.core.Point3D.create(
                cx - ax[0] * height / 2,
                cy - ax[1] * height / 2,
                cz - ax[2] * height / 2
            )
            p2 = adsk.core.Point3D.create(
                cx + ax[0] * height / 2,
                cy + ax[1] * height / 2,
                cz + ax[2] * height / 2
            )
            shape = temp.createCylinderOrCone(p1, radius, p2, radius)
            bf = comp.features.baseFeatures.add()
            bf.startEdit()
            body = comp.bRepBodies.add(shape, bf)
            bf.finishEdit()
            body.name = name
            set_appearance(body, appearance)
            return body

        def add_marker(comp, name, cx, cy, cz, size=0.25):
            return add_box(comp, name, cx, cy, cz, size, size, size, white_pla)

        # ============================================================
        # PLACEHOLDER MECHANICAL MODULES
        # ============================================================
        def insert_mg996r(comp, prefix, cx, cy, cz, axis="x"):
            # Approx servo envelope; add extra room for wires and horn
            if axis == "x":
                add_box(comp, f"{prefix}_MG996R_Body", cx, cy, cz, 4.05, 2.00, 4.20, grey_plastic)
                add_box(comp, f"{prefix}_MG996R_Ears", cx + 0.95, cy, cz, 0.30, 2.00, 5.60, grey_plastic)
                add_cylinder(comp, f"{prefix}_MG996R_Horn", cx + 2.35, cy, cz + 1.05, 0.95, 0.22, "x", white_pla)
                add_marker(comp, f"{prefix}_Mount_A", cx - 1.2, cy + 0.9, cz + 1.6)
                add_marker(comp, f"{prefix}_Mount_B", cx - 1.2, cy - 0.9, cz + 1.6)
            elif axis == "z":
                add_box(comp, f"{prefix}_MG996R_Body", cx, cy, cz, 4.05, 2.00, 4.20, grey_plastic)
                add_box(comp, f"{prefix}_MG996R_Ears", cx, cy, cz + 0.95, 5.60, 2.00, 0.30, grey_plastic)
                add_cylinder(comp, f"{prefix}_MG996R_Horn", cx - 1.10, cy, cz + 2.35, 0.95, 0.22, "z", white_pla)
                add_marker(comp, f"{prefix}_Mount_A", cx + 1.2, cy + 0.9, cz + 1.6)
                add_marker(comp, f"{prefix}_Mount_B", cx - 1.2, cy + 0.9, cz + 1.6)
            else:
                add_box(comp, f"{prefix}_MG996R_Body", cx, cy, cz, 4.05, 2.00, 4.20, grey_plastic)
                add_box(comp, f"{prefix}_MG996R_Ears", cx, cy + 0.95, cz, 4.05, 0.30, 5.60, grey_plastic)
                add_cylinder(comp, f"{prefix}_MG996R_Horn", cx, cy + 2.35, cz + 1.05, 0.95, 0.22, "y", white_pla)

        def insert_mg90s(comp, prefix, cx, cy, cz, axis="x"):
            if axis == "x":
                add_box(comp, f"{prefix}_MG90S_Body", cx, cy, cz, 2.30, 1.20, 2.30, blue_metal)
                add_box(comp, f"{prefix}_MG90S_Ears", cx + 0.45, cy, cz, 0.20, 1.20, 3.20, blue_metal)
                add_cylinder(comp, f"{prefix}_MG90S_Horn", cx + 1.40, cy, cz + 0.50, 0.55, 0.18, "x", white_pla)

        def insert_tt_motor(comp, prefix, cx, cy, cz, wheel_offset=3.8):
            add_box(comp, f"{prefix}_TT_Gearbox", cx, cy, cz, 2.30, 5.20, 1.90, yellow_metal)
            add_cylinder(comp, f"{prefix}_TT_MotorCan", cx, cy - 3.00, cz, 0.90, 2.10, "y", chrome)
            add_cylinder(comp, f"{prefix}_Axle", cx + wheel_offset * 0.5, cy, cz, 0.12, abs(wheel_offset), "x", chrome)
            add_cylinder(comp, f"{prefix}_Tire", cx + wheel_offset, cy, cz, 3.15, 2.60, "x", rubber_blk)

        def add_bearing_housing(comp, prefix, cx, cy, cz, axis="x", outer_radius=1.15, width=0.55):
            # Visual placeholder for a real bearing seat / rotary joint
            add_cylinder(comp, f"{prefix}_Bearing_Outer", cx, cy, cz, outer_radius, width, axis, chrome)
            add_cylinder(comp, f"{prefix}_Bearing_Core", cx, cy, cz, outer_radius * 0.55, width * 0.85, axis, dark_grey)

        def add_servo_bracket(comp, prefix, cx, cy, cz, lx, ly, lz, axis="x"):
            add_box(comp, f"{prefix}_Bracket", cx, cy, cz, lx, ly, lz, chrome)
            if axis == "x":
                add_cylinder(comp, f"{prefix}_Bolt_1", cx - lx * 0.25, cy + ly * 0.35, cz, 0.12, lz, "z", dark_grey)
                add_cylinder(comp, f"{prefix}_Bolt_2", cx - lx * 0.25, cy - ly * 0.35, cz, 0.12, lz, "z", dark_grey)

        # ============================================================
        # DIMENSIONS / CLEARANCE TARGETS
        # ============================================================
        torso_z = 20.0
        pelvis_z = 12.5
        head_z = 31.0
        shoulder_z = 25.0
        hip_z = 9.2

        shoulder_x = 12.0
        hip_x = 7.0

        # Extra clearance margin for real printed/mechanical parts
        arm_clearance = 0.8
        leg_clearance = 0.8

        # ============================================================
        # TORSO / MAIN FRAME
        # ============================================================
        torso = new_component("Kinematic_Torso")

        # Outer shell
        add_box(torso, "Torso_Shell", 0, 0, torso_z, 9.8, 8.0, 11.8, red_metal)

        # Inner structural frame
        add_box(torso, "Inner_Frame_Core", 0, 0, torso_z - 0.7, 6.6, 5.2, 10.3, dark_grey)
        add_box(torso, "Spine_Support", 0, 0, torso_z - 1.0, 2.0, 2.0, 9.8, chrome)
        add_cylinder(torso, "Spine_Joint", 0, 0, torso_z - 1.0, 1.25, 4.0, "z", chrome)

        # Front body details
        add_box(torso, "Chest_Plate", 0, -3.9, torso_z + 1.0, 8.8, 0.35, 6.0, chrome)
        add_box(torso, "Windshield", 0, -4.05, torso_z + 1.8, 7.5, 0.25, 3.8, glass_clr)
        add_box(torso, "Radiator", 0, -3.95, torso_z - 2.0, 6.8, 0.35, 4.2, chrome)
        add_box(torso, "Front_Bumper", 0, -4.7, torso_z - 5.7, 13.2, 2.2, 2.4, chrome)

        # Internal bays
        add_box(torso, "Battery_Bay", 0, 0.9, torso_z - 1.0, 5.2, 2.4, 4.2, black_plastic)
        add_box(torso, "Controller_Bay", 0, 2.7, torso_z + 2.0, 4.0, 1.8, 2.2, black_plastic)
        add_box(torso, "Cable_Channel_Left", -3.0, 0.4, torso_z - 0.8, 0.6, 1.2, 8.2, dark_grey)
        add_box(torso, "Cable_Channel_Right", 3.0, 0.4, torso_z - 0.8, 0.6, 1.2, 8.2, dark_grey)

        # Neck / waist mounts
        add_servo_bracket(torso, "Neck_Mount", 0, 0, head_z - 5.0, 2.8, 2.2, 2.8, "x")
        insert_mg996r(torso, "Neck_Pitch", 0, 0, head_z - 5.0, "x")

        add_servo_bracket(torso, "Waist_Mount", 0, 0, pelvis_z + 1.0, 4.2, 3.0, 3.2, "z")
        insert_mg996r(torso, "Waist_Yaw", 0, 0, pelvis_z + 1.0, "z")

        # Shoulder spread / collarbones
        add_servo_bracket(torso, "Collarbone_L", -7.2, 0, shoulder_z - 2.0, 4.8, 3.0, 3.0, "x")
        add_servo_bracket(torso, "Collarbone_R",  7.2, 0, shoulder_z - 2.0, 4.8, 3.0, 3.0, "x")

        # Transformation-style shell flaps
        add_box(torso, "Chest_Left_Flap", -4.4, -0.5, torso_z + 2.2, 0.45, 6.2, 5.6, red_metal)
        add_box(torso, "Chest_Right_Flap", 4.4, -0.5, torso_z + 2.2, 0.45, 6.2, 5.6, red_metal)
        add_box(torso, "Upper_Back_Flap", 0, 4.7, torso_z + 4.7, 7.2, 0.35, 4.7, blue_metal)

        # ============================================================
        # HEAD
        # ============================================================
        head = new_component("Kinematic_Head")
        insert_mg90s(head, "Neck_Tilt", 0, 0, head_z - 1.5, "x")
        add_box(head, "Helmet", 0, 0, head_z + 1.5, 4.9, 4.7, 4.7, blue_metal)
        add_box(head, "Faceplate", 0, -2.2, head_z + 0.4, 2.3, 0.30, 2.5, chrome)
        add_box(head, "Visor", 0, -2.45, head_z + 1.2, 2.9, 0.20, 0.95, glass_clr)
        add_box(head, "Rear_Head_Cap", 0, 1.6, head_z + 1.2, 3.3, 1.6, 3.5, red_metal)
        add_box(head, "Side_Head_Guards", 0, 0.0, head_z + 1.0, 4.8, 4.9, 0.35, dark_grey)

        # ============================================================
        # PELVIS
        # ============================================================
        pelvis = new_component("Kinematic_Pelvis")
        add_box(pelvis, "Pelvis_Block", 0, 0, pelvis_z, 15.8, 5.9, 4.8, blue_metal)
        add_box(pelvis, "Hip_Frame", 0, 0, pelvis_z + 0.2, 11.2, 3.9, 3.2, dark_grey)
        add_box(pelvis, "Hip_Armor_Left", -5.8, 0, pelvis_z + 0.2, 1.0, 4.6, 3.8, chrome)
        add_box(pelvis, "Hip_Armor_Right", 5.8, 0, pelvis_z + 0.2, 1.0, 4.6, 3.8, chrome)

        insert_mg996r(pelvis, "L_Hip_Yaw", -hip_x, 0, hip_z, "z")
        insert_mg996r(pelvis, "R_Hip_Yaw",  hip_x, 0, hip_z, "z")
        add_bearing_housing(pelvis, "Left_Hip_Bearing", -hip_x - 2.1, 0, hip_z + 0.3, "z", 1.10, 0.65)
        add_bearing_housing(pelvis, "Right_Hip_Bearing", hip_x + 2.1, 0, hip_z + 0.3, "z", 1.10, 0.65)

        # ============================================================
        # LEGS
        # ============================================================
        for side, sx in {"L": -hip_x, "R": hip_x}.items():
            mirror = -1 if side == "L" else 1

            thigh = new_component(f"Kinematic_Thigh_{side}")
            add_box(thigh, "Thigh_Link", sx, 0, 4.8, 4.6, 3.8, 9.2, chrome)
            add_box(thigh, "Thigh_Outer_Skin", sx + mirror * 1.9, 0, 4.8, 0.5, 4.0, 9.2, red_metal)
            add_servo_bracket(thigh, f"{side}_Hip_Pitch_Bracket", sx, 0, 9.0, 3.2, 2.6, 3.0, "x")
            insert_mg996r(thigh, f"{side}_Hip_Pitch", sx, 0, 9.0, "x")

            add_servo_bracket(thigh, f"{side}_Knee_Bracket", sx, 0, 0.2, 3.2, 2.6, 3.0, "x")
            insert_mg996r(thigh, f"{side}_Knee", sx, 0, 0.2, "x")

            add_box(thigh, "Thigh_Side_Guard", sx + mirror * 2.25, 0, 4.8, 0.55, 4.1, 9.0, red_metal)

            shin = new_component(f"Kinematic_Shin_{side}")
            shin_x = sx + mirror * 4.4
            add_box(shin, "Shin_Link", shin_x, 0, -4.2, 3.6, 5.5, 15.0, blue_metal)
            add_box(shin, "Shin_Armor", shin_x, -2.0, -4.2, 2.2, 0.35, 11.2, chrome)
            add_box(shin, "Shin_Rear_Support", shin_x, 2.1, -3.6, 1.6, 2.2, 13.0, dark_grey)

            # Wheel modules on shin for vehicle mode concept
            insert_tt_motor(shin, f"{side}_Drive_Front", shin_x, 2.0, -0.7, wheel_offset=3.8)
            insert_tt_motor(shin, f"{side}_Drive_Rear",  shin_x, 2.0, -8.0, wheel_offset=3.8)

            add_bearing_housing(shin, f"{side}_Knee_Bearing", shin_x, 0, 1.0, "x", 1.00, 0.55)

            foot = new_component(f"Kinematic_Foot_{side}")
            insert_mg996r(foot, f"{side}_Ankle_Pitch", shin_x, 0, -12.0, "x")
            add_box(foot, "Foot_Sole", shin_x, -1.1, -14.6, 5.2, 7.6, 1.2, red_metal)
            add_box(foot, "Heel_Block", shin_x - 1.1, 2.2, -13.7, 2.0, 3.0, 2.2, dark_grey)
            add_box(foot, "Toe_Block", shin_x + 1.1, -3.0, -13.7, 2.2, 3.2, 1.8, dark_grey)
            add_box(foot, "Ankle_Guard", shin_x, 0, -11.2, 4.8, 2.4, 2.4, chrome)

        # ============================================================
        # ARMS
        # ============================================================
        for side, ax in {"L": -shoulder_x, "R": shoulder_x}.items():
            mirror = -1 if side == "L" else 1

            upper_arm = new_component(f"Kinematic_UpperArm_{side}")
            add_box(upper_arm, "Shoulder_Block", ax, 0, shoulder_z, 5.0, 3.9, 4.9, red_metal)
            add_box(upper_arm, "Shoulder_Reinforcement", ax + mirror * 1.8, 0, shoulder_z, 1.2, 3.0, 4.7, chrome)
            insert_mg996r(upper_arm, f"{side}_Shoulder_Pitch", ax, 0, shoulder_z, "x")

            add_box(upper_arm, "Upper_Arm_Link", ax, 0, 18.0, 2.9, 3.2, 8.8, red_metal)
            add_box(upper_arm, "Upper_Arm_Outer_Skin", ax, mirror * 1.9, 18.0, 0.55, 3.2, 8.8, chrome)
            add_servo_bracket(upper_arm, f"{side}_Elbow_Bracket", ax, 0, 14.2, 3.2, 2.6, 3.0, "x")
            insert_mg996r(upper_arm, f"{side}_Elbow_Pitch", ax, 0, 14.2, "x")

            add_box(upper_arm, "Shoulder_Panel", ax + mirror * 2.1, 0, shoulder_z - 0.2, 0.45, 4.0, 6.0, blue_metal)

            forearm = new_component(f"Kinematic_Forearm_{side}")
            add_box(forearm, "Forearm_Link", ax, 0, 11.4, 2.9, 3.6, 7.2, blue_metal)
            add_box(forearm, "Forearm_Fender", ax + mirror * 2.0, 0, 11.4, 0.5, 5.0, 8.2, red_metal)
            add_box(forearm, "Forearm_Backplate", ax, 2.1, 11.4, 2.2, 0.35, 6.8, chrome)

            add_bearing_housing(forearm, f"{side}_Wrist_Bearing", ax, 0, 7.2, "x", 0.85, 0.45)
            insert_mg90s(forearm, f"{side}_Wrist_Roll", ax, 0, 7.2, "x")

            hand = new_component(f"Kinematic_Hand_{side}")
            add_box(hand, "Palm_Block", ax, -0.8, 5.0, 2.6, 3.6, 1.6, dark_grey)
            add_box(hand, "Hand_Claw", ax, 0, 5.5, 2.7, 2.7, 2.2, grey_plastic)
            add_box(hand, "Thumb_Block", ax + mirror * 1.4, 0.5, 5.0, 0.8, 1.0, 1.8, chrome)

            # Optional transform-style shell on arms
            add_box(hand, "Hand_Panel", ax + mirror * 0.7, -1.0, 5.0, 0.35, 2.6, 2.4, red_metal)

        # ============================================================
        # BACKPACK / VEHICLE MODE CONCEPT
        # ============================================================
        backpack = new_component("Backpack_Assembly")
        add_box(backpack, "Backpack_Core", 0, 5.0, torso_z + 0.5, 6.2, 2.2, 8.8, dark_grey)
        add_box(backpack, "Backpack_Cover", 0, 5.8, torso_z + 1.0, 5.0, 1.0, 7.4, blue_metal)
        add_box(backpack, "Upper_Back_Flap", 0, 4.8, torso_z + 5.2, 7.2, 0.35, 4.8, red_metal)
        add_box(backpack, "Back_Radiator_Panel", 0, 6.0, torso_z - 0.2, 4.8, 0.4, 5.0, chrome)

        add_cylinder(backpack, "Back_Wheel_L", -3.3, 5.8, torso_z - 1.0, 2.1, 1.0, "x", rubber_blk)
        add_cylinder(backpack, "Back_Wheel_R",  3.3, 5.8, torso_z - 1.0, 2.1, 1.0, "x", rubber_blk)

        # ============================================================
        # EXTRA CLEARANCE PANELS / SHIELD SHAPES
        # ============================================================
        shell_panels = new_component("Shell_Panels")
        add_box(shell_panels, "Left_Shoulder_Shield", -shoulder_x - 2.9, 0, shoulder_z + 1.0, 1.0, 4.2, 4.8, chrome)
        add_box(shell_panels, "Right_Shoulder_Shield", shoulder_x + 2.9, 0, shoulder_z + 1.0, 1.0, 4.2, 4.8, chrome)
        add_box(shell_panels, "Left_Hip_Shield", -hip_x - 2.8, 0, hip_z + 0.5, 1.0, 4.0, 3.5, blue_metal)
        add_box(shell_panels, "Right_Hip_Shield", hip_x + 2.8, 0, hip_z + 0.5, 1.0, 4.0, 3.5, blue_metal)

        # ============================================================
        # VIEW FIT
        # ============================================================
        try:
            cam = app.activeViewport.camera
            cam.isFitView = True
            app.activeViewport.camera = cam
        except:
            pass

    except Exception as e:
        if ui:
            try:
                ui.messageBox("Fusion 360 script error:\n\n{}\n\n{}".format(str(e), traceback.format_exc()))
            except:
                pass
        else:
            print("Fusion 360 script error:\n{}\n{}".format(str(e), traceback.format_exc()))
