import os
import re
import shutil
import asyncio
import httpx

# Paths to the motion controller files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOTION_CONTROLLER_DIR = os.path.join(os.path.dirname(BASE_DIR), "motion_controller")
CONFIG_PATH = os.path.join(MOTION_CONTROLLER_DIR, "src", "Config.h")
BUILD_BIN_PATH = os.path.join(MOTION_CONTROLLER_DIR, ".pio", "build", "esp32dev", "firmware.bin")

def modify_firmware_config(key: str, value: str) -> bool:
    """
    Parses Config.h and updates a specific #define key with a new value.
    If the value is meant to be a string, it must be passed in with double quotes (e.g. '"my_ssid"').
    """
    if not os.path.exists(CONFIG_PATH):
        print(f"[Error] Config.h not found at {CONFIG_PATH}")
        return False
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Search pattern for #define KEY VALUE
    pattern = rf"(#define\s+{key}\s+)[^\r\n]+"
    
    # Check if key exists
    if not re.search(pattern, content):
        print(f"[Error] Key '{key}' not found in Config.h")
        return False
    
    # Replace key
    replacement = rf"\g<1>{value}"
    new_content = re.sub(pattern, replacement, content)
    
    with open(CONFIG_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
        
    print(f"[OTA Compiler] Updated Config.h: {key} -> {value}")
    return True

async def compile_firmware() -> tuple[bool, str]:
    """
    Asynchronously invokes PlatformIO Core CLI to compile the firmware.
    Returns (success_boolean, compilation_log).
    """
    print("[OTA Compiler] Launching PlatformIO compiler build...")
    
    # Search for platformio command
    pio_executable = shutil.which("pio") or shutil.which("platformio")
    if not pio_executable:
        # Check standard Windows paths if not in PATH
        possible_paths = [
            os.path.expanduser("~/.platformio/penv/Scripts/pio.exe"),
            os.path.expanduser("~/.platformio/penv/Scripts/platformio.exe")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pio_executable = path
                break
                
    if not pio_executable:
        err_msg = "PlatformIO Core CLI (pio) was not found in PATH or standard user directories. Please install PlatformIO Core."
        print(f"[Error] {err_msg}")
        return False, err_msg
    
    # Run PlatformIO run command in motion_controller directory
    # We force the 'esp32dev' target environment
    cmd = [pio_executable, "run", "-d", MOTION_CONTROLLER_DIR, "-e", "esp32dev"]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        log = stdout.decode("utf-8", errors="ignore") + "\n" + stderr.decode("utf-8", errors="ignore")
        success = (process.returncode == 0)
        
        if success:
            print("[OTA Compiler] Compilation successful!")
        else:
            print(f"[Error] Compilation failed with return code {process.returncode}")
            
        return success, log
        
    except Exception as e:
        err_log = f"Exception running platformio: {str(e)}"
        print(f"[Error] {err_log}")
        return False, err_log

async def deploy_firmware_ota(ip_address: str) -> tuple[bool, str]:
    """
    Pushes the compiled firmware binary to the target ESP32 node via HTTP POST.
    Uses the standard ESP32 WebServer OTA upload endpoint (/update).
    """
    if not os.path.exists(BUILD_BIN_PATH):
        return False, f"Firmware binary not found at build output path: {BUILD_BIN_PATH}"
        
    url = f"http://{ip_address}/update"
    print(f"[OTA Compiler] Initiating OTA upload to {url}...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(BUILD_BIN_PATH, "rb") as bin_file:
                files = {
                    "update": ("firmware.bin", bin_file, "application/octet-stream")
                }
                response = await client.post(url, files=files)
                
            if response.status_code == 200:
                msg = f"OTA deploy successful! Target robot received payload: {response.text}"
                print(f"[OTA Compiler] {msg}")
                return True, msg
            else:
                msg = f"OTA failed. HTTP Status: {response.status_code}, Response: {response.text}"
                print(f"[Error] {msg}")
                return False, msg
                
    except Exception as e:
        msg = f"OTA failed with exception: {str(e)}"
        print(f"[Error] {msg}")
        return False, msg
