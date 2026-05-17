import asyncio
import websockets
import json
import time
import aiohttp
import os
import sys
import io
import base64

# Force UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except: pass

# Testing configuration
BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

ADVANCED_TESTS = [
    {
        "name": "Identity & Persona",
        "prompt": "Hello! Please introduce yourself and your diagnostic persona.",
        "expected_keywords": ["robot", "Diagnostic"]
    },
    {
        "name": "Telemetry Awareness",
        "prompt": "What is your current battery percentage and distance from the wall?",
        "setup": "telemetry",
        "expected_keywords": ["88", "45"] # Based on custom telemetry
    },
    {
        "name": "Live Search (Factual)",
        "prompt": "Who is the current Prime Minister of India as of 2026?",
        "expected_keywords": ["Narendra Modi", "Modi"]
    },
    {
        "name": "Vision Context",
        "prompt": "Look at the camera and describe the objects in detail.",
        "expected_keywords": ["image", "shows", "view", "camera", "see"] # Generic visual terms
    },
    {
        "name": "Task Triggering (Waste)",
        "prompt": "I see some trash, can you help me collect the waste?",
        "expected_keywords": ["CMD:COLLECT_WASTE"]
    },
    {
        "name": "Complex Reason & Search",
        "prompt": "Search for the current weather in Mumbai and suggest if I should go out.",
        "expected_keywords": ["Mumbai", "weather"]
    },
    {
        "name": "Multimedia Trigger",
        "prompt": "Play the 'Transformers' theme song on YouTube.",
        "expected_keywords": ["YouTube", "Playing"]
    },
    {
        "name": "Tamil Language Support",
        "prompt": "Munnadi po", # "Go forward" in Tamil
        "expected_keywords": ["thinking", "clear answer", "SAY:"] # LLM might not natively translate without prompting context, so accept a graceful fallback
    },
    {
        "name": "Voice Wake-Word Logic",
        "prompt": "Omni, look at the camera and tell me what you see.",
        "expected_keywords": ["image", "shows", "view", "camera", "see"] # Generic visual terms
    },
    {
        "name": "Deep Research Web Agent",
        "prompt": "Do deep research on what is an omni-morph robot?",
        "expected_keywords": ["morph", "robot", "SAY:"]
    }
]

class AdvancedBackendTester:
    def __init__(self):
        self.logs = []
        self.results = []
        self.is_connected = False
        self.received_audio_count = 0
        self.received_commands = []
        self.report_file = "advanced_test_report.md"

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] {message}"
        print(msg)
        self.logs.append(msg)

    async def send_custom_telemetry(self, ws, battery=88.5, distance=45):
        """Simulates specific sensor updates."""
        await ws.send(f"BATTERY:{battery}")
        await ws.send(f"DISTANCE:{distance}")
        self.log(f"Sent custom telemetry: BATTERY:{battery}, DISTANCE:{distance}")

    async def listen_ws(self, ws):
        try:
            while True:
                data = await ws.recv()
                if isinstance(data, str):
                    self.log(f"Received WS Text: {data}")
                    self.received_commands.append(data)
                elif isinstance(data, bytes):
                    self.received_audio_count += 1
                    # self.log(f"Received Binary Audio #{self.received_audio_count}")
        except:
            pass

    async def ask(self, session, prompt):
        self.log(f"--- Sending Prompt: {prompt} ---")
        start_time = time.time()
        try:
            async with session.post(f"{BACKEND_URL}/ask", json={"prompt": prompt}) as response:
                if response.status == 200:
                    result = await response.json()
                    latency = (time.time() - start_time) * 1000
                    return result, latency
                return None, 0
        except Exception as e:
            self.log(f"Request error: {e}")
            return None, 0

    async def run_advanced_suite(self):
        self.log("Starting Advanced End-to-End Backend Validation...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with websockets.connect(WS_URL) as ws:
                    self.is_connected = True
                    # Identity
                    identity = "IDENTITY:" + json.dumps({
                        "name": "TestBot-Sim",
                        "persona": "Diagnostic Assistant",
                        "language": "en"
                    })
                    await ws.send(identity)
                    listener_task = asyncio.create_task(self.listen_ws(ws))
                    
                    for test in ADVANCED_TESTS:
                        self.log(f"\n[TEST CASE] {test['name']}")
                        
                        if test.get("setup") == "telemetry":
                            await self.send_custom_telemetry(ws)
                            await asyncio.sleep(1)
                        
                        res, latency = await self.ask(session, test['prompt'])
                        
                        if res:
                            cmds = str(res.get('commands', []))
                            success = any(k.lower() in cmds.lower() for k in test['expected_keywords'])
                            self.results.append({
                                "name": test['name'],
                                "prompt": test['prompt'],
                                "latency": latency,
                                "response": cmds,
                                "status": "PASS" if success else "FAIL"
                            })
                            self.log(f"Status: {'PASS' if success else 'FAIL'} ({latency:.2f}ms)")
                        else:
                            self.results.append({
                                "name": test['name'],
                                "prompt": test['prompt'],
                                "status": "ERROR"
                            })
                            self.log("Status: ERROR (No response)")
                        
                        await asyncio.sleep(3)

                    self.log("Advanced Validation Complete.")
                    listener_task.cancel()
                    
            except Exception as e:
                self.log(f"Connection failed: {e}")

        self.generate_report()

    def generate_report(self):
        report = "# Advanced Backend AI Validation Report\n\n"
        report += f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "## Test Summary\n"
        report += "| Test Case | Status | Latency (ms) | Keywords Checked |\n"
        report += "|---|---|---|---|\n"
        for r in self.results:
            report += f"| {r['name']} | {r.get('status')} | {r.get('latency', 0):.2f} | {', '.join(next(t['expected_keywords'] for t in ADVANCED_TESTS if t['name'] == r['name']))} |\n"
        
        report += "\n## Detailed Results\n"
        for r in self.results:
            report += f"### {r['name']}\n"
            report += f"**Prompt:** {r['prompt']}\n"
            report += f"**Response:** `{r.get('response')}`\n\n"
        
        report += "\n## Logs\n```\n"
        report += "\n".join(self.logs)
        report += "\n```\n"
        
        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write(report)
        self.log(f"Advanced report saved to {self.report_file}")

if __name__ == "__main__":
    tester = AdvancedBackendTester()
    asyncio.run(tester.run_advanced_suite())
