# Autodesk Fusion 360 MCP Automation - Optimus Prime Project

**Reference Repository for MCP Setup:** [ai-autodesk-fusion-mcp](https://github.com/itsPremkumar/ai-autodesk-fusion-mcp)
*All MCP connection logic in this project is built referencing the official architecture guidelines from this repository.*

This folder contains the complete, verified Python codebase for parametrically generating the Optimus Prime G1 3D model directly inside Autodesk Fusion 360, along with the **Model Context Protocol (MCP)** tools used to execute scripts remotely.

---

## 📁 Project Structure

`	ext
final_3d_ai_model/
├── Release_v7.0/ (THE ULTIMATE VERSION)
│   ├── optimus_prime_v7.0_builder.py   # Master build script (Geometry + Kinematics)
│   └── Optimus_v7.0_Animator.py        # Live Animation + Auto-Collision Diagnostics
├── Release_v6.0_user_code.py           # Legacy All-in-One code
├── mcp_tools/
│   ├── run_v6_py.py                    # Robust Python MCP runner (Bypasses Memory Crash)
│   └── run_v7.py                       # Python MCP runner for v7
└── MCP_FUSION_DOCUMENTATION.md         # This file
`

---

## 🚀 Execution Rules (CRITICAL)

Before executing any script natively or via MCP, you **MUST** ensure you are inside a valid 3D Design workspace. 

⚠️ **Do not run scripts while sitting on the Fusion 360 "Home" dashboard tab.** 
If you execute an MCP script from the Home tab, the Python API crashes silently in the background because pp.activeProduct evaluates to None (there is no canvas to draw on).
✅ **Solution:** Always click New... to open an empty 3D grid before triggering an MCP run.

---

## 🧠 Why We Use Python for the MCP Connection (The Memory Crash)

When sending massive 1000+ line Python scripts (like Release_v6.0_user_code.py which is ~84 KB) over the local MCP connection (http://127.0.0.1:27182/mcp), you cannot use standard PowerShell commands like Invoke-RestMethod combined with ConvertTo-Json. 

**The Problem:** PowerShell's JSON converter runs out of memory (System.OutOfMemoryException) when attempting to parse and escape an 84-kilobyte script block into a valid JSON-RPC packet, causing the background process to silently die before it even sends the code to Fusion.

**The Solution:** We explicitly utilize a native Python script (mcp_tools/run_v6_py.py) utilizing the urllib and json libraries. Python handles massive string encodings instantly and securely negotiates the Mcp-Session-Id headers.

---

## ⚙️ How to Run via MCP (Remote Execution)

To build the complete Optimus Prime model and run simulations remotely from your terminal:

`ash
# Example: Triggering the v6 script using your local Python installation
"C:\Users\PREM KUMAR\AppData\Local\Programs\Python\Python312\python.exe" C:\one\tranformers\final_3d_ai_model\mcp_tools\run_v6_py.py
`

*This will immediately send the massive script via 	ools/call over the network into Fusion 360, where you will see it natively generate the model and run the simulation loops.*

---

## 🌟 The Ultimate v7.0 Architecture

While 6.0 places both the geometry builder and the animation loop into one file (forcing a 2-minute rebuild just to see it walk), the **v7.0** folder separates them cleanly.

1. **Build the Geometry:** Run Release_v7.0/optimus_prime_v7.0_builder.py once.
2. **Run the Animations:** Run Release_v7.0/Optimus_v7.0_Animator.py whenever you want. This instantly runs the walking simulation and the truck transformation, followed by an automatic execution of the check_interferences() diagnostic tool.

