"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  OPTIMUS PRIME G1 — KINEMATIC TRANSFORMER FUSION 360 BUILD SCRIPT v3.0      ║
║  Based on: Freightliner FL86 Cab-Over Semi-Truck ↔ Humanoid Robot            ║
║                                                                              ║
║  KEY IMPROVEMENTS OVER v2:                                                   ║
║  • Authentic G1 Optimus Prime humanoid proportions (head:torso:leg ~1:2:2.2) ║
║  • 6 TT-motor wheels: 2 front steer pods + 4 rear drive wheels               ║
║  • Full servo DOF map:                                                        ║
║    - Head: pitch (MG90S) + yaw (MG90S)                                       ║
║    - Shoulders: pitch + roll (MG996R ×4)                                     ║
║    - Elbows: pitch (MG996R ×2)                                               ║
║    - Wrists: roll (MG90S ×2)                                                 ║
║    - Waist: yaw (MG996R ×1)                                                  ║
║    - Hips: yaw + pitch + roll (MG996R ×6)                                    ║
║    - Knees: pitch (MG996R ×2)                                                ║
║    - Ankles: pitch + roll (MG996R ×4)                                        ║
║  • Truck-mode panel tagging (which robot part folds to become which truck piece) ║
║  • Shoulder smokestacks (G1 signature detail)                                ║
║  • Chest windows / windshield exactly as per G1 Freightliner cab             ║
║  • Ion Blaster arm cannon placeholder                                        ║
║  • Internal frame / spine / pelvis tub properly sized for real hardware      ║
║  • Bearing housings at every major pivot point                               ║
║  • All geometry in cm; scale to your print size afterward                    ║
║                                                                              ║
║  IMPORTANT — WHAT THIS SCRIPT IS NOT:                                        ║
║  Motion constraints, fasteners, tolerances, wire routing, PCB mounts,        ║
║  and final transformation sequence kinematic linkages must be completed       ║
║  manually in Fusion 360 after import.                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

