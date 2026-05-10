Transformer Robot – Detailed Components List with Uses


---

1. Main Control System

ESP32 Dev Board × 2

Use:

Main robot brain

Controls servo motors

Controls DC motors

Sensor reading

Wi-Fi communication

WebSocket communication

Command execution

Transformation logic


Why 2:

One for motion control
One for communication + internet + audio


---

ESP32-CAM × 1

Use:

Live video streaming

Camera vision

Remote monitoring

Flash LED light

Face/object detection (basic)



---

SIM7600 × 1

Use:

Internet connection anywhere

IoT remote access

Cloud connection

WebSocket communication

Remote robot control



---

IoT SIM Card × 1

Use:

Data plan for SIM7600

Permanent internet access



---

2. Motion System


---

MG996R / DS3218 × 14–18

Use:

Head movement

Hand movement

Leg movement

Hip movement

Transformation joints


Why:

Robot needs strong torque for lifting body weight


---

PCA9685 × 2

Use:

Controls multiple servos safely

Stable PWM signal generation

Reduces ESP32 load


Why:

ESP32 cannot safely control many servos directly


---

L298N Motor Driver

Use:

Controls DC motors

Car mode movement

Forward / backward / turning


Important:

Use separate motor power supply


---

12V Geared DC Motor × 4

Use:

Car mode driving

Wheel movement


Why:

Needed for transformer robot car mode


---

Wheel Set × 4

Use:

Robot movement in car mode



---

Mecanum Wheels × 4 (Optional)

Use:

Side movement

Diagonal movement

Omni-directional driving


Why:

Normal wheels cannot move sideways


for fornt two wheel

Swivel wheel

---

3. Balance + Safety Sensors


---

MPU6050 × 1

Use:

Accelerometer

Gyroscope

Balance detection

Tilt detection

Fall detection

Robot stabilization


Very Important:

Critical for walking robot


---

Fall Detection Sensor × 1

Use:

Detect robot falling

Trigger safety stop

Auto recovery


Note:

Can also use MPU6050 for this


---

4. Audio System


---

INMP441 × 1

Use:

Voice input

Command recognition

Audio capture



---

MAX98357A × 1

Use:

Audio output amplifier

Voice assistant speaking



---

Mini Speaker 4Ω / 8Ω × 1

Use:

Robot voice output

Alerts

Audio feedback



---

5. Display + Lighting


---

OLED Display × 1

Use:

Battery status

Internet status

Mode display

Sensor status

Debug information



---

LED Light Module × 1

Use:

Flashlight

Eye effect

Night camera support


Optional:

ESP32-CAM flash can also be used


---

6. Power System (Most Important)


---

18650 Li-ion Battery × 6–8

Use:

Main robot power source


Why:

Portable power for full robot system


---

18650 Battery Holder × 1

Use:

Safe battery mounting



---

3S / 4S BMS Protection Board × 1

Use:

Overcharge protection

Over-discharge protection

Short circuit protection

Battery safety



---

Buck Converter Module × 2

Use:

Step down voltage


Example:

12V → 5V
12V → 7.4V


---

Voltage Regulator Module × 2

Use:

Stable voltage supply

Protect ESP32 and sensors



---

Power Distribution Board × 1

Use:

Clean power distribution to all modules



---

7. Safety Components


---

Main Power Switch × 1

Use:

Full robot ON/OFF control



---

Emergency Kill Switch × 1

Use:

Immediate emergency shutdown


Very Important:

Must have during testing


---

Fuse Protection × 1

Use:

Protect against short circuit



---

Battery Level Monitor × 1

Use:

Monitor battery percentage

Low battery alert



---

8. Mechanical Structure


---

Robot Chassis Frame × 1

Use:

Full body support



---

Metal Servo Brackets Set

Use:

Servo mounting

Joint structure



---

Bearings Set

Use:

Smooth movement

Reduce friction



---

Screws + Nuts Set

Use:

Full assembly support



---

Couplers + Mounts

Use:

Motor connection

Wheel connection

Joint fixing



---

9. Wiring + Connection


---

Jumper Wires

Use:

Signal connections



---

Terminal Blocks

Use:

Strong power connection



---

Connectors Set

Use:

Clean detachable wiring



---

Charging Port Module

Use:

External battery charging



---

10. Cooling System


---

Heat Sink + Cooling Fan

Use:

Prevent overheating


Needed for:

L298N

SIM7600

Voltage regulators

Power system



---

Final Truth

Most Important Parts

Priority Order

1. Power System


2. Mechanical Design


3. Servo Torque


4. Balance Sensor


5. Communication System



These decide success of the robot.


ultrasonic sensor for the robot to detect obstacles

the ultrasonic sensor and the esp32 camera  is present in the top of the degree of freedom in the with Pan-Tilt + Hole Detection servo motors 
