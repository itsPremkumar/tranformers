# 🔌 NVIDIA Jetson 40-Pin Header Connector Mapping
> **Hardware Configuration Sheet**

This guide documents the absolute GPIO configurations and pin mapping connections required to wire components directly to the onboard Jetson Nano / Orin Nano 40-pin header.

---

## 1. SSD1306 OLED Display (I2C1 Bus)

*   **Jetson Pin 1 (3.3V)** or **Pin 2 (5.0V)** ──► OLED `VCC`
*   **Jetson Pin 9 (GND)** or **Pin 6 (GND)** ──► OLED `GND`
*   **Jetson Pin 3 (I2C1_SDA)** ──► OLED `SDA`
*   **Jetson Pin 5 (I2C1_SCL)** ──► OLED `SCL`

*Note: Enable the physical I2C1 bus using `sudo /opt/nvidia/jetson-io/jetson-io.py` or editing the system device tree overlay.*

---

## 2. MAX98357A I2S Audio Amplifier (I2S4 Bus)

*   **Jetson Pin 4 (5.0V)** ──► Amp `VIN`
*   **Jetson Pin 34 (GND)** ──► Amp `GND`
*   **Jetson Pin 12 (I2S_SCLK / BCLK)** ──► Amp `BCLK`
*   **Jetson Pin 35 (I2S_LRCK / LRCLK)** ──► Amp `LRC` (Left-Right Clock)
*   **Jetson Pin 40 (I2S_SDOUT / DIN)** ──► Amp `DIN` (Data Input)

*Note: Multiplex pins 12, 35, and 40 to I2S outputs via `jetson-io.py`. Use integration script `setup_jetson.sh` to automate.*

---

## 3. CP2102 USB-to-TTL Serial Bridge (UART)

*Connects from Jetson USB 3.0 type-A ports to ESP32 Hardware Serial2:*

```
[ Jetson USB Port ] <─── Standard USB Cable ───> [ CP2102 Board ]
                                                       │
                                                       ├─► RXD  ───► ESP32 GPIO 17 (TXD)
                                                       ├─► TXD  ───► ESP32 GPIO 16 (RXD)
                                                       └─► GND  ───► ESP32 GND
```

*Note: The CP2102 requires a secure ground reference (`GND`) loop with the ESP32 to prevent UART frame corruptions.*

---

## 4. Waveshare SN65HVD230 CAN Transceiver (Native CAN)

*For Jetson Orin Nano / Xavier NX native CAN transceiver bindings:*

*   **Jetson Pin 29 (CAN_TX)** ──► Transceiver `TXD`
*   **Jetson Pin 31 (CAN_RX)** ──► Transceiver `RXD`
*   **Jetson Pin 1 (3.3V)** ──► Transceiver `3.3V`
*   **Jetson Pin 39 (GND)** ──► Transceiver `GND`
*   **Transceiver `CAN_H`** ──► ESP32 CAN Controller `CAN_H`
*   **Transceiver `CAN_L`** ──► ESP32 CAN Controller `CAN_L`

*Note: Verify that a 120-ohm termination resistor is bridged across CAN_H and CAN_L lines.*
