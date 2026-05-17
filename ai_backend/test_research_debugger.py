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

BACKEND_URL = "http://localhost:8005"
WS_URL = "ws://localhost:8005/ws"

# Target exclusively Deep Research and Scraper Grading Tests
RESEARCH_DEBUG_TESTS = [
    {
        "name": "Science Perspective Research",
        "prompt": "Do deep research on why quantum computing is difficult to scale?",
        "expected_keywords": ["quantum", "scale", "qubit", "SAY:"]
    },
    {
        "name": "News Perspective Research",
        "prompt": "Do deep research on latest news about SpaceX Starship launches",
        "expected_keywords": ["SpaceX", "Starship", "launch", "SAY:", "thinking", "clear answer"]
    }
]

class ResearchDebuggerTester:
    def __init__(self):
        self.logs = []
        self.results = []
        self.scr_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'debug_screenshots'))
        self.debug_output_path = os.path.join(self.scr_dir, 'research_debugger_audit.json')
        self.report_file = "research_debugger_report.md"

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] {message}"
        print(msg)
        self.logs.append(msg)

    async def listen_ws(self, ws):
        try:
            while True:
                data = await ws.recv()
                if isinstance(data, str):
                    self.log(f"Received WS Text: {data}")
        except:
            pass

    async def ask(self, session, prompt):
        self.log(f"--- Sending Research Prompt: {prompt} ---")
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

    async def run_debugger_suite(self):
        self.log("==================================================================")
        self.log("🚀 STARTING ADVANCED RESEARCH GRADER & SCRAEP DEBUGGER TEST RUN 🚀")
        self.log("==================================================================")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with websockets.connect(WS_URL) as ws:
                    identity = "IDENTITY:" + json.dumps({
                        "name": "Research-Debugger-Sim",
                        "persona": "Diagnostic Auditor",
                        "language": "en"
                    })
                    await ws.send(identity)
                    listener_task = asyncio.create_task(self.listen_ws(ws))
                    
                    for test in RESEARCH_DEBUG_TESTS:
                        self.log(f"\n[TEST CASE] {test['name']}")
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

                    self.log("\nResearch Grader Run Complete.")
                    
                    # TRIGGER THE ADVANCED DEBUGGER EXTRACTOR
                    self.log("\n[ADVANCED DEBUGGER] Collecting and structuring raw scraped research data...")
                    self.run_advanced_debugger_audit()
                    
                    listener_task.cancel()
                    
            except Exception as e:
                self.log(f"Connection failed: {e}")

        self.generate_report()

    def run_advanced_debugger_audit(self):
        """Advanced Debugger logic to compile all detailed collected scrape text, metadata, grades, and paths into a single audit file."""
        current_run_path = os.path.join(self.scr_dir, 'current_run.json')
        if not os.path.exists(current_run_path):
            self.log(f"[DEBUGGER ERROR] No current_run.json log found at: {current_run_path}")
            return

        try:
            with open(current_run_path, 'r', encoding='utf-8') as f:
                run_data = json.load(f)

            self.log(f"[DEBUGGER] Processing current_run.json content for query: '{run_data.get('query')}'")
            structured_audit = {
                "session_query": run_data.get("query"),
                "session_timestamp": run_data.get("timestamp"),
                "total_pages_visited": len(run_data.get("pages_visited", [])),
                "detailed_scraped_data": []
            }

            for page in run_data.get("pages_visited", []):
                self.log(f"[DEBUGGER ITEM] Structuring detailed data for: {page.get('url')}")
                scr_path = page.get('screenshot')
                scr_exists = os.path.exists(scr_path) if scr_path else False

                structured_audit["detailed_scraped_data"].append({
                    "url": page.get("url"),
                    "perspective": page.get("perspective"),
                    "title": page.get("title"),
                    "browser_grade_status": page.get("status"),
                    "load_time_ms": page.get("load_time_ms"),
                    "scraped_chars_count": page.get("chars_scraped"),
                    "screenshot_saved_path": scr_path,
                    "screenshot_file_exists": scr_exists,
                    "seo_aeo_metadata_harvested": page.get("seo_metadata", {}),
                    "scraped_full_text": page.get("scraped_content", ""),
                    "manually_cross_verify_note": "Ensure to check the corresponding vertical screenshot to verify lazy elements fully loaded."
                })

            with open(self.debug_output_path, 'w', encoding='utf-8') as df:
                json.dump(structured_audit, df, indent=4)

            self.log(f"[DEBUGGER SUCCESS] Compiled detailed raw audit payload for line-by-line verification at: {self.debug_output_path}")

        except Exception as e:
            self.log(f"[DEBUGGER CRITICAL ERROR] Failed compiling structured debugger audit: {e}")

    def generate_report(self):
        report = "# Targeted Deep Research AI Validation Report\n\n"
        report += f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "## Test Summary\n"
        report += "| Test Case | Status | Latency (ms) | Keywords Checked |\n"
        report += "|---|---|---|---|\n"
        for r in self.results:
            report += f"| {r['name']} | {r.get('status')} | {r.get('latency', 0):.2f} | {', '.join(next(t['expected_keywords'] for t in RESEARCH_DEBUG_TESTS if t['name'] == r['name']))} |\n"
        
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
        self.log(f"Research Debug report saved to {self.report_file}")

if __name__ == "__main__":
    tester = ResearchDebuggerTester()
    asyncio.run(tester.run_debugger_suite())
