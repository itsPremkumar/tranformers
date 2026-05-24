import asyncio
import websockets
import json
import time
import aiohttp
import os
import sys
import io

# Force UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except: pass

# Testing configuration
BACKEND_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"

TEST_QUESTIONS = [
    "Who is the current Chief Minister of Tamil Nadu as of May 11, 2026?",
    "Which political party does the current CM of Tamil Nadu belong to?"
]

class BackendTester:
    def __init__(self):
        self.logs = []
        self.latency_metrics = []
        self.is_connected = False
        self.received_audio_count = 0
        self.received_commands = []
        self.report_file = "test_report.md"

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] {message}"
        print(msg)
        self.logs.append(msg)

    async def send_telemetry(self, ws):
        """Simulates periodic ESP32 sensor updates."""
        try:
            while self.is_connected:
                # Simulate distance, battery, current
                await ws.send("DISTANCE:45")
                await ws.send("BATTERY:12.4")
                await ws.send("CURRENT:0.8")
                # self.log("Sent telemetry: DISTANCE:45, BATTERY:12.4, CURRENT:0.8")
                await asyncio.sleep(5)
        except Exception as e:
            self.log(f"Telemetry error: {e}")

    async def listen_ws(self, ws):
        """Monitors incoming signals from the backend."""
        try:
            while True:
                data = await ws.recv()
                if isinstance(data, str):
                    self.log(f"Received WS Text: {data}")
                    self.received_commands.append(data)
                elif isinstance(data, bytes):
                    self.received_audio_count += 1
                    self.log(f"Received WS Binary Audio: {len(data)} bytes (Chunk #{self.received_audio_count})")
        except websockets.exceptions.ConnectionClosed:
            self.log("WebSocket connection closed.")
        except Exception as e:
            self.log(f"WS Listener error: {e}")

    async def ask_question(self, session, prompt):
        """Simulates voice input via text prompt to the /ask endpoint."""
        self.log(f"--- Sending Prompt: {prompt} ---")
        start_time = time.time()
        try:
            async with session.post(f"{BACKEND_URL}/ask", json={"prompt": prompt}) as response:
                if response.status == 200:
                    result = await response.json()
                    latency = (time.time() - start_time) * 1000
                    self.latency_metrics.append({"prompt": prompt, "latency_ms": latency})
                    self.log(f"AI Response received in {latency:.2f}ms")
                    self.log(f"Commands: {result.get('commands')}")
                    return result
                else:
                    self.log(f"Error: HTTP {response.status}")
                    return None
        except Exception as e:
            self.log(f"Request error: {e}")
            return None

    async def run_tests(self):
        self.log("Starting End-to-End Backend Test...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with websockets.connect(WS_URL) as ws:
                    self.is_connected = True
                    self.log("WebSocket connected to backend.")
                    
                    # 1. Send Identity
                    identity = "IDENTITY:" + json.dumps({
                        "name": "TestBot-Sim",
                        "persona": "Diagnostic Assistant",
                        "version": "1.0.0",
                        "language": "en"
                    })
                    await ws.send(identity)
                    self.log("Sent IDENTITY packet.")

                    # Start background tasks
                    telemetry_task = asyncio.create_task(self.send_telemetry(ws))
                    listener_task = asyncio.create_task(self.listen_ws(ws))

                    # 2. Sequential Testing of Real-world prompts
                    for q in TEST_QUESTIONS:
                        await self.ask_question(session, q)
                        await asyncio.sleep(3) # Wait for processing and audio streams

                    # 3. Wait a bit for any lagging audio chunks
                    self.log("Waiting for final responses...")
                    await asyncio.sleep(5)

                    self.is_connected = False
                    telemetry_task.cancel()
                    listener_task.cancel()
                    
            except Exception as e:
                self.log(f"Failed to connect to backend: {e}")

        self.generate_report()

    def generate_report(self):
        self.log("Generating Test Report...")
        report = "# Backend Test Report\n\n"
        report += f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "## Performance Metrics\n"
        report += "| Prompt | Latency (ms) |\n|---|---|\n"
        for m in self.latency_metrics:
            report += f"| {m['prompt']} | {m['latency_ms']:.2f} |\n"
        
        report += f"\n## Hardware Simulation Summary\n"
        report += f"- **Audio Packets Received:** {self.received_audio_count}\n"
        report += f"- **Commands Received:** {len(self.received_commands)}\n"
        
        report += "\n## Detailed Logs\n```\n"
        report += "\n".join(self.logs)
        report += "\n```\n"
        
        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write(report)
        self.log(f"Report saved to {self.report_file}")

if __name__ == "__main__":
    tester = BackendTester()
    asyncio.run(tester.run_tests())
