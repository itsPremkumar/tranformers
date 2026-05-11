import cv2
import asyncio
import numpy as np
import mediapipe as mp
import time
from app.core.config import settings
from app.core.manager import manager

class ReactiveVision:
    def __init__(self):
        self.is_tracking = False
        self.tracking_mode = "face" # "face", "ball", "waste", None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Gesture Recognition (MediaPipe)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
        
        # Ball Tracking (HSV ranges for a Red Ball)
        self.ball_lower = np.array([0, 120, 70])
        self.ball_upper = np.array([10, 255, 255])
        
        # SLAM / Optical Flow
        self.prev_gray = None
        self.total_displacement_x = 0
        self.total_displacement_y = 0

        # Target Offsets (Internal for navigation)
        self.target_offset_x = 0.0
        self.target_offset_y = 0.0
        self.target_area = 0.0

        # Gimbal State
        self.current_pan = 90
        self.current_tilt = 90
        self.last_distance = 100 
        self.last_battery = 100.0
        self.last_battery_alert_time = 0
        self.latest_frame = None

    async def start_tracking(self, mode="face"):
        print(f"[VISION] Tracking Mode: {mode}")
        self.tracking_mode = mode
        self.is_tracking = True
        
        source = settings.LOCAL_CAMERA_INDEX if settings.USE_LOCAL_CAMERA else settings.ESP32_CAM_URL
        cap = cv2.VideoCapture(source)
        
        while self.is_tracking:
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.1)
                continue
            
            self.latest_frame = frame 
            frame_h, frame_w = frame.shape[:2]

            if self.tracking_mode == "face":
                await self.process_face_tracking(frame)
            elif self.tracking_mode == "ball":
                await self.process_ball_tracking(frame)
            elif self.tracking_mode == "waste":
                # Waste usually requires LLM identification first
                # For now, we use a generic "blob" tracking if LLM points it out
                await self.process_generic_blob(frame)

            # --- GESTURE RECOGNITION (Always Active for Safety) ---
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = await asyncio.to_thread(self.hands.process, rgb_frame)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    gesture = self.detect_gesture(hand_landmarks)
                    if gesture == "STOP":
                        await manager.send_command("CMD:STOP")
                        self.is_tracking = False

            await asyncio.sleep(0.01)
        cap.release()

    async def process_face_tracking(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) > 0:
            (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
            self.target_offset_x = ((x + w//2) - frame.shape[1]//2) / (frame.shape[1]//2)
            self.target_offset_y = ((y + h//2) - frame.shape[0]//2) / (frame.shape[0]//2)
            self.target_area = (w * h) / (frame.shape[0] * frame.shape[1])
            await self.update_gimbal()

    async def process_ball_tracking(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.ball_lower, self.ball_upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        cnts, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            if radius > 5:
                self.target_offset_x = (x - frame.shape[1]//2) / (frame.shape[1]//2)
                self.target_offset_y = (y - frame.shape[0]//2) / (frame.shape[0]//2)
                self.target_area = (np.pi * radius**2) / (frame.shape[0] * frame.shape[1])
                await self.update_gimbal()

    async def process_generic_blob(self, frame):
        # Generic dark blob tracking for "waste"
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] > 500:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                self.target_offset_x = (cX - frame.shape[1]//2) / (frame.shape[1]//2)
                self.target_offset_y = (cY - frame.shape[0]//2) / (frame.shape[0]//2)
                self.target_area = M["m00"] / (frame.shape[0] * frame.shape[1])
                await self.update_gimbal()

    async def update_gimbal(self):
        """Moves head servos to keep target centered."""
        if abs(self.target_offset_x) > 0.1: self.current_pan -= int(self.target_offset_x * 10)
        if abs(self.target_offset_y) > 0.1: self.current_tilt += int(self.target_offset_y * 10)
        
        self.current_pan = max(0, min(180, self.current_pan))
        self.current_tilt = max(0, min(180, self.current_tilt))

        await manager.send_command(f"PAN:{self.current_pan}")
        await manager.send_command(f"TILT:{self.current_tilt}")

    def detect_gesture(self, landmarks):
        """Simple gesture detection logic based on finger extension."""
        # Get finger tips
        tips = [8, 12, 16, 20] # Index, Middle, Ring, Pinky
        extended = []
        for tip in tips:
            if landmarks.landmark[tip].y < landmarks.landmark[tip - 2].y:
                extended.append(True)
            else:
                extended.append(False)
        
        # 5 fingers up = STOP
        if all(extended): return "STOP"
        # Only Index up = GO
        if extended[0] and not any(extended[1:]): return "GO"
        return "NONE"

    def update_distance(self, distance: float):
        self.last_distance = distance

    def update_battery(self, voltage: float):
        """Converts voltage to percentage and manages verbal alerts with cooldown."""
        percentage = ((voltage - 3.3) / (4.2 - 3.3)) * 100
        self.last_battery = max(0, min(100, percentage))
        
        # 5-minute cooldown (300 seconds) for battery alerts
        current_time = time.time()
        if self.last_battery < 15 and (current_time - self.last_battery_alert_time > 300):
            asyncio.create_task(manager.send_command("SAY:Caution. My energy levels are low. Please connect a charger."))
            self.last_battery_alert_time = current_time

reactive_vision = ReactiveVision()

