#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from robot_interfaces.msg import RobotStatus, BatteryState, IMUData
from std_msgs.msg import String

class HealthMonitorNode(Node):
    def __init__(self):
        super().__init__('health_monitor_node')
        
        # Subscribers
        self.create_subscription(RobotStatus, '/robot/status', self.status_callback, 10)
        self.create_subscription(BatteryState, '/sensor/battery', self.battery_callback, 10)
        self.create_subscription(IMUData, '/imu/data_custom', self.imu_callback, 10)
        
        # Publisher for verbal warnings
        self.speak_pub = self.create_publisher(String, '/speech/speak', 10)
        
        # Track warning states to avoid spamming the audio engine
        self.last_battery_alert = 0.0
        self.last_current_alert = 0.0
        self.last_imu_alert = 0.0
        
        self.get_logger().info("Health Diagnostics Monitor Node active.")

    def status_callback(self, msg: RobotStatus):
        if not msg.motors_ok:
            self.get_logger().error("DIAGNOSTICS: Motor fault detected!")
        if not msg.sensors_ok:
            self.get_logger().error("DIAGNOSTICS: Sensor read failure!")
        if not msg.imu_ok:
            self.get_logger().error("DIAGNOSTICS: IMU initialization or connection lost!")

    def battery_callback(self, msg: BatteryState):
        current_time = time_in_sec = self.get_clock().now().nanoseconds / 1e9
        
        if msg.low_battery_warning:
            # Alert every 60 seconds
            if current_time - self.last_battery_alert > 60.0:
                self.last_battery_alert = current_time
                alert_text = f"Warning. Battery power is critical at {msg.percentage:.1f} percent. Please charge."
                self.get_logger().warn(alert_text)
                self.speak(alert_text)
                
        if msg.over_current_fault:
            if current_time - self.last_current_alert > 10.0:
                self.last_current_alert = current_time
                alert_text = "Alert! High current spike detected in motors! Safety lock engaged."
                self.get_logger().error(alert_text)
                self.speak(alert_text)

    def imu_callback(self, msg: IMUData):
        current_time = self.get_clock().now().nanoseconds / 1e9
        if msg.drift_warning:
            if current_time - self.last_imu_alert > 30.0:
                self.last_imu_alert = current_time
                alert_text = "Diagnostics notice: Pitch and Roll angles exceed normal threshold. Verifying chassis alignment."
                self.get_logger().warn(alert_text)
                self.speak(alert_text)

    def speak(self, phrase: str):
        msg = String()
        msg.data = phrase
        self.speak_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = HealthMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
