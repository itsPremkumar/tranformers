#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import xml.etree.ElementTree as ET
from robot_interfaces.msg import RobotStatus, BatteryState
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist

class BehaviorTreeExecutor(Node):
    def __init__(self):
        super().__init__('behavior_tree_executor')
        
        # Declare parameters
        self.declare_parameter('tree_config_path', '/robot_project/configs/autonomy_tree.xml')
        self.tree_config_path = self.get_parameter('tree_config_path').value
        
        # Core State Variables for Tree Evaluation
        self.is_fallen = False
        self.is_battery_low = False
        self.is_obstacle_critical = False
        self.is_dock_visible = False
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.bt_status_pub = self.create_publisher(String, '/robot/bt_status', 10)
        self.transform_pub = self.create_publisher(String, '/cmd_transform', 10)
        
        # Subscribers to feed Conditions
        self.create_subscription(Bool, '/robot/fall_alert', self.fall_callback, 10)
        self.create_subscription(BatteryState, '/sensor/battery', self.battery_callback, 10)
        self.create_subscription(Bool, '/sensor/dock_visible', self.dock_callback, 10)
        
        # Timer tick (10Hz)
        self.tick_timer = self.create_timer(0.1, self.tick)
        self.get_logger().info("Behavior Tree Autonomy Executor Active.")

    def fall_callback(self, msg: Bool):
        self.is_fallen = msg.data

    def battery_callback(self, msg: BatteryState):
        self.is_battery_low = msg.low_battery_warning

    def dock_callback(self, msg: Bool):
        self.is_dock_visible = msg.data

    def tick(self):
        # Evaluate Conditions sequentially following autonomy_tree.xml logic:
        # Fallback Node -> First child that succeeds:
        
        status = "ACTIVE_IDLE"
        
        # 1. Fall Recovery
        if self.is_fallen:
            status = "ACTION_GETTING_UP"
            self.execute_recovery()
            
        # 2. Low Battery Autodock
        elif self.is_battery_low:
            if self.is_dock_visible:
                status = "ACTION_DOCKING_APPROACH"
                # Handled directly by aruco_docking_node guiding /cmd_vel
            else:
                status = "ACTION_SEARCHING_FOR_DOCK"
                self.execute_search_spin()
                
        # 3. Default Nav
        else:
            status = "NORMAL_OPERATION"
            
        # Publish active Behavior Tree status
        status_msg = String()
        status_msg.data = status
        self.bt_status_pub.publish(status_msg)

    def execute_recovery(self):
        self.get_logger().warn("BT Executor: Robot is down! Sending Get-Up static sequence command...")
        # Proactively trigger transform check/stand recovery sequence
        # Write recovery serial command wrapper via pub
        rec_msg = String()
        rec_msg.data = "TRANSFORM"
        self.transform_pub.publish(rec_msg)

    def execute_search_spin(self):
        self.get_logger().info("BT Executor: Battery low & dock invisible. Initiating search sweep...")
        # Spin slowly in place to scan for the ArUco marker
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.5 # Rads/sec
        self.cmd_vel_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = BehaviorTreeExecutor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
