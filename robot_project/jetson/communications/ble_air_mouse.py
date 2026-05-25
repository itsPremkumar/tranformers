#!/usr/bin/env python3
import time

class BleAirMouseController:
    def __init__(self):
        self.device = None
        self.init_uinput()

    def init_uinput(self):
        """Initializes a virtual Linux input device using uinput kernel interface."""
        try:
            import uinput
            # Expose a virtual mouse with relative X, Y movement and click buttons
            self.device = uinput.Device([
                uinput.REL_X,
                uinput.REL_Y,
                uinput.BTN_LEFT,
                uinput.BTN_RIGHT
            ])
            print("[AIR-MOUSE] Virtual input device registered in Linux kernel.")
        except ImportError:
            print("[AIR-MOUSE] python-uinput module missing. Running in mock console mode.")
        except Exception as e:
            print(f"[AIR-MOUSE] Could not open /dev/uinput: {e}. (Verify sudo permissions).")

    def move_cursor(self, dx: int, dy: int):
        """Move the mouse cursor relatively by dx, dy steps."""
        if self.device:
            self.device.emit(uinput.REL_X, dx)
            self.device.emit(uinput.REL_Y, dy)
        else:
            print(f"[AIR-MOUSE MOCK] Cursor movement: dx={dx}, dy={dy}")

    def click(self, right=False):
        """Execute a virtual mouse click."""
        if self.device:
            import uinput
            btn = uinput.BTN_RIGHT if right else uinput.BTN_LEFT
            self.device.emit(btn, 1) # Press button
            self.device.emit(btn, 0) # Release button
            print(f"[AIR-MOUSE] Virtual click executed: {'Right' if right else 'Left'}")
        else:
            print(f"[AIR-MOUSE MOCK] Click executed: {'Right' if right else 'Left'}")

if __name__ == "__main__":
    mouse = BleAirMouseController()
    for _ in range(5):
        mouse.move_cursor(10, -5)
        time.sleep(0.2)
    mouse.click()
