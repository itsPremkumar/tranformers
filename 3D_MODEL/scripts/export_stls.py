"""
🦾 TRANSFORMER ROBOT — STL EXPORTER
================================================================
Run this script in Fusion 360 AFTER running the build script. 
It will automatically export every single body/component as a high-quality STL file
ready for 3D printing!
"""

def run(context):
    import adsk.core
    import adsk.fusion
    import os
    import traceback

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        # Define export directory
        export_dir = r"c:\one\tranformers\3D_MODEL\STLs"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        export_mgr = design.exportManager
        exported_count = 0

        # Function to export a single occurrence
        def export_occurrence(occ):
            nonlocal exported_count
            name = occ.name.replace(":", "_").replace(" ", "_")
            file_path = os.path.join(export_dir, f"{name}.stl")
            
            # Set STL Export Options
            stl_options = export_mgr.createSTLExportOptions(occ)
            stl_options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            stl_options.filename = file_path
            
            try:
                export_mgr.execute(stl_options)
                exported_count += 1
                print(f"Exported: {name}.stl")
            except:
                print(f"Skipped empty component: {name}")

        # Iterate through all top-level occurrences and export them
        for i in range(root.occurrences.count):
            occ = root.occurrences.item(i)
            # Only export the physical robot parts (ignore servo/motor blocks if they are separate, 
            # but currently they are bodies inside the occurrences, so they will be exported as one solid piece!)
            export_occurrence(occ)

        ui.messageBox(f"✅ Successfully exported {exported_count} STL files to:\n{export_dir}\n\nReady for your 3D Printer Slicer!")

    except Exception as e:
        print(f"\n❌ ERROR:\n{str(e)}\n{traceback.format_exc()}")
