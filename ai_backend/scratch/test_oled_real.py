import serial
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_display_test():
    print("==================================================")
    print("🖥️  OMNI-MORPH OLED DISPLAY TESTING UTILITY 🖥️")
    print("==================================================")
    
    port = "COM15"
    baud = 115200
    
    print(f"Connecting to ESP32 on {port}...")
    try:
        ser = serial.Serial(port, baud, timeout=1.0)
    except Exception as e:
        print(f"❌ Failed to open port {port}: {e}")
        return
        
    print("♻️ Performing hardware reset...")
    ser.setDTR(False)
    ser.setRTS(False)
    time.sleep(0.1)
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setRTS(False)
    ser.setDTR(False)
    time.sleep(0.5)
    ser.reset_input_buffer()
    
    print("Waiting for boot to finish (3 seconds)...")
    time.sleep(3.0)
    ser.reset_input_buffer()
    
    test_commands = [
        ("FACE:happy", "😀 HAPPY EXPRESSION"),
        ("FACE:sad", "😢 SAD EXPRESSION"),
        ("FACE:angry", "😡 ANGRY EXPRESSION (with Anger Pop graphic!)"),
        ("FACE:hero", "😎 HERO EXPRESSION"),
        ("FACE:love", "❤️ LOVE EXPRESSION (with Heart graphic!)"),
        ("FACE:peace", "✌️ PEACE EXPRESSION"),
        ("FACE:fear", "😨 FEAR EXPRESSION"),
        ("FACE:disgust", "🤢 DISGUST EXPRESSION"),
        ("FACE:wonder", "😮 WONDER EXPRESSION"),
        ("FACE:debug", "📊 DEBUG HUD DISPLAY"),
        ("FACE:transform", "🤖 TRANSFORMING SCANNER HUD (caution border + rotating scope!)"),
        ("SUB_TEXT:Testing Scrolling Subtitles on the OLED HUD!", "📝 SCROLLING SUBTITLES overlay"),
        ("FACE:happy", "😊 back to HAPPY & IDLE")
    ]
    
    for cmd, desc in test_commands:
        print(f"\nSending command: '{cmd}' -> Showing {desc}")
        ser.write((cmd + "\n").encode('utf-8'))
        time.sleep(3.0)
        
    print("\n==================================================")
    print("🎉 OLED DISPLAY TEST ROUTINE COMPLETE! 🎉")
    print("==================================================")
    ser.close()

if __name__ == "__main__":
    run_display_test()
