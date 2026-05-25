#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from robot_interfaces.msg import IMUData, RobotStatus
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist

class BalanceControlNode(Node):
    def __init__(self):
        super().__init__('balance_control_node')
        
        # Declare parameters
        self.declare_parameter('kp_yaw', 0.02)
        self.declare_parameter('kd_yaw', 0.005)
        self.declare_parameter('kp_pitch', 0.05)
        self.declare_parameter('critical_angle_limit', 30.0) # Degrees
        
        self.kp_yaw = self.get_parameter('kp_yaw').value
        self.kd_yaw = self.get_parameter('kd_yaw').value
        self.kp_pitch = self.get_parameter('kp_pitch').value
        self.critical_limit = self.get_parameter('critical_angle_limit').value
        
        # PID Variables
        self.last_yaw_error = 0.0
        self.target_yaw = 0.0
        self.is_moving = False
        
        # Publishers
        self.fall_alert_pub = self.create_publisher(Bool, '/robot/fall_alert', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Subscribers
        self.create_subscription(IMUData, '/imu/data_custom', self.imu_callback, 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        self.get_logger().info("Closed-Loop Balance and Yaw Control Node initialized.")

    def cmd_vel_callback(self, msg: Twist):
        # Update motion state
        threshold = 0.01
        self.is_moving = abs(msg.linear.x) > threshold or abs(msg.angular.z) > threshold

    def imu_callback(self, msg: IMUData):
        # 1. Fall Detection Guard
        # If absolute pitch or roll exceeds the critical safety threshold, trigger a fall alert.
        if abs(msg.pitch) > self.critical_limit or abs(msg.roll) > self.critical_limit:
            self.get_logger().error(f"FALL DETECTED: Pitch={msg.pitch:.1f} Roll={msg.roll:.1f} - Triggering Emergency Safety Cutoff!")
            fall_msg = Bool()
            fall_msg.data = True
            self.fall_alert_pub.publish(fall_msg)
            
            # Immediately override velocity to zero
            emergency_stop = Twist()
            self.cmd_vel_pub.publish(emergency_stop)
            return

        # 2. Straight-Drive Yaw Assist
        # If the robot is driving straight (has linear velocity but zero angular intent),
        # use the IMU yaw to apply minor differential steering corrections.
        if self.is_moving:
            yaw_error = self.target_yaw - msg.yaw
            
            # Normalize yaw error to [-180, 180]
            while yaw_error > 180.0: yaw_error -= 360.0
            while yaw_error < -180.0: yaw_error += 360.0
            
            # Calculate derivative component
            yaw_derivative = yaw_error - self.last_yaw_error
            self.last_yaw_error = yaw_error
            
            # Calculate correction
            correction = (yaw_error * self.kp_yaw) + (yaw_derivative * self.kd_yaw)
            
            # In a full setup, this correction is forwarded as a differential command 
            # to adjust the wheel velocities or walking stride angles.
            self.get_logger().debug(f"Yaw Assist Correction: {correction:.3f}")
        else:
            # If stationary, lock current yaw as the target direction
            self.target_yaw = msg.yaw
            self.last_yaw_error = 0.0

def main(args=None):
    rclpy.init(args=args)
    node = BalanceControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
