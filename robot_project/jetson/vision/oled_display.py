#!/usr/bin/env python3
import time
import math

class JetsonOledDisplay:
    def __init__(self, width=128, height=64, i2c_bus=1):
        self.width = width
        self.height = height
        self.i2c_bus = i2c_bus
        self.device = None
        self.draw = None
        
        # Initial states
        self.expression = "NORMAL" # NORMAL, THINK, TALK, WARNING
        self.mouth_height = 0
        
        self.init_display()

    def init_display(self):
        try:
            # Check for luma.oled and luma.core.interface.serial libraries
            from luma.core.interface.serial import i2c
            from luma.oled.device import ssd1306
            from PIL import ImageDraw
            
            serial = i2c(port=self.i2c_bus, address=0x3C)
            self.device = ssd1306(serial, width=self.width, height=self.height)
            self.draw_builder = ImageDraw
            print(f"[OLED] SSD1306 successfully bound to I2C bus {self.i2c_bus}")
        except ImportError:
            print("[OLED] luma.oled/PIL libraries missing. Running display in mock terminal mode.")
        except Exception as e:
            print(f"[OLED] Hardware connection failed: {e}. Defaulting to mock.")

    def update_frame(self):
        if not self.device:
            # Mock console representation of display state
            print(f"[OLED MOCK] Face expression: {self.expression} | Mouth Height: {self.mouth_height}px")
            return

        from PIL import Image
        img = Image.new("1", (self.width, self.height))
        draw = self.draw_builder.Draw(img)
        
        # 1. Draw Eyes (Blinking Logic)
        eye_y = 20
        eye_size = 12
        blink = (int(time.time() * 2) % 4 == 0) # blink every 2 seconds
        
        if blink and self.expression == "NORMAL":
            # Draw shut eyes (flat lines)
            draw.line((20, eye_y, 40, eye_y), fill=255, width=3)
            draw.line((88, eye_y, 108, eye_y), fill=255, width=3)
        elif self.expression == "THINK":
            # Draw rotating thought arcs
            angle = time.time() * 5
            x_offset = int(math.cos(angle) * 5)
            y_offset = int(math.sin(angle) * 5)
            draw.ellipse((20 + x_offset, eye_y - 5 + y_offset, 40 + x_offset, eye_y + 15 + y_offset), outline=255, width=2)
            draw.ellipse((88 - x_offset, eye_y - 5 - y_offset, 108 - x_offset, eye_y + 15 - y_offset), outline=255, width=2)
        else:
            # Draw open eyes (circular shapes)
            draw.ellipse((20, eye_y - 5, 40, eye_y + 15), fill=255)
            draw.ellipse((88, eye_y - 5, 108, eye_y + 15), fill=255)

        # 2. Draw Mouth (Lip-Sync based on Speech amplitude)
        mouth_y = 48
        if self.expression == "TALK":
            # Oscillating speaking mouth
            self.mouth_height = int(abs(math.sin(time.time() * 15)) * 12)
            draw.ellipse((48, mouth_y - self.mouth_height//2, 80, mouth_y + self.mouth_height//2), outline=255, width=2)
        elif self.expression == "WARNING":
            # Flat wide line
            draw.line((40, mouth_y, 88, mouth_y), fill=255, width=4)
        else:
            # Happy curved line
            draw.arc((48, mouth_y - 5, 80, mouth_y + 10), 0, 180, fill=255)

        # Update physical display
        self.device.display(img)

    def set_expression(self, expression: str):
        self.expression = expression.upper()
        self.update_frame()

if __name__ == "__main__":
    display = JetsonOledDisplay()
    for exp in ["NORMAL", "THINK", "TALK", "WARNING"]:
        display.set_expression(exp)
        time.sleep(1.0)
