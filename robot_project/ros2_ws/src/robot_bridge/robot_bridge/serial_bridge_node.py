#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import serial
import threading
import time
from std_msgs.msg import String, Int32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range, Imu
from robot_interfaces.msg import RobotStatus, IMUData, BatteryState
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue

class SerialBridgeNode(Node):
    def __init__(self):
        super().__init__('serial_bridge_node')
        
        # Declare parameters
        self.declare_parameter('port', '/dev/ttyRobotMotion')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('heartbeat_interval', 1.0) # seconds
        self.declare_parameter('timeout', 1.0)
        
        self.port = self.get_parameter('port').value
        self.baudrate = self.get_parameter('baudrate').value
        self.heartbeat_interval = self.get_parameter('heartbeat_interval').value
        self.timeout = self.get_parameter('timeout').value
        
        self.serial_conn = None
        self.is_connected = False
        self.lock = threading.Lock()
        
        # Publishers
        self.status_pub = self.create_publisher(RobotStatus, '/robot/status', 10)
        self.battery_pub = self.create_publisher(BatteryState, '/sensor/battery', 10)
        self.range_pub = self.create_publisher(Range, '/sensor/ultrasonic', 10)
        self.imu_pub = self.create_publisher(IMUData, '/imu/data_custom', 10)
        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        
        # Subscribers
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.create_subscription(String, '/cmd_transform', self.transform_callback, 10)
        self.create_subscription(Int32, '/head/pan', self.pan_callback, 10)
        self.create_subscription(Int32, '/head/tilt', self.tilt_callback, 10)
        
        # Connect to serial port
        self.connect_serial()
        
        # Start reading thread
        self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.read_thread.start()
        
        # Start heartbeat timer
        self.heartbeat_timer = self.create_timer(self.heartbeat_interval, self.send_heartbeat)
        
        # Start diagnostics timer
        self.diag_timer = self.create_timer(2.0, self.publish_diagnostics)
        
        self.get_logger().info(f"Serial Bridge Node initialized on port {self.port} at {self.baudrate} baud.")

    def connect_serial(self):
        while rclpy.ok() and not self.is_connected:
            try:
                self.get_logger().info(f"Attempting to connect to serial port {self.port}...")
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                self.is_connected = True
                self.get_logger().info("Serial connection established successfully.")
            except serial.SerialException as e:
                self.get_logger().error(f"Serial connection failed: {e}. Retrying in 2 seconds...")
                time.sleep(2)

    def write_to_serial(self, data: str):
        with self.lock:
            if self.is_connected and self.serial_conn:
                try:
                    self.serial_conn.write(f"{data}\n".encode('utf-8'))
                except serial.SerialException as e:
                    self.get_logger().error(f"Failed to write to serial: {e}")
                    self.is_connected = False
                    self.serial_conn.close()
                    # Reconnect in background
                    threading.Thread(target=self.connect_serial, daemon=True).start()

    def send_heartbeat(self):
        if self.is_connected:
            self.write_to_serial("BEAT")

    def cmd_vel_callback(self, msg: Twist):
        # Translate Twist geometry velocity to robot directional commands
        linear_x = msg.linear.x
        angular_z = msg.angular.z
        
        # Deadband threshold
        threshold = 0.05
        
        if abs(linear_x) < threshold and abs(angular_z) < threshold:
            self.write_to_serial("CMD:STOP")
        elif linear_x > threshold:
            if angular_z > threshold:
                self.write_to_serial("CMD:LEFT") # Move left-forward or pivot left
            elif angular_z < -threshold:
                self.write_to_serial("CMD:RIGHT")
            else:
                self.write_to_serial("CMD:FORWARD")
        elif linear_x < -threshold:
            self.write_to_serial("CMD:BACKWARD")
        else:
            if angular_z > threshold:
                self.write_to_serial("CMD:LEFT")
            else:
                self.write_to_serial("CMD:RIGHT")

    def transform_callback(self, msg: String):
        command = msg.data.upper()
        if command in ["TRANSFORM", "CMD:TRANSFORM"]:
            self.get_logger().info("Forwarding Transform command to ESP32...")
            self.write_to_serial("CMD:TRANSFORM")

    def pan_callback(self, msg: Int32):
        angle = max(0, min(180, msg.data))
        self.write_to_serial(f"PAN:{angle}")

    def tilt_callback(self, msg: Int32):
        angle = max(0, min(180, msg.data))
        self.write_to_serial(f"TILT:{angle}")

    def read_loop(self):
        while rclpy.ok():
            if self.is_connected and self.serial_conn:
                try:
                    line = self.serial_conn.readline()
                    if line:
                        decoded = line.decode('utf-8', errors='ignore').strip()
                        if decoded:
                            self.parse_telemetry(decoded)
                except Exception as e:
                    self.get_logger().error(f"Read error: {e}")
                    self.is_connected = False
                    self.serial_conn.close()
                    threading.Thread(target=self.connect_serial, daemon=True).start()
            else:
                time.sleep(0.1)

    def parse_telemetry(self, data: str):
        self.get_logger().debug(f"Telemetry received: {data}")
        
        # Parse Distance
        if data.startswith("DISTANCE:"):
            try:
                distance_cm = float(data[9:])
                range_msg = Range()
                range_msg.header.stamp = self.get_clock().now().to_msg()
                range_msg.header.frame_id = "ultrasonic_sensor_link"
                range_msg.radiation_type = Range.ULTRASONIC
                range_msg.field_of_view = 0.26 # ~15 degrees
                range_msg.min_range = 0.02
                range_msg.max_range = 4.0
                range_msg.range = distance_cm / 100.0 # Convert to meters
                self.range_pub.publish(range_msg)
            except ValueError:
                pass
                
        # Parse Battery / Current
        elif data.startswith("BATTERY:") or data.startswith("CURRENT:"):
            # Format could be BATTERY:V_val,I_val
            parts = data.split(",")
            battery_msg = BatteryState()
            battery_msg.header.stamp = self.get_clock().now().to_msg()
            
            for part in parts:
                if part.startswith("BATTERY:"):
                    try:
                        battery_msg.voltage = float(part[8:])
                        # Simple percentage approximation for 2S LiPo (7.2V to 8.4V)
                        volts = battery_msg.voltage
                        percentage = ((volts - 7.0) / (8.4 - 7.0)) * 100.0
                        battery_msg.percentage = max(0.0, min(100.0, percentage))
                        battery_msg.low_battery_warning = battery_msg.percentage < 15.0
                    except ValueError:
                        pass
                elif part.startswith("CURRENT:"):
                    try:
                        battery_msg.current_draw = float(part[8:])
                        battery_msg.over_current_fault = battery_msg.current_draw > 3.0
                    except ValueError:
                        pass
            self.battery_pub.publish(battery_msg)
            
        # Parse IMU Data
        elif data.startswith("IMU:"):
            # Format: IMU:pitch,roll,yaw,ax,ay,az,gx,gy,gz
            try:
                vals = data[4:].split(",")
                if len(vals) >= 3:
                    imu_msg = IMUData()
                    imu_msg.header.stamp = self.get_clock().now().to_msg()
                    imu_msg.pitch = float(vals[0])
                    imu_msg.roll = float(vals[1])
                    imu_msg.yaw = float(vals[2])
                    
                    if len(vals) >= 9:
                        imu_msg.linear_acceleration.x = float(vals[3])
                        imu_msg.linear_acceleration.y = float(vals[4])
                        imu_msg.linear_acceleration.z = float(vals[5])
                        
                        imu_msg.angular_velocity.x = float(vals[6])
                        imu_msg.angular_velocity.y = float(vals[7])
                        imu_msg.angular_velocity.z = float(vals[8])
                    
                    # Watch for high drift
                    imu_msg.drift_warning = abs(imu_msg.pitch) > 45.0 or abs(imu_msg.roll) > 45.0
                    self.imu_pub.publish(imu_msg)
            except ValueError:
                pass
                
        # Parse Status Diagnostics
        elif data.startswith("[PASS]") or data.startswith("[FAIL]"):
            self.get_logger().info(f"ESP32 Diagnostics: {data}")

    def publish_diagnostics(self):
        diag_array = DiagnosticArray()
        diag_array.header.stamp = self.get_clock().now().to_msg()
        
        status = DiagnosticStatus()
        status.name = "Hardware Bridge: Serial Link"
        
        if self.is_connected:
            status.level = DiagnosticStatus.OK
            status.message = "Connected to ESP32 Motion Controller"
        else:
            status.level = DiagnosticStatus.ERROR
            status.message = "Disconnected from ESP32"
            
        status.values = [
            KeyValue(key="port", value=self.port),
            KeyValue(key="baudrate", value=str(self.baudrate)),
            KeyValue(key="connected", value=str(self.is_connected))
        ]
        
        diag_array.status.append(status)
        self.diag_pub.publish(diag_array)

def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.serial_conn:
            node.serial_conn.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
