# BatteryState.msg
# Battery and power diagnostics telemetry

std_msgs/Header header

float32 voltage          # Volts (e.g. 7.4V - 8.4V for 2S LiPo)
float32 current_draw     # Amperes (motor current draw)
float32 percentage       # Charge percentage (0.0 to 100.0)

bool is_charging
bool low_battery_warning # True if percentage < 15%
bool over_current_fault  # True if current exceeds 3.0A safety threshold
