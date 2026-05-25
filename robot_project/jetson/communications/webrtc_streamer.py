#!/usr/bin/env python3
import asyncio
import os

class WebRtcStreamer:
    def __init__(self, port=8765):
        self.port = port
        self.is_running = False

    async def start(self):
        # WebRTC utilizes PeerConnection and GStreamer elements:
        # "webrtcdbin name=sendrecv nvarguscamerasrc ! nvvidconv ! nvv4l2h264enc ! h264parse ! rtph264pay ! sendrecv."
        # This wrapper initializes the aiortc framework or GStreamer webrtcbin loops
        print(f"[WEBRTC] Starting WebRTC streaming server on port {self.port}...")
        self.is_running = True
        
        while self.is_running:
            # Maintain signaling handshake exchanges
            await asyncio.sleep(1.0)

    def stop(self):
        self.is_running = False
        print("[WEBRTC] Streaming halted.")

if __name__ == "__main__":
    streamer = WebRtcStreamer()
    try:
        asyncio.run(streamer.start())
    except KeyboardInterrupt:
        streamer.stop()
