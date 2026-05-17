import os
import sys
import time
import platform
import subprocess
import logging
from typing import str

logger = logging.getLogger(__name__)

class OSAutomationTools:
    @staticmethod
    def start_application(app_name: str) -> str:
        """
        Start a desktop application based on the host operating system.
        
        Args:
            app_name: The lowercase name of the application (e.g. chrome, vscode, notepad).
        """
        app_name = app_name.strip().lower()
        system = platform.system()
        logger.info(f"[OS AUTOMATION] Request to start application: '{app_name}' on {system}")

        # Map common application command lines across platforms
        app_commands = {
            "windows": {
                "chrome": "start chrome",
                "firefox": "start firefox",
                "vscode": "start code",
                "code": "start code",
                "spotify": "start spotify",
                "discord": "start discord",
                "terminal": "start cmd",
                "cmd": "start cmd",
                "calc": "start calc",
                "calculator": "start calc",
                "notes": "start notepad",
                "notepad": "start notepad",
                "explorer": "start explorer",
            },
            "darwin": { # macOS
                "chrome": "open -a 'Google Chrome'",
                "firefox": "open -a 'Firefox'",
                "vscode": "open -a 'Visual Studio Code'",
                "code": "open -a 'Visual Studio Code'",
                "spotify": "open -a 'Spotify'",
                "discord": "open -a 'Discord'",
                "terminal": "open -a 'Terminal'",
                "calc": "open -a 'Calculator'",
                "calculator": "open -a 'Calculator'",
                "notes": "open -a 'Notes'",
                "notepad": "open -a 'Notes'",
            },
            "linux": {
                "chrome": "google-chrome",
                "firefox": "firefox",
                "vscode": "code",
                "code": "code",
                "spotify": "spotify",
                "terminal": "x-terminal-emulator",
                "calc": "gnome-calculator",
                "calculator": "gnome-calculator",
            }
        }

        sys_key = system.lower()
        if sys_key not in ["windows", "darwin", "linux"]:
            return f"Unsupported operating system: {system}"

        commands = app_commands.get(sys_key, {})
        
        if app_name in commands:
            cmd = commands[app_name]
            try:
                if sys_key == "windows":
                    # Use shell=True for 'start' commands on Windows
                    subprocess.Popen(cmd, shell=True)
                else:
                    # Split string command for POSIX
                    subprocess.Popen(cmd, shell=True)
                return f"Successfully launched {app_name} on {system}."
            except Exception as e:
                logger.error(f"[OS AUTOMATION] Error launching mapped app: {e}")
                return f"Failed to launch mapped application '{app_name}': {e}"
        else:
            # Fallback to system default or attempt to execute direct command
            try:
                if sys_key == "windows":
                    subprocess.Popen(f"start {app_name}", shell=True)
                elif sys_key == "darwin":
                    subprocess.Popen(f"open -a '{app_name}'", shell=True)
                else:
                    subprocess.Popen(app_name, shell=True)
                return f"Attempted to start program '{app_name}' using system defaults."
            except Exception as e:
                logger.error(f"[OS AUTOMATION] General fallback command failed: {e}")
                return f"Failed to start program '{app_name}' using fallbacks: {e}"

    @staticmethod
    def type_text(text: str) -> str:
        """
        Simulate human typing to write text into the currently focused window/application.
        
        Args:
            text: String content to type.
        """
        if not text:
            return "No text content provided to type."
            
        logger.info(f"[OS AUTOMATION] Simulating keyboard typing for {len(text)} characters.")
        
        try:
            import pyautogui
        except ImportError:
            logger.warning("[OS AUTOMATION] pyautogui library is missing. Attempting auto-installation...")
            return "Simulated typing tools require the pyautogui dependency. Please say 'install pyautogui' or let me install it!"

        try:
            # Short safety delay to let the targeted window gain focus
            time.sleep(1.5)
            
            # Type text with micro-delays between keystrokes to feel natural and secure
            pyautogui.write(text, interval=0.01)
            return f"Successfully simulated typing {len(text)} characters into the focused application."
        except Exception as e:
            logger.error(f"[OS AUTOMATION] Error during pyautogui write: {e}")
            return f"Failed to simulate keyboard typing: {e}"
