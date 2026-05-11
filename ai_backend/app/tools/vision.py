import cv2
from PIL import Image
import os
from app.core.config import settings
from app.tools.reactive_vision import reactive_vision

def capture_frame():
    """Captures a frame, prioritizing the shared frame from reactive_vision tracking."""
    # 1. Try to get the frame from the active tracking system (No conflict)
    if reactive_vision.latest_frame is not None:
        try:
            img_rgb = cv2.cvtColor(reactive_vision.latest_frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(img_rgb)
        except Exception as e:
            print(f"[VIDEO] Error converting shared frame: {e}")

    # 2. If tracking isn't running, try to capture a one-off frame (Fallback)
    try:
        source = settings.LOCAL_CAMERA_INDEX if settings.USE_LOCAL_CAMERA else settings.ESP32_CAM_URL
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        
        # Give it a moment to initialize
        for _ in range(5): 
            cap.read()
            
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            # Save for verification
            try:
                pil_img.save("last_capture.jpg")
                print("[VIDEO] Saved capture to last_capture.jpg")
            except: pass
            return pil_img
    except Exception as e:
        print(f"[VIDEO] One-off capture error: {e}")
        
    return None
