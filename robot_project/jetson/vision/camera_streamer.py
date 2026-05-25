#!/usr/bin/env python3
import cv2

class JetsonCameraStreamer:
    def __init__(self, width=640, height=480, framerate=30, flip_method=0):
        self.width = width
        self.height = height
        self.framerate = framerate
        self.flip_method = flip_method
        self.cap = None

    def get_gstreamer_pipeline(self):
        # Native GStreamer pipeline with NVMM (Nvidia Memory) GPU-acceleration
        return (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            f"width=(int){self.width}, height=(int){self.height}, "
            f"format=(string)NV12, framerate=(fraction){self.framerate}/1 ! "
            f"nvvidconv flip-method={self.flip_method} ! "
            "video/x-raw, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
        )

    def start(self):
        pipeline = self.get_gstreamer_pipeline()
        print(f"[CAM] Launching GStreamer pipeline: \n{pipeline}")
        self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        return self.cap.isOpened()

    def get_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def stop(self):
        if self.cap:
            self.cap.release()

if __name__ == "__main__":
    streamer = JetsonCameraStreamer()
    if streamer.start():
        print("[CAM] Success: Camera pipeline active.")
        frame = streamer.get_frame()
        if frame is not None:
            print(f"[CAM] Capture resolution: {frame.shape}")
        streamer.stop()
    else:
        print("[CAM] Failure: Could not bind GStreamer pipeline (run on non-Jetson hardware?).")
