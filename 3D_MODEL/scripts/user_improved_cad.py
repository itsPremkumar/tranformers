"""
KINEMATIC TRANSFORMER ROBOT — Fusion 360 Build Script
------------------------------------------------------
Improved CAD generator focused on:
- better component structure
- cleaner placement and clearances
- consistent servo / motor placeholder geometry
- electronics bay and internal frame placeholders
- less collision-prone proportions

Note:
This is still a Fusion 360 concept-build script, not a fully engineered transforming mechanism.
It is intended to be a stronger starting point for real CAD refinement.
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

        # ------------------------------------------------------------
        # APPEARANCE HELPERS
        # ------------------------------------------------------------
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

        red_metal    = get_appearance("Paint - Metallic (Red)")
        blue_metal   = get_appearance("Paint - Metallic (Blue)")
        yellow_metal = get_appearance("Paint - Metallic (Yellow)")
        chrome       = get_appearance("Chrome") or get_appearance("Steel - Satin")
        rubber_blk   = get_appearance("Rubber") or get_appearance("Plastic - Matte (Black)")
        glass_clr    = get_appearance("Glass - Window")
        grey_plastic = get_appearance("Plastic - Matte (Grey)")
        white_pla    = get_appearance("Plastic - Glossy (White)")
        black_plastic = get_appearance("Plastic - Matte (Black)")
        dark_grey    = get_appearance("Plastic - Matte (Dark Grey)") or grey_plastic

        # ------------------------------------------------------------
        # BASIC UTILITIES
        # ------------------------------------------------------------
        def new_component(name):
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = name
            return comp

        def set_body_appearance(body, appearance):
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
            set_body_appearance(body, appearance)
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
            set_body_appearance(body, appearance)
            return body

        def add_hinge_block(comp, prefix, cx, cy, cz, lx, ly, lz, appearance=None):
            return add_box(comp, f"{prefix}_Hinge_Block", cx, cy, cz, lx, ly, lz, appearance)

        # ------------------------------------------------------------
        # SERVO / MOTOR PLACEHOLDERS
        # ------------------------------------------------------------
        def insert_mg996r(comp, prefix, cx, cy, cz, axis="x"):
            if axis == "x":
                add_box(comp, f"{prefix}_MG996R_Body", cx, cy, cz, 4.05, 2.00, 4.20, grey_plastic)
                add_box(comp, f"{prefix}_MG996R_Ears", cx + 0.90, cy, cz, 0.30, 2.00, 5.50, grey_plastic)
                add_cylinder(comp, f"{prefix}_MG996R_Horn", cx + 2.35, cy, cz + 1.05, 0.95, 0.22, "x", white_pla)
            elif axis == "z":
                add_box(comp, f"{prefix}_MG996R_Body", cx, cy, cz, 4.05, 2.00, 4.20, grey_plastic)
                add_box(comp, f"{prefix}_MG996R_Ears", cx, cy, cz + 0.95, 5.50, 2.00, 0.30, grey_plastic)
                add_cylinder(comp, f"{prefix}_MG996R_Horn", cx - 1.10, cy, cz + 2.35, 0.95, 0.22, "z", white_pla)
            else:
                add_box(comp, f"{prefix}_MG996R_Body", cx, cy, cz, 4.05, 2.00, 4.20, grey_plastic)
                add_box(comp, f"{prefix}_MG996R_Ears", cx, cy + 0.90, cz, 4.05, 0.30, 5.50, grey_plastic)
                add_cylinder(comp, f"{prefix}_MG996R_Horn", cx, cy + 2.35, cz + 1.05, 0.95, 0.22, "y", white_pla)

        def insert_mg90s(comp, prefix, cx, cy, cz, axis="x"):
            if axis == "x":
                add_box(comp, f"{prefix}_MG90S_Body", cx, cy, cz, 2.30, 1.20, 2.30, blue_metal)
                add_box(comp, f"{prefix}_MG90S_Ears", cx + 0.45, cy, cz, 0.20, 1.20, 3.20, blue_metal)
                add_cylinder(comp, f"{prefix}_MG90S_Horn", cx + 1.40, cy, cz + 0.50, 0.55, 0.18, "x", white_pla)
            else:
                add_box(comp, f"{prefix}_MG90S_Body", cx, cy, cz, 2.30, 1.20, 2.30, blue_metal)
                add_box(comp, f"{prefix}_MG90S_Ears", cx, cy, cz + 0.45, 3.20, 1.20, 0.20, blue_metal)
                add_cylinder(comp, f"{prefix}_MG90S_Horn", cx, cy, cz + 1.40, 0.55, 0.18, "z", white_pla)

        def insert_tt_motor(comp, prefix, cx, cy, cz, wheel_offset=3.8):
            add_box(comp, f"{prefix}_TT_Gearbox", cx, cy, cz, 2.30, 5.20, 1.90, yellow_metal)
            add_cylinder(comp, f"{prefix}_TT_MotorCan", cx, cy - 3.00, cz, 0.90, 2.10, "y", chrome)
            add_cylinder(comp, f"{prefix}_Axle", cx + wheel_offset * 0.5, cy, cz, 0.12, abs(wheel_offset), "x", chrome)
            add_cylinder(comp, f"{prefix}_Tire", cx + wheel_offset, cy, cz, 3.15, 2.60, "x", rubber_blk)

        # ------------------------------------------------------------
        # MAIN GEOMETRY PARAMETERS
        # ------------------------------------------------------------
        torso_z = 20.0
        head_z = 30.5
        pelvis_z = 12.5
        shoulder_z = 25.0
        hip_z = 9.0
        shoulder_x = 12.00
        hip_x = 7.00

        # ------------------------------------------------------------
        # TORSO / INTERNAL FRAME
        # ------------------------------------------------------------
        torso = new_component("Kinematic_Torso")
        add_box(torso, "Torso_Shell", 0, 0, torso_z, 9.5, 7.8, 11.5, red_metal)
        add_box(torso, "Inner_Frame_Core", 0, 0, torso_z - 0.7, 6.5, 5.0, 10.0, dark_grey)
        add_box(torso, "Chest_Plate", 0, -3.8, torso_z + 1.0, 8.6, 0.35, 6.0, chrome)
        add_box(torso, "Windshield", 0, -4.05, torso_z + 1.7, 7.4, 0.25, 3.7, glass_clr)
        add_box(torso, "Radiator", 0, -3.95, torso_z - 2.0, 6.7, 0.35, 4.2, chrome)
        add_box(torso, "Front_Bumper", 0, -4.7, torso_z - 5.5, 13.0, 2.2, 2.4, chrome)

        add_hinge_block(torso, "Neck_Mount", 0, 0, head_z - 5.0, 2.8, 2.2, 2.8, chrome)
        insert_mg996r(torso, "Neck_Pitch", 0, 0, head_z - 5.0, "x")

        add_hinge_block(torso, "Waist_Mount", 0, 0, pelvis_z + 1.0, 4.0, 3.0, 3.2, chrome)
        insert_mg996r(torso, "Waist_Yaw", 0, 0, pelvis_z + 1.0, "z")

        add_box(torso, "Battery_Bay", 0, 0.75, torso_z - 1.0, 5.0, 2.2, 4.0, black_plastic)
        add_box(torso, "Controller_Bay", 0, 2.3, torso_z + 2.0, 3.8, 1.6, 2.0, black_plastic)
        add_box(torso, "Wire_Channel_Left", -2.8, 0.2, torso_z - 0.8, 0.6, 1.2, 8.0, dark_grey)
        add_box(torso, "Wire_Channel_Right", 2.8, 0.2, torso_z - 0.8, 0.6, 1.2, 8.0, dark_grey)

        add_hinge_block(torso, "Collarbone_L", -7.1, 0, shoulder_z - 2.0, 4.6, 3.0, 3.0, chrome)
        add_hinge_block(torso, "Collarbone_R",  7.1, 0, shoulder_z - 2.0, 4.6, 3.0, 3.0, chrome)

        # ------------------------------------------------------------
        # HEAD
        # ------------------------------------------------------------
        head = new_component("Kinematic_Head")
        insert_mg90s(head, "Neck_Tilt", 0, 0, head_z - 1.5, "x")
        add_box(head, "Helmet", 0, 0, head_z + 1.5, 4.8, 4.6, 4.6, blue_metal)
        add_box(head, "Faceplate", 0, -2.2, head_z + 0.4, 2.2, 0.30, 2.4, chrome)
        add_box(head, "Visor", 0, -2.45, head_z + 1.2, 2.8, 0.20, 0.9, glass_clr)
        add_box(head, "Rear_Head_Cap", 0, 1.6, head_z + 1.2, 3.2, 1.6, 3.4, red_metal)

        # ------------------------------------------------------------
        # PELVIS
        # ------------------------------------------------------------
        pelvis = new_component("Kinematic_Pelvis")
        add_box(pelvis, "Pelvis_Block", 0, 0, pelvis_z, 15.5, 5.8, 4.8, blue_metal)
        add_box(pelvis, "Hip_Frame", 0, 0, pelvis_z + 0.2, 11.0, 3.8, 3.2, dark_grey)

        insert_mg996r(pelvis, "L_Hip_Yaw", -hip_x, 0, hip_z, "z")
        insert_mg996r(pelvis, "R_Hip_Yaw",  hip_x, 0, hip_z, "z")

        add_hinge_block(pelvis, "Hip_Guard_L", -hip_x - 2.2, 0, hip_z + 0.2, 3.0, 2.5, 2.8, chrome)
        add_hinge_block(pelvis, "Hip_Guard_R",  hip_x + 2.2, 0, hip_z + 0.2, 3.0, 2.5, 2.8, chrome)

        # ------------------------------------------------------------
        # LEGS
        # ------------------------------------------------------------
        for side, sx in {"L": -hip_x, "R": hip_x}.items():
            mirror = -1 if side == "L" else 1

            thigh = new_component(f"Kinematic_Thigh_{side}")
            add_box(thigh, "Thigh_Link", sx, 0, 4.5, 4.4, 3.8, 9.0, chrome)
            insert_mg996r(thigh, f"{side}_Hip_Pitch", sx, 0, 9.0, "x")
            insert_mg996r(thigh, f"{side}_Knee", sx, 0, 0.0, "x")
            add_hinge_block(thigh, "Thigh_Side_Guard", sx + mirror * 2.2, 0, 4.5, 0.55, 4.0, 8.8, red_metal)

            shin = new_component(f"Kinematic_Shin_{side}")
            shin_x = sx + mirror * 4.2
            add_box(shin, "Shin_Link", shin_x, 0, -4.5, 3.4, 5.4, 15.0, blue_metal)
            add_box(shin, "Shin_Armor", shin_x, -2.0, -4.5, 2.2, 0.35, 11.0, chrome)
            insert_tt_motor(shin, f"{side}_Drive_Front", shin_x, 2.0, -1.0, wheel_offset=3.7)
            insert_tt_motor(shin, f"{side}_Drive_Rear",  shin_x, 2.0, -8.0, wheel_offset=3.7)

            foot = new_component(f"Kinematic_Foot_{side}")
            insert_mg996r(foot, f"{side}_Ankle_Pitch", shin_x, 0, -12.0, "x")
            add_box(foot, "Foot_Sole", shin_x, -1.1, -14.6, 5.0, 7.4, 1.2, red_metal)
            add_box(foot, "Heel_Block", shin_x - 1.1, 2.2, -13.7, 2.0, 3.0, 2.2, dark_grey)
            add_box(foot, "Toe_Block",  shin_x + 1.1, -3.0, -13.7, 2.2, 3.2, 1.8, dark_grey)

        # ------------------------------------------------------------
        # ARMS
        # ------------------------------------------------------------
        for side, ax in {"L": -shoulder_x, "R": shoulder_x}.items():
            mirror = -1 if side == "L" else 1

            upper_arm = new_component(f"Kinematic_UpperArm_{side}")
            add_box(upper_arm, "Shoulder_Block", ax, 0, shoulder_z, 4.8, 3.8, 4.8, red_metal)
            insert_mg996r(upper_arm, f"{side}_Shoulder_Pitch", ax, 0, shoulder_z, "x")
            add_box(upper_arm, "Upper_Arm_Link", ax, 0, 18.0, 2.8, 3.2, 8.8, red_metal)
            add_box(upper_arm, "Upper_Arm_Outer_Skin", ax, mirror * 1.9, 18.0, 0.55, 3.2, 8.8, chrome)
            insert_mg996r(upper_arm, f"{side}_Elbow_Pitch", ax, 0, 14.2, "x")
            add_hinge_block(upper_arm, f"{side}_Shoulder_Reinforcement", ax + mirror * 1.8, 0, shoulder_z, 1.2, 3.0, 4.5, chrome)

            forearm = new_component(f"Kinematic_Forearm_{side}")
            add_box(forearm, "Forearm_Link", ax, 0, 11.4, 2.8, 3.6, 7.0, blue_metal)
            add_box(forearm, "Forearm_Fender", ax + mirror * 2.0, 0, 11.4, 0.5, 5.0, 8.2, red_metal)
            add_box(forearm, "Wrist_Block", ax, 0, 7.2, 2.6, 2.8, 2.6, chrome)
            insert_mg90s(forearm, f"{side}_Wrist_Roll", ax, 0, 7.2, "x")

            hand = new_component(f"Kinematic_Hand_{side}")
            add_box(hand, "Hand_Claw", ax, 0, 5.5, 2.6, 2.6, 2.2, grey_plastic)
            add_box(hand, "Palm_Block", ax, -0.8, 5.0, 2.4, 3.6, 1.6, dark_grey)
            add_box(hand, "Thumb_Block", ax + mirror * 1.4, 0.5, 5.0, 0.8, 1.0, 1.8, chrome)

        # ------------------------------------------------------------
        # TRANSFORMATION-STYLE EXTERIOR PANELS / WHEEL MOUNTS
        # ------------------------------------------------------------
        robot_backpack = new_component("Backpack_Assembly")
        add_box(robot_backpack, "Backpack_Core", 0, 5.0, torso_z + 0.5, 6.2, 2.2, 8.8, dark_grey)
        add_box(robot_backpack, "Backpack_Cover", 0, 5.8, torso_z + 1.0, 5.0, 1.0, 7.4, blue_metal)
        add_box(robot_backpack, "Upper_Back_Flap", 0, 4.8, torso_z + 5.2, 7.0, 0.35, 4.6, red_metal)

        add_cylinder(robot_backpack, "Back_Wheel_L", -3.3, 5.8, torso_z - 1.0, 2.1, 1.0, "x", rubber_blk)
        add_cylinder(robot_backpack, "Back_Wheel_R",  3.3, 5.8, torso_z - 1.0, 2.1, 1.0, "x", rubber_blk)

        # ------------------------------------------------------------
        # CAMERA FIT
        # ------------------------------------------------------------
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
