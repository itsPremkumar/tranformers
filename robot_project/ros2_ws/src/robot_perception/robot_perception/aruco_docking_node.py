#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class ArucoDockingNode(Node):
    def __init__(self):
        super().__init__('aruco_docking_node')
        
        # Declare parameters
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('dock_marker_id', 42)
        self.declare_parameter('target_distance_m', 0.15)
        
        self.camera_topic = self.get_parameter('camera_topic').value
        self.dock_marker_id = self.get_parameter('dock_marker_id').value
        self.target_distance = self.get_parameter('target_distance_m').value
        
        self.bridge = CvBridge()
        
        # Dictionary and parameters for ArUco detection
        # Compatibility handling for various OpenCV versions (dict selection)
        if hasattr(cv2.aruco, 'DICT_6X6_250'):
            self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
            self.aruco_params = cv2.aruco.DetectorParameters()
        else:
            self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
            self.aruco_params = cv2.aruco.DetectorParameters_create()

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.dock_visible_pub = self.create_publisher(Bool, '/sensor/dock_visible', 10)
        self.dock_status_pub = self.create_publisher(String, '/robot/dock_status', 10)
        
        # Subscriber to image topic
        self.create_subscription(Image, self.camera_topic, self.image_callback, 10)
        
        self.get_logger().info(f"ArUco Docking Node initialized. Looking for Marker ID {self.dock_marker_id}")

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Image conversion failed: {e}")
            return
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect markers
        # OpenCV version compatibility check for detectMarkers call signature
        if hasattr(cv2.aruco, 'detectMarkers'):
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)
        else:
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)
            
        dock_found = False
        twist = Twist()
        
        if ids is not None:
            # Flatten IDs array
            flat_ids = ids.flatten()
            if self.dock_marker_id in flat_ids:
                dock_idx = np.where(flat_ids == self.dock_marker_id)[0][0]
                marker_corners = corners[dock_idx][0]
                
                dock_found = True
                
                # Calculate center point of the ArUco marker
                center_x = int(np.mean(marker_corners[:, 0]))
                center_y = int(np.mean(marker_corners[:, 1]))
                
                # Calculate deviation from camera center
                img_width = frame.shape[1]
                frame_center_x = img_width / 2
                offset_x = center_x - frame_center_x
                
                # Proportional steering to center the marker
                steering_gain = 0.005
                twist.angular.z = -float(offset_x * steering_gain)
                
                # Calculate size/area of the marker corners to approximate distance
                marker_width_px = np.linalg.norm(marker_corners[0] - marker_corners[1])
                
                # Distance estimation formula based on focal length model
                # Z_est = (known_width * focal_length) / width_px
                # We simplify to proportional scale for movement commands
                target_width_px = 120.0 # Pixel width when docked
                
                width_error = target_width_px - marker_width_px
                forward_gain = 0.002
                
                if width_error > 10.0:
                    # Drive forward slowly to approach dock
                    twist.linear.x = float(width_error * forward_gain)
                    # Limit speed
                    twist.linear.x = min(0.15, max(0.02, twist.linear.x))
                    status = "APPROACHING"
                elif width_error < -10.0:
                    # Back up slowly
                    twist.linear.x = float(width_error * forward_gain)
                    twist.linear.x = max(-0.1, min(-0.02, twist.linear.x))
                    status = "BACKING_UP"
                else:
                    # Dock reached, halt and trigger latching
                    twist.linear.x = 0.0
                    twist.angular.z = 0.0
                    status = "DOCKED"
                    
                status_msg = String()
                status_msg.data = status
                self.dock_status_pub.publish(status_msg)
                self.cmd_vel_pub.publish(twist)
                self.get_logger().info(f"Dock alignment: offset_x={offset_x:.1f}, dist_err={width_error:.1f} -> cmd_vel.x={twist.linear.x:.2f}")

        # Publish visibility status
        visible_msg = Bool()
        visible_msg.data = dock_found
        self.dock_visible_pub.publish(visible_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ArucoDockingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
