# IMUData.msg
# Inertial Measurement Unit data from ESP32 MPU6050

std_msgs/Header header

# Orientation (Euler angles in degrees)
float32 pitch
float32 roll
float32 yaw

# Raw Accelerometer data (m/s^2)
geometry_msgs/Vector3 linear_acceleration

# Raw Gyroscope data (rad/s)
geometry_msgs/Vector3 angular_velocity

# Drift warning threshold flag
bool drift_warning
