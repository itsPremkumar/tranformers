# Autodesk Fusion 360 MCP Automation - Optimus Prime Project

This folder contains the complete, verified Python codebase for parametrically generating the Optimus Prime G1 3D model directly inside Autodesk Fusion 360, along with the **Model Context Protocol (MCP)** tools used to execute scripts remotely.

This folder is structured to be a **standalone project** for Fusion 360 API and MCP integration.

---

## 📁 Project Structure

`	ext
final_3d_ai_model/
├── Release_v5.1/
│   ├── optimus_prime_v5.1_final.py   # The master build script (170+ parts, kinematics)
│   └── Optimus_Live_Animation.py     # Native Fusion 360 animation script
├── mcp_tools/
│   └── run_full.py                   # MCP wrapper to execute the master build script remotely
└── MCP_FUSION_DOCUMENTATION.md       # This file
`

---

## 🔌 What is MCP (Model Context Protocol)?

The Model Context Protocol (MCP) allows external Python scripts (or AI assistants) to execute code *directly* inside a running instance of Autodesk Fusion 360 without manually opening the "Scripts and Add-ins" menu.

It works by running a local background server (usually on 127.0.0.1:27182). We send standard **JSON-RPC** HTTP payloads to this port containing raw Python scripts. The server injects the script into Fusion 360's API environment and returns the result.

### Standard MCP Connection Template
To execute *any* code inside Fusion 360 remotely, we use this boilerplate template (as seen in mcp_tools/run_full.py):

`python
import json
import http.client

# 1. Read your Fusion 360 script
with open("your_fusion_script.py", "r", encoding="utf-8") as f:
    fusion_code = f.read()

# 2. Connect to the local MCP server running on port 27182
conn = http.client.HTTPConnection("127.0.0.1", 27182, timeout=300)
session_id = None
req_id = 0

def send_rpc(method, params=None):
    global session_id, req_id
    req_id += 1
    payload = {"jsonrpc": "2.0", "method": method, "id": req_id}
    if params: payload["params"] = params
    
    headers = {"Content-Type": "application/json"}
    if session_id: headers["Mcp-Session-Id"] = session_id
    
    conn.request("POST", "/mcp", json.dumps(payload), headers)
    resp = conn.getresponse()
    
    for h, v in resp.getheaders():
        if h.lower() == "mcp-session-id": session_id = v
    return json.loads(resp.read().decode("utf-8"))

# 3. Initialize Connection
send_rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "MCP_Runner", "version": "1.0"}})
conn.request("POST", "/mcp", json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}), {"Content-Type": "application/json", "Mcp-Session-Id": session_id})
conn.getresponse().read()

# 4. Execute the Script inside Fusion 360
response = send_rpc("tools/call", {"name": "fusion_mcp_execute", "arguments": {"featureType": "script", "object": {"script": fusion_code}}})
print("Execution Result:", response)
`

---

## 🚀 Execution Workflows

### 1. Building the Model Remotely (MCP)
To build the complete Optimus Prime model from scratch, run the MCP wrapper from your command line:
`ash
python mcp_tools/run_full.py
`
**What happens:** This grabs the massive optimus_prime_v5.1_final.py file, wraps it in the JSON-RPC payload, and forces Fusion 360 to open a new tab and build all 170+ components automatically.

### 2. Live Animation (Native vs. MCP)
**The Problem with MCP Animation:** When you execute a script via the MCP server, it runs inside an HTTP request handler on Fusion 360's main thread. This completely freezes the UI viewport from refreshing until the script finishes. You will not see live walking frames; it will just snap to the final position.

**The Solution (Native Scripting):** 
To view the live walking simulation natively without freezing:
1. Open Fusion 360.
2. Go to **Utilities > Scripts and Add-ins** (Shift + S).
3. Click the + icon and select Release_v5.1/Optimus_Live_Animation.py.
4. Click **Run**.
Because this executes directly on the UI thread without background HTTP blocking, dsk.doEvents() works perfectly and the viewport renders every kinematic frame.

---

## 🛠️ Optimus Prime (Release v5.1) Technical Specs
* **Assembly Type**: Parametric Multi-Body Component Architecture
* **Joints**: 13 Active Revolute/Ball Joints
* **Clearance Tolerance**: 0.2mm standard, physical wheel offsets verified.
* **Auto-Diagnostics**: Built-in script functions calculate mass, Center of Mass, interference collisions, and un-cut pockets at compile-time.
* **Outputs**: Generates a standard obot.urdf physical kinematic map for external physics simulations.
