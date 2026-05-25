#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import time
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range

class BehaviorTreeNode(Node):
    def __init__(self):
        super().__init__('behavior_tree_node')
        
        # Subscribers
        self.create_subscription(Range, '/sensor/ultrasonic', self.ultrasonic_callback, 10)
        self.create_subscription(String, '/robot/gesture', self.gesture_callback, 10)
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.transform_pub = self.create_publisher(String, '/cmd_transform', 10)
        
        # State variables
        self.current_obstacle_dist = 1.0 # meters
        self.active_gesture = "NONE"
        self.tree_running = True
        
        # Timer loop for tick (5Hz)
        self.tick_timer = self.create_timer(0.2, self.tick)
        self.get_logger().info("Behavior Tree Executor Node initialized.")

    def ultrasonic_callback(self, msg: Range):
        self.current_obstacle_dist = msg.range

    def gesture_callback(self, msg: String):
        self.active_gesture = msg.data

    def tick(self):
        if not self.tree_running:
            return
            
        # Execute Behavior Tree Sequence:
        # 1. Safety Check (Condition) -> If obstacle < 0.3m, stop.
        # 2. Gesture Mode (Sequence) -> If hand gesture detected, override.
        # 3. Default Nav (Fallback) -> Otherwise, maintain current goal.
        
        if self.current_obstacle_dist < 0.3:
            # Action: Stop immediately due to obstacle
            self.execute_stop("CRITICAL_OBSTACLE")
        elif self.active_gesture == "STOP_PALM":
            self.execute_stop("GESTURE_STOP")
        elif self.active_gesture == "POINT_FORWARD":
            self.execute_forward("GESTURE_FORWARD")
        else:
            # Default running state, let high-level nav planning manage
            pass

    def execute_stop(self, reason: str):
        self.get_logger().warn(f"BT Action [STOP] triggered by: {reason}")
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)

    def execute_forward(self, reason: str):
        self.get_logger().info(f"BT Action [FORWARD] triggered by: {reason}")
        twist = Twist()
        twist.linear.x = 0.15
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = BehaviorTreeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