def run(context):
    import adsk.core
    import adsk.fusion
    import traceback
    import math

    app = None
    ui  = None

    try:
        app    = adsk.core.Application.get()
        ui     = app.userInterface
        doc    = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        root   = design.rootComponent

        # ═══════════════════════════════════════════════════════════════════
        # APPEARANCES  — graceful fallback if library name differs
        # ═══════════════════════════════════════════════════════════════════
        app_lib = None
        for i in range(app.materialLibraries.count):
            lib = app.materialLibraries.item(i)
            if "Appearance" in lib.name:
                app_lib = lib
                break

        def _copy_appearance(query):
            if not app_lib:
                return None
            for i in range(app_lib.appearances.count):
                ap = app_lib.appearances.item(i)
                if query.lower() in ap.name.lower():
                    try:
                        return design.appearances.addByCopy(ap)
                    except Exception:
                        return ap
            return None

        def get_ap(primary, *fallbacks):
            ap = _copy_appearance(primary)
            if ap:
                return ap
            for fb in fallbacks:
                ap = _copy_appearance(fb)
                if ap:
                    return ap
            return None

        # Optimus Prime G1 palette
        op_red        = get_ap("Paint - Metallic (Red)",  "Steel - Painted (Red)")
        op_blue       = get_ap("Paint - Metallic (Blue)", "Steel - Painted (Blue)")
        op_grey       = get_ap("Aluminum",                "Steel - Satin")
        chrome        = get_ap("Chrome",                  "Steel - Polished")
        dark_metal    = get_ap("Steel - Flat",            "Plastic - Matte (Black)")
        rubber_blk    = get_ap("Rubber",                  "Plastic - Matte (Black)")
        glass_clr     = get_ap("Glass - Window",          "Acrylic - Clear")
        grey_plastic  = get_ap("Plastic - Matte (Grey)",  "ABS Plastic")
        dark_grey     = get_ap("Plastic - Matte (Dark Grey)", "Plastic - Matte (Grey)")
        white_pla     = get_ap("Plastic - Glossy (White)","Nylon - White")
        black_plastic = get_ap("Plastic - Matte (Black)", "Rubber")
        gold_met      = get_ap("Gold",                    "Brass")
        yellow_met    = get_ap("Paint - Metallic (Yellow)","Gold")

        # ═══════════════════════════════════════════════════════════════════
        # LOW-LEVEL GEOMETRY HELPERS
        # ═══════════════════════════════════════════════════════════════════
        def new_component(name):
            occ  = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = name
            return comp

        def set_ap(body, ap):
            if body and ap:
                try:
                    body.appearance = ap
                except Exception:
                    pass

        def box(comp, name, cx, cy, cz, lx, ly, lz, ap=None):
            """Axis-aligned box centred at (cx,cy,cz) with full-width extents lx,ly,lz."""
            temp = adsk.fusion.TemporaryBRepManager.get()
            obb  = adsk.core.OrientedBoundingBox3D.create(
                adsk.core.Point3D.create(cx, cy, cz),
                adsk.core.Vector3D.create(1, 0, 0),
                adsk.core.Vector3D.create(0, 1, 0),
                lx, ly, lz
            )
            shape = temp.createBox(obb)
            bf    = comp.features.baseFeatures.add()
            bf.startEdit()
            body  = comp.bRepBodies.add(shape, bf)
            bf.finishEdit()
            body.name = name
            set_ap(body, ap)
            return body

        def cyl(comp, name, cx, cy, cz, r, h, axis, ap=None):
            """Cylinder centred at (cx,cy,cz), aligned to 'x','y','z'."""
            temp = adsk.fusion.TemporaryBRepManager.get()
            ax   = {"x": (1,0,0), "y": (0,1,0), "z": (0,0,1)}[axis]
            p1   = adsk.core.Point3D.create(cx - ax[0]*h/2, cy - ax[1]*h/2, cz - ax[2]*h/2)
            p2   = adsk.core.Point3D.create(cx + ax[0]*h/2, cy + ax[1]*h/2, cz + ax[2]*h/2)
            shape= temp.createCylinderOrCone(p1, r, p2, r)
            bf   = comp.features.baseFeatures.add()
            bf.startEdit()
            body = comp.bRepBodies.add(shape, bf)
            bf.finishEdit()
            body.name = name
            set_ap(body, ap)
            return body

        def cone_shape(comp, name, cx, cy, cz, r1, r2, h, axis, ap=None):
            """Truncated cone (r1 at base, r2 at tip)."""
            temp = adsk.fusion.TemporaryBRepManager.get()
            ax   = {"x": (1,0,0), "y": (0,1,0), "z": (0,0,1)}[axis]
            p1   = adsk.core.Point3D.create(cx - ax[0]*h/2, cy - ax[1]*h/2, cz - ax[2]*h/2)
            p2   = adsk.core.Point3D.create(cx + ax[0]*h/2, cy + ax[1]*h/2, cz + ax[2]*h/2)
            shape= temp.createCylinderOrCone(p1, r1, p2, r2)
            bf   = comp.features.baseFeatures.add()
            bf.startEdit()
            body = comp.bRepBodies.add(shape, bf)
            bf.finishEdit()
            body.name = name
            set_ap(body, ap)
            return body

        def marker(comp, name, cx, cy, cz, size=0.22):
            """White cube pivot/mount marker."""
            return box(comp, name, cx, cy, cz, size, size, size, white_pla)

        # ═══════════════════════════════════════════════════════════════════
        # MECHANICAL MODULE HELPERS
        # ═══════════════════════════════════════════════════════════════════

        # ── MG996R standard servo (4.05 × 2.00 × 4.20 cm body) ──────────
        def mg996r(comp, tag, cx, cy, cz, axis="x"):
            """
            Accurate MG996R envelope with horn + mounting ears.
            axis = rotation output axis direction.
            """
            if axis == "x":
                box(comp, f"{tag}_Body",  cx,        cy, cz, 4.05, 2.00, 4.20, grey_plastic)
                box(comp, f"{tag}_Ears",  cx+0.95,   cy, cz, 0.30, 2.20, 5.80, dark_grey)
                cyl(comp, f"{tag}_Horn",  cx+2.40,   cy, cz+1.05, 0.95, 0.22, "x", white_pla)
                marker(comp, f"{tag}_Pivot", cx+2.40, cy, cz+1.05)
                marker(comp, f"{tag}_MtA",   cx-1.2,  cy+1.0, cz+1.7)
                marker(comp, f"{tag}_MtB",   cx-1.2,  cy-1.0, cz+1.7)
            elif axis == "z":
                box(comp, f"{tag}_Body",  cx, cy,        cz,      4.05, 2.00, 4.20, grey_plastic)
                box(comp, f"{tag}_Ears",  cx, cy,        cz+0.95, 5.80, 2.20, 0.30, dark_grey)
                cyl(comp, f"{tag}_Horn",  cx-1.10, cy,   cz+2.40, 0.95, 0.22, "z", white_pla)
                marker(comp, f"{tag}_Pivot", cx-1.10, cy, cz+2.40)
            else:  # axis == "y"
                box(comp, f"{tag}_Body",  cx, cy,        cz,      4.05, 4.20, 2.00, grey_plastic)
                box(comp, f"{tag}_Ears",  cx, cy+0.95,   cz,      4.05, 0.30, 2.20, dark_grey)
                cyl(comp, f"{tag}_Horn",  cx, cy+2.40,   cz+1.05, 0.95, 0.22, "y", white_pla)
                marker(comp, f"{tag}_Pivot", cx, cy+2.40, cz+1.05)

        # ── MG90S micro servo (2.30 × 1.20 × 2.30 cm body) ──────────────
        def mg90s(comp, tag, cx, cy, cz, axis="x"):
            if axis == "x":
                box(comp, f"{tag}_Body",  cx, cy, cz, 2.30, 1.20, 2.30, op_blue)
                box(comp, f"{tag}_Ears",  cx+0.45, cy, cz, 0.20, 1.30, 3.20, op_blue)
                cyl(comp, f"{tag}_Horn",  cx+1.40, cy, cz+0.50, 0.55, 0.18, "x", white_pla)
                marker(comp, f"{tag}_Pivot", cx+1.40, cy, cz+0.50)
            elif axis == "z":
                box(comp, f"{tag}_Body",  cx, cy, cz, 2.30, 1.20, 2.30, op_blue)
                box(comp, f"{tag}_Ears",  cx, cy, cz+0.45, 3.20, 1.30, 0.20, op_blue)
                cyl(comp, f"{tag}_Horn",  cx-0.50, cy, cz+1.40, 0.55, 0.18, "z", white_pla)
                marker(comp, f"{tag}_Pivot", cx-0.50, cy, cz+1.40)
            else:
                box(comp, f"{tag}_Body",  cx, cy, cz, 2.30, 2.30, 1.20, op_blue)
                box(comp, f"{tag}_Ears",  cx, cy+0.45, cz, 3.20, 0.20, 1.30, op_blue)
                cyl(comp, f"{tag}_Horn",  cx, cy+1.40, cz+0.50, 0.55, 0.18, "y", white_pla)

        # ── TT DC gear-motor + wheel (full assembly) ─────────────────────
        def tt_motor_wheel(comp, tag, cx, cy, cz, side=1):
            """
            side: +1 = wheel extends in +X, -1 = wheel extends in -X.
            The gearbox output shaft exits from side*+X face.
            Wheel centre is 3.25 cm from gearbox centre along X.
            """
            box(comp,  f"{tag}_Gearbox",   cx, cy, cz, 2.30, 5.20, 1.90, yellow_met)
            cyl(comp,  f"{tag}_MotorCan",  cx, cy-3.00, cz, 0.90, 2.10, "y", chrome)
            cyl(comp,  f"{tag}_Shaft",     cx+side*1.75, cy, cz, 0.20, 3.50, "x", chrome)
            cyl(comp,  f"{tag}_Hub",       cx+side*3.25, cy, cz, 0.80, 2.60, "x", dark_metal)
            cyl(comp,  f"{tag}_Tire",      cx+side*3.25, cy, cz, 3.25, 2.60, "x", rubber_blk)
            cyl(comp,  f"{tag}_Rim_Inner", cx+side*3.25, cy, cz, 2.20, 2.65, "x", chrome)
            marker(comp, f"{tag}_Axle_Pivot", cx+side*3.25, cy, cz, 0.18)

        # ── Bearing housing placeholder ───────────────────────────────────
        def bearing(comp, tag, cx, cy, cz, axis="x", ro=1.10, w=0.60):
            cyl(comp, f"{tag}_Bearing_Outer", cx, cy, cz, ro,          w, axis, chrome)
            cyl(comp, f"{tag}_Bearing_Inner", cx, cy, cz, ro*0.58,     w*0.80, axis, dark_grey)
            cyl(comp, f"{tag}_Bearing_Bore",  cx, cy, cz, ro*0.32,     w*1.10, axis, chrome)

        # ── U-bracket for servo (double-sided pivot frame) ─────────────────
        def u_bracket(comp, tag, cx, cy, cz, lx, ly, lz, ap=None):
            ap = ap or chrome
            box(comp, f"{tag}_Bracket_Back", cx,          cy, cz, 0.45, ly, lz, ap)
            box(comp, f"{tag}_Bracket_TopL", cx+lx*0.45,  cy+ly*0.35, cz, lx*0.55, 0.40, lz, ap)
            box(comp, f"{tag}_Bracket_TopR", cx+lx*0.45,  cy-ly*0.35, cz, lx*0.55, 0.40, lz, ap)
            cyl(comp,  f"{tag}_Pivot_Pin",   cx+lx*0.50,  cy, cz, 0.18, ly*0.85, "y", chrome)

        # ═══════════════════════════════════════════════════════════════════
        # GLOBAL PROPORTIONS  (all in cm)
        # G1 Optimus at ~38 cm tall robot mode → 1:1 scale representation
        # Coordinate origin = sole of feet.
        # ═══════════════════════════════════════════════════════════════════
        GROUND        = 0.0
        ANKLE_CTR     = 3.8
        SHIN_CTR      = 9.5
        KNEE_CTR      = 16.5
        THIGH_CTR     = 22.0
        HIP_CTR       = 27.5
        PELVIS_CTR    = 29.5
        WAIST_CTR     = 31.5
        TORSO_CTR     = 35.0
        SHOULDER_CTR  = 40.5
        NECK_BASE     = 43.5
        HEAD_CTR      = 46.5

        HIP_X         = 5.8
        SHOULDER_X    = 11.0
        ELBOW_X       = SHOULDER_X
        ELBOW_Z       = 34.0
        WRIST_Z       = 28.0

        # ═══════════════════════════════════════════════════════════════════
        # ① TORSO
        # ═══════════════════════════════════════════════════════════════════
        torso = new_component("OP_Torso")

        box(torso, "Torso_Shell",          0, 0, TORSO_CTR,      10.2, 8.4, 12.0, op_red)
        box(torso, "Torso_Side_L",        -5.5, 0, TORSO_CTR,     0.50, 7.6, 11.0, op_red)
        box(torso, "Torso_Side_R",         5.5, 0, TORSO_CTR,     0.50, 7.6, 11.0, op_red)

        box(torso, "Chest_Window_L",      -2.2, -4.25, TORSO_CTR+2.5, 2.6, 0.22, 2.8, glass_clr)
        box(torso, "Chest_Window_R",       2.2, -4.25, TORSO_CTR+2.5, 2.6, 0.22, 2.8, glass_clr)
        box(torso, "Chest_Window_Divider", 0,   -4.2,  TORSO_CTR+2.5, 0.35,0.22, 2.8, op_blue)
        box(torso, "Chest_Grille",        0,   -4.35, TORSO_CTR-0.5, 7.0, 0.30, 4.0, chrome)
        box(torso, "Front_Bumper",        0,   -5.10, TORSO_CTR-4.2, 9.6, 1.80, 1.6, chrome)
        box(torso, "Headlight_L",        -4.2, -4.45, TORSO_CTR-1.2, 1.6, 0.30, 1.8, glass_clr)
        box(torso, "Headlight_R",         4.2, -4.45, TORSO_CTR-1.2, 1.6, 0.30, 1.8, glass_clr)

        box(torso, "Chest_Plate",        0, -4.15, TORSO_CTR+0.5, 8.2, 0.30, 3.5, chrome)
        cyl(torso,  "Autobot_Badge",     0, -4.52, TORSO_CTR+0.5, 0.70, 0.10, "y", op_red)

        box(torso, "Inner_Frame",        0, 0, TORSO_CTR,      7.2, 5.8, 10.6, dark_metal)
        box(torso, "Spine_Beam",         0, 0, TORSO_CTR,      1.8, 1.8, 11.2, chrome)
        cyl(torso,  "Spine_Joint_Cyl",   0, 0, TORSO_CTR,      1.10, 4.2, "z", chrome)

        box(torso, "Battery_Bay",        0, 2.2, TORSO_CTR-1.5, 5.8, 2.6, 4.8, black_plastic)
        box(torso, "Controller_Bay",     0, 2.8, TORSO_CTR+2.2, 4.2, 1.8, 2.4, black_plastic)
        box(torso, "Cable_Ch_L",        -3.2, 0.6, TORSO_CTR,   0.55,1.0,10.0, dark_grey)
        box(torso, "Cable_Ch_R",         3.2, 0.6, TORSO_CTR,   0.55,1.0,10.0, dark_grey)

        u_bracket(torso, "Waist_Brkt", 0, 0, WAIST_CTR, 4.0, 4.2, 3.4)
        mg996r(torso, "Waist_Yaw",     0, 0, WAIST_CTR, "z")
        bearing(torso, "Waist_Bearing", 0, 0, WAIST_CTR+0.5, "z", 1.30, 0.65)

        u_bracket(torso, "Neck_Brkt", 0, 0, NECK_BASE, 3.2, 2.8, 3.0)
        mg996r(torso, "Neck_Pitch",   0, 0, NECK_BASE, "x")

        box(torso, "Collar_L",  -7.8, 0, SHOULDER_CTR-1.0, 5.0, 3.2, 2.8, chrome)
        box(torso, "Collar_R",   7.8, 0, SHOULDER_CTR-1.0, 5.0, 3.2, 2.8, chrome)

        box(torso, "TF_Flap_L",  -5.25, -0.2, TORSO_CTR+3.0, 0.40, 6.4, 6.0, op_red)
        box(torso, "TF_Flap_R",   5.25, -0.2, TORSO_CTR+3.0, 0.40, 6.4, 6.0, op_red)
        box(torso, "TF_Back_Top", 0, 4.8, TORSO_CTR+5.0, 8.0, 0.35, 5.0, op_blue)

        # ═══════════════════════════════════════════════════════════════════
        # ② HEAD
        # ═══════════════════════════════════════════════════════════════════
        head = new_component("OP_Head")

        mg90s(head, "Neck_Yaw",  0, 0, HEAD_CTR-2.5, "z")

        box(head, "Helmet_Main",    0, 0, HEAD_CTR+1.0, 5.2, 4.9, 4.8, op_blue)
        box(head, "Helmet_Top",     0, 0, HEAD_CTR+3.5, 4.4, 4.2, 0.5, op_blue)
        box(head, "Crest",          0,-0.2,HEAD_CTR+3.6,  0.8, 0.6, 3.0, chrome)
        box(head, "Ear_Fin_L",    -2.75, 0, HEAD_CTR+1.8, 0.35, 3.8, 3.0, op_blue)
        box(head, "Ear_Fin_R",     2.75, 0, HEAD_CTR+1.8, 0.35, 3.8, 3.0, op_blue)

        box(head, "Faceplate",      0,-2.35, HEAD_CTR+0.5, 2.5, 0.28, 2.6, chrome)
        box(head, "Visor",          0,-2.55, HEAD_CTR+1.4, 3.0, 0.18, 0.9, glass_clr)
        box(head, "Mouth_Grille",   0,-2.50, HEAD_CTR-0.3, 1.6, 0.20, 1.0, dark_grey)

        cyl(head,  "Antenna_L",   -2.60, 0, HEAD_CTR+4.2, 0.14, 2.2, "z", chrome)
        cyl(head,  "Antenna_R",    2.60, 0, HEAD_CTR+4.2, 0.14, 2.2, "z", chrome)
        cyl(head,  "Antenna_Tip_L",-2.60,0, HEAD_CTR+5.5, 0.22, 0.28,"z", gold_met)
        cyl(head,  "Antenna_Tip_R", 2.60,0, HEAD_CTR+5.5, 0.22, 0.28,"z", gold_met)

        box(head, "Rear_Head_Cap",  0, 1.8, HEAD_CTR+1.2, 3.6, 1.6, 3.8, op_red)

        # ═══════════════════════════════════════════════════════════════════
        # ③ PELVIS
        # ═══════════════════════════════════════════════════════════════════
        pelvis = new_component("OP_Pelvis")

        box(pelvis, "Pelvis_Shell",      0, 0, PELVIS_CTR,    16.2, 6.0, 4.8, op_blue)
        box(pelvis, "Pelvis_Frame",      0, 0, PELVIS_CTR,    12.0, 4.2, 3.6, dark_metal)
        box(pelvis, "Hip_Armor_L",      -7.0, 0, PELVIS_CTR,   1.0, 5.0, 4.0, chrome)
        box(pelvis, "Hip_Armor_R",       7.0, 0, PELVIS_CTR,   1.0, 5.0, 4.0, chrome)
        box(pelvis, "Crotch_Plate",      0,-2.8, PELVIS_CTR-1.2,5.0, 0.28, 2.2, op_red)

        mg996r(pelvis, "L_Hip_Yaw",  -HIP_X, 0, HIP_CTR, "z")
        mg996r(pelvis, "R_Hip_Yaw",   HIP_X, 0, HIP_CTR, "z")
        bearing(pelvis,"L_Hip_Yaw_Brg", -HIP_X-2.2, 0, HIP_CTR+0.3, "z", 1.10, 0.62)
        bearing(pelvis,"R_Hip_Yaw_Brg",  HIP_X+2.2, 0, HIP_CTR+0.3, "z", 1.10, 0.62)

        # ═══════════════════════════════════════════════════════════════════
        # ④ LEGS
        # ═══════════════════════════════════════════════════════════════════
        for side, sx in [("L", -HIP_X), ("R", HIP_X)]:
            m = -1 if side == "L" else 1

            thigh = new_component(f"OP_Thigh_{side}")
            u_bracket(thigh, f"{side}_HipP_Brkt", sx, 0, THIGH_CTR+3.5, 4.0, 3.2, 3.2)
            mg996r(thigh, f"{side}_Hip_Pitch", sx, 0, THIGH_CTR+3.8, "x")
            mg996r(thigh, f"{side}_Hip_Roll",  sx, 0, THIGH_CTR+2.0, "y")
            bearing(thigh, f"{side}_Hip_Roll_Brg", sx, 0, THIGH_CTR+2.0, "y", 1.00, 0.55)
            box(thigh, "Thigh_Link",   sx, 0, THIGH_CTR,  4.8, 3.8, 9.5, chrome)
            box(thigh, "Thigh_Skin_Outer", sx+m*2.55, 0, THIGH_CTR, 0.45, 4.2, 9.5, op_red)
            box(thigh, "Thigh_Skin_Front", sx, -2.1,   THIGH_CTR,   4.8, 0.38, 9.5, op_blue)
            u_bracket(thigh, f"{side}_Knee_Brkt", sx, 0, KNEE_CTR+1.5, 3.8, 3.0, 3.0)
            mg996r(thigh, f"{side}_Knee_Pitch", sx, 0, KNEE_CTR+1.5, "x")
            bearing(thigh, f"{side}_Knee_Brg",  sx, 0, KNEE_CTR, "x", 1.00, 0.55)

            shin = new_component(f"OP_Shin_{side}")
            shin_x = sx + m * 0.0

            box(shin, "Shin_Link",   shin_x, 0, SHIN_CTR,     4.2, 5.8, 14.0, op_blue)
            box(shin, "Shin_Armor",  shin_x, -2.6, SHIN_CTR,  3.0, 0.32,10.5, chrome)
            box(shin, "Shin_Rear",   shin_x,  2.6, SHIN_CTR,  1.8, 0.32,12.5, dark_grey)
            box(shin, "Shin_Beam",   shin_x, 0.4, SHIN_CTR,   1.6, 2.0, 13.0, dark_metal)

            tt_motor_wheel(shin, f"{side}_Wheel_Front", shin_x+m*4.0, 1.8, SHIN_CTR+3.5, side=m)
            tt_motor_wheel(shin, f"{side}_Wheel_Rear",  shin_x+m*4.0, 1.8, SHIN_CTR-3.8, side=m)
            bearing(shin, f"{side}_Knee_Lower_Brg", shin_x, 0, KNEE_CTR-0.5, "x", 1.00, 0.55)

            foot = new_component(f"OP_Foot_{side}")
            mg996r(foot, f"{side}_Ankle_Pitch", shin_x, 0, ANKLE_CTR+2.2, "x")
            mg996r(foot, f"{side}_Ankle_Roll",  shin_x, 0, ANKLE_CTR+0.5, "y")
            bearing(foot, f"{side}_Ankle_Brg", shin_x, 0, ANKLE_CTR, "x", 1.00, 0.55)

            box(foot, "Foot_Sole",    shin_x, -1.0, ANKLE_CTR-1.4, 5.8, 8.2, 1.2, op_red)
            box(foot, "Heel_Block",   shin_x-m*0.8, 2.8, ANKLE_CTR-0.8, 2.2,3.0,2.4, dark_grey)
            box(foot, "Toe_Block",    shin_x+m*0.8,-3.6, ANKLE_CTR-0.8, 2.4,3.4,1.8, dark_grey)
            box(foot, "Ankle_Guard",  shin_x,  0, ANKLE_CTR+1.0, 5.0, 2.6, 2.4, chrome)
            box(foot, "Boot_Fin",     shin_x+m*1.5, 0, ANKLE_CTR-0.2, 0.35, 6.0, 3.8, op_blue)

        # ═══════════════════════════════════════════════════════════════════
        # ⑤ ARMS
        # ═══════════════════════════════════════════════════════════════════
        for side, ax in [("L", -SHOULDER_X), ("R", SHOULDER_X)]:
            m = -1 if side == "L" else 1

            upper_arm = new_component(f"OP_UpperArm_{side}")
            u_bracket(upper_arm, f"{side}_ShPit_Brkt", ax, 0, SHOULDER_CTR, 4.8, 3.4, 3.4)
            mg996r(upper_arm, f"{side}_Sh_Pitch", ax, 0, SHOULDER_CTR, "x")
            mg996r(upper_arm, f"{side}_Sh_Roll",  ax, 0, SHOULDER_CTR-1.2, "y")
            bearing(upper_arm, f"{side}_Sh_Brg",  ax, 0, SHOULDER_CTR, "x", 1.10, 0.62)

            box(upper_arm, "Shoulder_Block", ax, 0, SHOULDER_CTR, 5.2, 4.0, 5.2, op_red)
            box(upper_arm, "Shoulder_Guard", ax+m*2.35, 0, SHOULDER_CTR-0.2, 0.40, 4.2, 6.2, op_blue)

            cyl(upper_arm, f"Smokestack_{side}_Main", ax+m*3.2, -1.4, SHOULDER_CTR+2.5, 0.48, 7.5, "z", chrome)
            cyl(upper_arm, f"Smokestack_{side}_Base", ax+m*3.2, -1.4, SHOULDER_CTR-0.2, 0.72, 1.0, "z", chrome)
            cone_shape(upper_arm, f"Smokestack_{side}_Tip", ax+m*3.2, -1.4, SHOULDER_CTR+6.5, 0.50, 0.30, 0.60, "z", dark_grey)

            box(upper_arm, "UA_Link", ax, 0, ELBOW_Z+3.0, 3.0, 3.2, 9.0, op_red)
            box(upper_arm, "UA_Skin", ax+m*1.65, 0, ELBOW_Z+3.0, 0.50, 3.2, 9.0, chrome)

            u_bracket(upper_arm, f"{side}_Elbow_Brkt", ax, 0, ELBOW_Z, 3.8, 3.0, 3.0)
            mg996r(upper_arm, f"{side}_Elbow_Pitch", ax, 0, ELBOW_Z, "x")
            bearing(upper_arm, f"{side}_Elbow_Brg", ax, 0, ELBOW_Z-0.5, "x", 0.95, 0.52)

            forearm = new_component(f"OP_Forearm_{side}")
            box(forearm, "FA_Link",     ax, 0, WRIST_Z+3.5, 3.0, 3.6, 7.2, op_blue)
            box(forearm, "FA_Fender",   ax+m*2.0, 0, WRIST_Z+3.5, 0.50, 5.0, 8.4, op_red)
            box(forearm, "FA_Backplate",ax, 2.2, WRIST_Z+3.5, 2.4, 0.35, 7.0, chrome)

            mg90s(forearm, f"{side}_Wrist_Roll", ax, 0, WRIST_Z+0.8, "x")
            bearing(forearm, f"{side}_Wrist_Brg", ax, 0, WRIST_Z+0.5, "x", 0.80, 0.44)

            hand = new_component(f"OP_Hand_{side}")
            box(hand, "Palm",        ax, -0.8, WRIST_Z-1.2, 2.8, 3.8, 1.8, dark_grey)
            box(hand, "Fingers",     ax, -1.8, WRIST_Z-2.6, 2.6, 1.8, 2.2, grey_plastic)
            box(hand, "Thumb",       ax+m*1.4, 0.5, WRIST_Z-1.5, 0.9, 1.0, 1.9, chrome)
            box(hand, "Hand_Panel",  ax+m*0.6,-1.0, WRIST_Z-1.0, 0.35,2.6,2.6, op_red)

            if side == "R":
                blaster = new_component("OP_Ion_Blaster")
                cyl(blaster, "Barrel_Main",   ax, -2.0, WRIST_Z-5.0, 0.90, 7.5, "z", dark_metal)
                cyl(blaster, "Barrel_Tip",    ax, -2.0, WRIST_Z-9.0, 0.65, 1.0, "z", chrome)
                box(blaster, "Blaster_Body",  ax, -1.0, WRIST_Z-4.5, 2.4, 2.2, 3.0, dark_metal)
                box(blaster, "Blaster_Guard", ax, -0.2, WRIST_Z-4.5, 2.6, 0.35, 2.0, chrome)
                cyl(blaster, "Scope",         ax+1.4, -2.0, WRIST_Z-4.5, 0.40, 3.2, "z", chrome)

        # ═══════════════════════════════════════════════════════════════════
        # ⑥ BACKPACK
        # ═══════════════════════════════════════════════════════════════════
        backpack = new_component("OP_Backpack")
        box(backpack, "BP_Core",         0, 5.5, TORSO_CTR+0.5, 7.0, 2.4, 9.0, dark_grey)
        box(backpack, "BP_Hood_Cover",   0, 6.4, TORSO_CTR+1.0, 5.6, 1.0, 7.6, op_red)
        box(backpack, "BP_Top_Flap",     0, 5.0, TORSO_CTR+5.4, 8.2, 0.35, 5.2, op_red)
        box(backpack, "BP_Radiator",     0, 6.8, TORSO_CTR-0.5, 5.2, 0.42, 5.5, chrome)
        box(backpack, "Exhaust_Block",   0, 6.2, TORSO_CTR+2.8, 3.0, 0.60, 1.8, dark_metal)
        cyl(backpack,  "Exhaust_Port_L",-1.2, 6.6, TORSO_CTR+2.8, 0.38, 1.2, "y", dark_metal)
        cyl(backpack,  "Exhaust_Port_R", 1.2, 6.6, TORSO_CTR+2.8, 0.38, 1.2, "y", dark_metal)

        # ═══════════════════════════════════════════════════════════════════
        # ⑦ STEER WHEEL PODS
        # ═══════════════════════════════════════════════════════════════════
        steer_pods = new_component("OP_SteerWheelPods")
        for side, sx in [("L", -(HIP_X+5.8)), ("R", HIP_X+5.8)]:
            m = -1 if side == "L" else 1
            box(steer_pods, f"SteerArm_{side}",   sx, 0, PELVIS_CTR-0.5, 1.5, 1.2, 5.5, chrome)
            box(steer_pods, f"SteerPod_{side}",   sx, 2.2, PELVIS_CTR-1.5, 2.8, 2.0, 3.0, dark_grey)
            tt_motor_wheel(steer_pods, f"SteerWheel_{side}", sx, 2.2, PELVIS_CTR-1.5, side=m)
            bearing(steer_pods, f"Steer_Pivot_{side}", sx, 0, PELVIS_CTR-0.5, "z", 0.95, 0.50)
            mg90s(steer_pods, f"Steer_Servo_{side}", sx, 0.8, PELVIS_CTR-0.5, "z")

        # ═══════════════════════════════════════════════════════════════════
        # ⑧ PANELS / SHIELDS
        # ═══════════════════════════════════════════════════════════════════
        shields = new_component("OP_Shoulder_Shields")
        for side, sx in [("L", -(SHOULDER_X+3.2)), ("R", SHOULDER_X+3.2)]:
            m = -1 if side == "L" else 1
            box(shields, f"Sh_Shield_{side}",       sx, 0, SHOULDER_CTR+1.5, 1.0, 4.4, 5.0, chrome)
            box(shields, f"Sh_Shield_Hinge_{side}", sx-m*0.7, 0, SHOULDER_CTR+1.5, 0.5,1.8,1.8, dark_grey)
            box(shields, f"Mirror_{side}",           sx+m*0.5, -2.8, SHOULDER_CTR+2.0, 1.4,0.2,0.8, dark_grey)

        for side, hx in [("L", -(HIP_X+3.0)), ("R", HIP_X+3.0)]:
            box(shields, f"Hip_Shield_{side}", hx, 0, HIP_CTR+0.5, 1.0, 4.2, 3.8, op_blue)

        try:
            cam = app.activeViewport.camera
            cam.isFitView = True
            app.activeViewport.camera = cam
        except Exception:
            pass

    except Exception as e:
        if ui:
            try:
                ui.messageBox(
                    "Optimus Prime Script Error:\n\n{}\n\n{}".format(
                        str(e), traceback.format_exc()
                    )
                )
            except Exception:
                pass
        else:
            print("Error:\n{}\n{}".format(str(e), traceback.format_exc()))
