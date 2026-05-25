# RobotStatus.msg
# Overall state of the humanoid/transformer robot

std_msgs/Header header

# Operating Mode
uint8 MODE_HUMANOID = 0
uint8 MODE_CAR = 1
uint8 MODE_TRANSFORMING = 2
uint8 mode

# System State
string state_name # e.g., "WALKING", "STOPPED", "FALLEN", "AUTO_AVOID"

# Subsystem Health Flags
bool motors_ok
bool sensors_ok
bool imu_ok
bool communication_ok

# Error Message (if any)
string status_message
