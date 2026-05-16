# ⚡ Omni-Morph Autonomous Charging Blueprint

This document outlines the architecture and implementation plan for a self-charging docking system. For a high-performance transformer robot, the **V-Funnel Mechanical Dock** combined with **ArUco Vision** is the recommended standard.

---

## 1. Mechanical Design Options

### A. The V-Funnel Dock (Recommended)
*   **Design**: A physical docking station with a 45-degree "V" shaped guide wall.
*   **Mechanism**: The funnel guides a rear-mounted DC probe or USB-C tail into a centered port.
*   **Hardware**: 
    *   DC Power Jack (Dock Side)
    *   Spring-loaded DC Plug (Robot Side)
    *   Neodymium magnets to assist the final 5mm "snap."

### B. Wireless Inductive Pad
*   **Design**: A flat charging pad on the floor.
*   **Mechanism**: The robot parks its belly directly over a 15W inductive transmitter.
*   **Hardware**: 
    *   Qi-compatible transmitter (Dock Side)
    *   Inductive receiver coil + 5V/2A regulator (Robot Side)

### C. Solar Explorer (Sun-Seeking)
*   **Design**: Flexible solar panels mounted on the robot's back or limbs.
*   **Mechanism**: The robot uses its camera to find the brightest spot in the room (sunlight patch) and navigates there for trickle charging.
*   **Hardware**: 
    *   6V-12V Flexible Solar Panels.
    *   Schottky blocking diode (to prevent battery drain at night).

## 2. Software Logic (The "Brain")

The charging cycle is managed by a state machine distributed across the AI Backend and the Motion Controller.

### Phase 1: Search & Detect (AI Backend)
1.  **Trigger**: Battery voltage drops below `BATTERY_LOW_THRESHOLD` (e.g., 10.8V).
2.  **Vision**: The `vision_controller` scans for a specific **ArUco Marker** ID (e.g., ID 42) attached to the top of the dock.
3.  **Command**: The AI sends `CMD:NAV_TO_DOCK` with the relative coordinates of the marker.

### Phase 2: The Approach (Motion Controller)
1.  **Coarse Alignment**: Use PID control to center the marker in the camera frame.
2.  **Smoothing**: Slow down speed to `SPEED_SLOW` as the distance decreases.
3.  **The "Push"**: In the final 10cm, the robot ignores side sensors and performs a steady forward/backward push to enter the mechanical funnel.

### Phase 3: Validation (Comm Controller)
1.  **Voltage Check**: The robot monitors its internal battery sensor.
2.  **Confirmation**: If `analogRead(BATTERY_PIN)` shows an increase over 1s, set `STATE_CHARGING = true`.
3.  **Notification**: Send `STATUS: CHARGING_STARTED` to the dashboard.

---

## 3. Safety Failsafes

| Event | Action |
| :--- | :--- |
| **High Resistance** | If motor current (`CURRENT_PIN`) spikes during docking, reverse 5cm and retry alignment. |
| **Marker Lost** | If vision is lost, the robot stops and rotates 360° to find the dock again. |
| **Overheat** | If charging temperature exceeds 45°C (using optional sensor), disconnect the dock relay. |

---

## 4. Hardware Wiring Hint

Connect a **P-Channel MOSFET** or a **Relay** between the charging port and the battery. This allows the robot to "disconnect" itself from the dock electronically once charging is complete, preventing overcharging.

---

*This document is a living blueprint for the Omni-Morph autonomy stack. Last Updated: May 2026.*
