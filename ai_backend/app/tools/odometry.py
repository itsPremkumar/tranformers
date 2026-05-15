import cv2
import numpy as np
import time

class VisualOdometry:
    def __init__(self, px_to_cm=0.08):
        self.prev_gray = None
        self.prev_pts = None
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.yaw = 0.0
        self.px_to_cm = px_to_cm # Calibration constant
        self.is_active = True
        
        # Parameters for Lucas-Kanade optical flow
        self.lk_params = dict(winSize=(21, 21),
                             maxLevel=3,
                             criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

        # Parameters for corner detection
        self.feature_params = dict(maxCorners=100,
                                 qualityLevel=0.3,
                                 minDistance=7,
                                 blockSize=7)

    def process_frame(self, frame):
        if not self.is_active or frame is None:
            return

        # 1. Pre-process: Resize for speed and convert to grayscale
        frame_small = cv2.resize(frame, (320, 240))
        gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        
        # Focus on the lower part of the frame where the floor is
        h, w = gray.shape
        mask = np.zeros_like(gray)
        mask[int(h*0.6):, :] = 255 

        if self.prev_gray is None:
            self.prev_gray = gray
            self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=mask, **self.feature_params)
            return

        if self.prev_pts is None or len(self.prev_pts) < 10:
            self.prev_pts = cv2.goodFeaturesToTrack(self.prev_gray, mask=mask, **self.feature_params)
            if self.prev_pts is None:
                return

        # 2. Calculate Optical Flow
        next_pts, status, err = cv2.calcOpticalFlowPyrLK(self.prev_gray, gray, self.prev_pts, None, **self.lk_params)

        if next_pts is not None:
            # Select good points
            good_new = next_pts[status == 1]
            good_old = self.prev_pts[status == 1]

            if len(good_new) > 5:
                # 3. Calculate Average Displacement
                dxs = good_new[:, 0] - good_old[:, 0]
                dys = good_new[:, 1] - good_old[:, 1]
                
                # Filter outliers using median
                mdx = np.median(dxs)
                mdy = np.median(dys)

                # 4. Map to World Coordinates (Simplified)
                # In camera view (top-down-ish):
                # -mdy corresponds to forward movement (Y)
                # mdx corresponds to lateral movement (X)
                self.pos_y -= mdy * self.px_to_cm
                self.pos_x += mdx * self.px_to_cm

                # 5. Update for next iteration
                self.prev_pts = good_new.reshape(-1, 1, 2)
            else:
                self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=mask, **self.feature_params)
        
        self.prev_gray = gray

        # Periodic feature refreshment to avoid drift/loss
        if int(time.time() * 10) % 50 == 0:
             self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=mask, **self.feature_params)

    def get_position(self):
        return {
            "x": round(self.pos_x, 1),
            "y": round(self.pos_y, 1),
            "dist": round(np.sqrt(self.pos_x**2 + self.pos_y**2), 1)
        }

    def reset(self):
        self.pos_x = 0.0
        self.pos_y = 0.0
        print("[ODO] Odometry Reset to Home.")

# Global instance
visual_odometry = VisualOdometry()
