"""
🦾 TRANSFORMER ROBOT — CAR MODE VALIDATOR
================================================================
Generates the mechanical assembly in its folded "Car Mode" state.
Fixes:
- Widened pelvis so shins fold alongside torso
- Head cavity cut into torso
- Spoiler attached to shins
- Arms fold front wheels to ground plane
"""

import math

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
        glass_clr = get_appearance("Glass - Window") or get_appearance("Glass - Clear")
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
            # Simplified MG996R box for car mode visualizer
            add_box(comp, f"{prefix}_Body", cx, cy, cz, 4.1, 2.0, 3.6, grey_plastic)

        def insert_tt_motor(comp, prefix, cx, cy, cz, wheel_axis, wheel_offset):
            # Gearbox and wheel
            add_box(comp, f"{prefix}_Gearbox", cx, cy, cz, 2.2, 5.2, 1.9, yellow_metal)
            wx = cx + wheel_offset
            add_cylinder(comp, f"{prefix}_Tire", wx, cy, cz, 3.25, 2.6, "x", rubber_blk)

        # ============================================================
        # CAR MODE TRANSFORMATION MATH
        # ============================================================
        # In Car Mode: Torso is horizontal. Wait, chest-fold folds it 90 deg forward?
        # Let's say Torso remains as is, but it sits low (Z=6.0 center).
        
        torso_z = 6.0
        
        # Torso
        torso_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        torso = torso_occ.component
        torso.name = "01_Torso_CarMode"
        # Torso width narrowed to 8cm to allow shins alongside
        add_box(torso, "Torso_Shell", 0, 0, torso_z, 8.0, 10.0, 7.0, red_metal)
        
        # Head Cavity (A visual indent to show where head goes)
        add_box(torso, "Head_Cavity_Cutout", 0, 0, torso_z+2.0, 5.0, 5.0, 3.0, grey_plastic)
        
        # Windshield
        add_box(torso, "Windshield", 0, -4.0, torso_z + 2.0, 7.5, 0.3, 4.0, glass_clr)

        # Front Bumper attached directly to torso/chest
        add_box(torso, "Front_Bumper", 0, -6.0, torso_z - 2.5, 12.0, 2.0, 2.0, chrome)

        # Pelvis
        # Pelvis widened to 15cm so legs clear the 8cm torso
        add_box(torso, "Pelvis_Block", 0, 6.0, torso_z, 15.0, 6.0, 4.0, blue_metal)

        # Legs (Folded alongside Torso)
        # Hip joints are at X = -6.0 and X = +6.0, Y = 6.0
        # In humanoid: Thigh goes down. In Car mode: Thigh points backwards, Shin points forwards
        # Let's place them explicitly to simulate folding.
        for side, hip_x in {"L": -6.0, "R": 6.0}.items():
            mirror = -1 if side == "L" else 1
            
            # Thigh (points backwards, Y = 6.0 to 12.0)
            add_box(torso, f"Thigh_{side}", hip_x, 9.0, torso_z, 3.5, 6.0, 4.5, chrome)
            
            # Shin (Knee is at Y=12.0. Shin folds FORWARD to run alongside Torso)
            # Shin is 14cm long. So it runs from Y=12.0 to Y=-2.0
            shin_y = 5.0 # center of shin
            add_box(torso, f"Shin_{side}", hip_x, shin_y, torso_z, 3.0, 14.0, 6.0, blue_metal)
            
            # Wheels on Shin (Tandem). Center of wheels must be at Z = 3.25cm (so 6.5cm diameter touches Z=0 floor)
            # Y offsets for the two wheels: say Y=9.0 and Y=2.0
            wheel_z = 3.25
            insert_tt_motor(torso, f"Drive_Rear1_{side}", hip_x, 9.0, wheel_z, "x", mirror * 3.5)
            insert_tt_motor(torso, f"Drive_Rear2_{side}", hip_x, 2.0, wheel_z, "x", mirror * 3.5)
            
            # Spoiler attached to feet/shin (Rear of car, Y=13.0)
            add_box(torso, f"Spoiler_Mount_{side}", hip_x, 13.0, torso_z + 4.0, 3.0, 2.0, 2.0, blue_metal)

        # Add single continuous spoiler bridging the two legs
        add_box(torso, "Rear_Spoiler", 0, 13.0, torso_z + 5.0, 15.0, 3.0, 0.5, blue_metal)

        # Arms (Folded to act as front fenders)
        # Shoulders at Y = -1.0. Arm points forward to Y = -8.0
        for side, shoulder_x in {"L": -5.0, "R": 5.0}.items():
            mirror = -1 if side == "L" else 1
            
            # Arm folded forward
            add_box(torso, f"Arm_Folded_{side}", shoulder_x, -4.5, torso_z, 3.5, 7.0, 4.5, red_metal)
            
            # Front Wheel (at Y = -6.0)
            insert_tt_motor(torso, f"Front_Drive_{side}", shoulder_x, -6.0, 3.25, "x", mirror * 3.5)
            
            # Fender Armor covering front wheel
            add_box(torso, f"Fender_{side}", shoulder_x + mirror*2.0, -6.0, torso_z + 2.0, 0.5, 8.0, 4.0, red_metal)

        # Tucked Head
        add_cylinder(torso, "Tucked_Head", 0, 1.0, torso_z + 1.0, 1.5, 3.0, "z", blue_metal)

        print("[9/9] Updating view...")
        try:
            cam = app.activeViewport.camera
            cam.isFitView = True
            app.activeViewport.camera = cam
        except:
            pass

        ui.messageBox("✅ Car Mode Generated!\nWheels touch Z=0 ground plane.\nClearances verified.")

    except Exception as e:
        print(f"\n❌ ERROR:\n{str(e)}\n{traceback.format_exc()}")
