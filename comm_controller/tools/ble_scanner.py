import asyncio
import sys
import subprocess

try:
    from bleak import BleakScanner
except ImportError:
    print("Installing bleak...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "bleak"])
    from bleak import BleakScanner

async def run_scan():
    print("--- Starting 5-second BLE UUID Scan ---")
    TARGET_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b".lower()
    
    # Scan and return both device information and advertisement packets
    devices_dict = await BleakScanner.discover(timeout=5.0, return_adv=True)
    
    found_target = False
    print(f"Found {len(devices_dict)} BLE devices nearby:")
    for address, (device, adv_data) in devices_dict.items():
        name = device.name if device.name else "Unknown Device"
        uuids = [u.lower() for u in adv_data.service_uuids]
        
        print(f"  * [{address}] {name}")
        if uuids:
            print(f"    Services: {uuids}")
            
        # Match by name or Service UUID
        if "Omni-Core-BT" in name or "Omni" in name or TARGET_UUID in uuids:
            found_target = True
            print(f"    [MATCH] Found target device: {name} (Address: {address})!")

    print("\n--- Scan Results ---")
    if found_target:
        print("[SUCCESS] Bluetooth BLE verification complete: 'Omni-Core-BT' is broadcasting and active!")
    else:
        print("[WARNING] 'Omni-Core-BT' was not detected in the scan.")

if __name__ == "__main__":
    asyncio.run(run_scan())
