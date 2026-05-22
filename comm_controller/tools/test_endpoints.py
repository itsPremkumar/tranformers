import sys
import subprocess

try:
    import requests
except ImportError:
    print("Installing requests library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Default IP when connected directly to robot hotspot is 192.168.4.1
# Can also be set to 'omni.local' or another IP assigned by your router
ROBOT_IP = "192.168.4.1"
BASE_URL = f"http://{ROBOT_IP}"

def test_endpoint(endpoint, params=None, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"\n[TESTING] {method} {url}...")
    try:
        if method == "GET":
            r = requests.get(url, params=params, timeout=5)
        else:
            r = requests.post(url, data=data, timeout=5)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.text}")
        return True
    except Exception as e:
        print(f"[FAILED] Could not connect: {e}")
        return False

def show_menu():
    print("\n==============================")
    print("      OMNI-MORPH TEST TOOL    ")
    print("==============================")
    print("1. Get Status Info (/status)")
    print("2. Send Movement: FORWARD (/forward)")
    print("3. Send Movement: STOP (/stop)")
    print("4. Test TTS Speech (/say)")
    print("5. Change Eye Expression (/expression)")
    print("6. Trigger Swarm Scan (/scan)")
    print("7. Exit")
    print("==============================")

def main():
    print(f"Targeting Robot IP: {ROBOT_IP}")
    print("Make sure you are connected to the 'Remote-car' hotspot.")
    
    while True:
        show_menu()
        choice = input("Enter choice (1-7): ").strip()
        
        if choice == '1':
            test_endpoint("/status")
        elif choice == '2':
            test_endpoint("/forward")
        elif choice == '3':
            test_endpoint("/stop")
        elif choice == '4':
            text = input("What should the robot say? ")
            test_endpoint("/say", params={"text": text})
        elif choice == '5':
            print("Expressions: 0=Neutral, 1=Happy, 2=Angry, 3=Sad, 4=Surprised")
            val = input("Enter expression number (0-4): ").strip()
            test_endpoint("/expression", params={"val": val})
        elif choice == '6':
            test_endpoint("/scan")
        elif choice == '7':
            print("Exiting...")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
