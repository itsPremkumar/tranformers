#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import can
import struct
import threading
from std_msgs.msg import String, Int32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range
from robot_interfaces.msg import RobotStatus, IMUData, BatteryState
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue

# CAN IDs definitions
CAN_ID_CMD_VEL       = 0x100
CAN_ID_CMD_TRANS     = 0x101
CAN_ID_PAN_TILT      = 0x102
CAN_ID_TELE_DIST     = 0x200
CAN_ID_TELE_BAT      = 0x201
CAN_ID_TELE_IMU_ACC  = 0x202
CAN_ID_TELE_IMU_GYRO = 0x203

class CanBridgeNode(Node):
    def __init__(self):
        super().__init__('can_bridge_node')
        
        # Declare parameters
        self.declare_parameter('interface', 'socketcan')
        self.declare_parameter('channel', 'can0')
        self.declare_parameter('bitrate', 500000)
        
        self.interface = self.get_parameter('interface').value
        self.channel = self.get_parameter('channel').value
        self.bitrate = self.get_parameter('bitrate').value
        
        self.bus = None
        self.is_connected = False
        self.lock = threading.Lock()
        
        # Publishers
        self.range_pub = self.create_publisher(Range, '/sensor/ultrasonic', 10)
        self.battery_pub = self.create_publisher(BatteryState, '/sensor/battery', 10)
        self.imu_pub = self.create_publisher(IMUData, '/imu/data_custom', 10)
        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        
        # Subscribers
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.create_subscription(String, '/cmd_transform', self.transform_callback, 10)
        self.create_subscription(Int32, '/head/pan', self.pan_callback, 10)
        self.create_subscription(Int32, '/head/tilt', self.tilt_callback, 10)
        
        # Connect to CAN Bus
        self.connect_can()
        
        # Start receive loop thread
        self.recv_thread = threading.Thread(target=self.recv_loop, daemon=True)
        self.recv_thread.start()
        
        # Diagnostics timer
        self.diag_timer = self.create_timer(2.0, self.publish_diagnostics)
        
        self.get_logger().info(f"CAN Bridge Node initialized on interface {self.interface} channel {self.channel} at {self.bitrate} bps.")

    def connect_can(self):
        try:
            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype=self.interface,
                bitrate=self.bitrate
            )
            self.is_connected = True
            self.get_logger().info("SocketCAN bus connection active.")
        except Exception as e:
            self.get_logger().error(f"CAN Bus connection failed: {e}.")
            self.is_connected = False

    def send_can_message(self, arbitration_id, data):
        if not self.is_connected or not self.bus:
            return
        msg = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=False
        )
        with self.lock:
            try:
                self.bus.send(msg)
            except Exception as e:
                self.get_logger().error(f"Failed to transmit CAN packet: {e}")
                self.is_connected = False

    def cmd_vel_callback(self, msg: Twist):
        # Pack linear.x and angular.z as float values (4 bytes each) into a 8-byte payload
        data = struct.pack('ff', msg.linear.x, msg.angular.z)
        self.send_can_message(CAN_ID_CMD_VEL, data)

    def transform_callback(self, msg: String):
        command = msg.data.upper()
        if command in ["TRANSFORM", "CMD:TRANSFORM"]:
            # Pack value 1 to indicate transform trigger
            data = struct.pack('B', 1)
            self.send_can_message(CAN_ID_CMD_TRANS, data)

    def pan_callback(self, msg: Int32):
        data = struct.pack('h', msg.data) # Pack 16-bit integer
        self.send_can_message(CAN_ID_PAN_TILT, data + b'\x00\x00\x00\x00\x00\x00') # Zero-padded

    def tilt_callback(self, msg: Int32):
        # High byte can represent tilt, or we can use custom packaging.
        # Pack pan = -1 (no change) and tilt as 16-bit integer
        data = struct.pack('hh', -1, msg.data)
        self.send_can_message(CAN_ID_PAN_TILT, data + b'\x00\x00\x00\x00')

    def recv_loop(self):
        # Temp variables for multi-packet telemetry
        latest_imu = IMUData()
        
        while rclpy.ok():
            if self.is_connected and self.bus:
                try:
                    msg = self.bus.recv(timeout=1.0)
                    if msg:
                        self.process_can_packet(msg, latest_imu)
                except Exception as e:
                    self.get_logger().error(f"CAN read loop exception: {e}")
                    self.is_connected = False
            else:
                # Try to reconnect
                self.connect_can()
                threading.Event().wait(2.0)

    def process_can_packet(self, msg, imu_msg):
        # Process Distance Telemetry
        if msg.arbitration_id == CAN_ID_TELE_DIST:
            try:
                distance_cm = struct.unpack('f', msg.data[:4])[0]
                range_msg = Range()
                range_msg.header.stamp = self.get_clock().now().to_msg()
                range_msg.header.frame_id = "ultrasonic_sensor_link"
                range_msg.radiation_type = Range.ULTRASONIC
                range_msg.min_range = 0.02
                range_msg.max_range = 4.0
                range_msg.range = distance_cm / 100.0
                self.range_pub.publish(range_msg)
            except struct.error:
                pass
                
        # Process Battery Telemetry
        elif msg.arbitration_id == CAN_ID_TELE_BAT:
            try:
                voltage, current = struct.unpack('ff', msg.data)
                bat_msg = BatteryState()
                bat_msg.header.stamp = self.get_clock().now().to_msg()
                bat_msg.voltage = voltage
                bat_msg.current_draw = current
                percentage = ((voltage - 7.0) / (8.4 - 7.0)) * 100.0
                bat_msg.percentage = max(0.0, min(100.0, percentage))
                bat_msg.low_battery_warning = bat_msg.percentage < 15.0
                bat_msg.over_current_fault = bat_msg.current_draw > 3.0
                self.battery_pub.publish(bat_msg)
            except struct.error:
                pass
                
        # Process IMU ACC Telemetry
        elif msg.arbitration_id == CAN_ID_TELE_IMU_ACC:
            try:
                pitch, roll, yaw = struct.unpack('fff', msg.data[:12])
                imu_msg.header.stamp = self.get_clock().now().to_msg()
                imu_msg.pitch = pitch
                imu_msg.roll = roll
                imu_msg.yaw = yaw
            except struct.error:
                pass
                
        # Process IMU GYRO/ACC values
        elif msg.arbitration_id == CAN_ID_TELE_IMU_GYRO:
            try:
                ax, ay, az = struct.unpack('fff', msg.data[:12])
                imu_msg.linear_acceleration.x = ax
                imu_msg.linear_acceleration.y = ay
                imu_msg.linear_acceleration.z = az
                # Publish combined IMU data
                self.imu_pub.publish(imu_msg)
            except struct.error:
                pass

    def publish_diagnostics(self):
        diag_array = DiagnosticArray()
        diag_array.header.stamp = self.get_clock().now().to_msg()
        
        status = DiagnosticStatus()
        status.name = "Hardware Bridge: SocketCAN Link"
        
        if self.is_connected:
            status.level = DiagnosticStatus.OK
            status.message = "Connected to SocketCAN"
        else:
            status.level = DiagnosticStatus.ERROR
            status.message = "SocketCAN offline"
            
        status.values = [
            KeyValue(key="interface", value=self.interface),
            KeyValue(key="channel", value=self.channel),
            KeyValue(key="bitrate", value=str(self.bitrate)),
            KeyValue(key="connected", value=str(self.is_connected))
        ]
        
        diag_array.status.append(status)
        self.diag_pub.publish(diag_array)

def main(args=None):
    rclpy.init(args=args)
    node = CanBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.bus:
            node.bus.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
