# AI Agent Interaction Guide (AGENTS.md)

Welcome, AI Agent. This guide helps you understand how to navigate, modify, and optimize the **Omni-Morph Robot** codebase.

## Repository Layout for Agents
- `ai_backend/`: Python source code. Entry point is `app/main.py`.
- `motion_controller/`: ESP32 firmware for servos/motors. Core logic in `src/main.cpp`.
- `comm_controller/`: Networking and UI firmware.
- `docs/`: Comprehensive markdown documentation. Start with `docs/docs.md`.

## Coding Standards
- **Firmware**: Use non-blocking code. Prefer `FreeRTOS` tasks for long-running operations.
- **Backend**: Use asynchronous Python (`asyncio`/`FastAPI`).
- **Variable Naming**: Use `camelCase` for C++ and `snake_case` for Python.

## How to Propose Changes
1.  **Safety First**: Any changes to `motion_controller/` must be validated against `SERVO_MOTOR_SPECIFICATIONS.md`.
2.  **Modularization**: Keep the controllers decoupled. Communication between them should happen via defined protocols (Serial/WebSockets).
3.  **Documentation**: When adding features, update the corresponding file in `docs/`.

## Contextual Priorities
- If optimizing for **SEO/GEO**, focus on `readme.md` and `llms.txt`.
- If optimizing for **Performance**, focus on S-Curve logic in `motion_controller/`.
- If optimizing for **Intelligence**, focus on `ai_backend/` LLM prompts.
