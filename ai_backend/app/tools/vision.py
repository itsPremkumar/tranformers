import cv2
from PIL import Image
import os
from app.core.config import settings
from app.tools.reactive_vision import reactive_vision

def capture_frame():
    """Captures a frame from the ESP32-CAM MJPEG stream. Prefers existing stream if active."""
    # If reactive vision is already tracking, use its latest frame to save bandwidth/resources
    if reactive_vision.is_tracking and reactive_vision.latest_frame is not None:
        try:
            img_rgb = cv2.cvtColor(reactive_vision.latest_frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(img_rgb)
        except:
            pass

    try:
        cap = cv2.VideoCapture(settings.ESP32_CAM_URL)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(img_rgb)
    except:
        return None
