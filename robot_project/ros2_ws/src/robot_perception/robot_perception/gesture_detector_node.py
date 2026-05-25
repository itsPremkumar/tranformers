#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class GestureDetectorNode(Node):
    def __init__(self):
        super().__init__('gesture_detector_node')
        
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.camera_topic = self.get_parameter('camera_topic').value
        
        self.bridge = CvBridge()
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.gesture_pub = self.create_publisher(String, '/robot/gesture', 10)
        
        # Subscriber
        self.create_subscription(Image, self.camera_topic, self.image_callback, 10)
        
        # Lazy load mediapipe to avoid startup delays
        self.mp_hands = None
        self.hands = None
        
        self.get_logger().info("Gesture Detector Node initialized and listening on " + self.camera_topic)

    def init_mediapipe(self):
        try:
            import mediapipe as mp
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            self.get_logger().info("MediaPipe Hands library initialized successfully.")
        except ImportError:
            self.get_logger().error("MediaPipe not installed! Run pip install mediapipe.")

    def image_callback(self, msg: Image):
        if self.hands is None:
            self.init_mediapipe()
            if self.hands is None:
                return # Skip if MediaPipe could not be loaded
                
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Image conversion failed: {e}")
            return
            
        # Flip image horizontally for natural mirroring
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Classify gesture based on finger counts
                gesture = self.classify_gesture(hand_landmarks)
                
                if gesture:
                    gesture_msg = String()
                    gesture_msg.data = gesture
                    self.gesture_pub.publish(gesture_msg)
                    
                    self.execute_gesture_command(gesture)
                    
    def classify_gesture(self, hand_landmarks) -> str:
        # Landmarks map: 4=Thumb tip, 8=Index tip, 12=Middle tip, 16=Ring tip, 20=Pinky tip
        # Knuckle landmarks: 3=Thumb knuckle, 6=Index knuckle, 10=Middle knuckle, 14=Ring knuckle, 18=Pinky knuckle
        
        tips = [8, 12, 16, 20]
        knuckles = [6, 10, 14, 18]
        
        fingers_open = []
        
        # Check standard 4 fingers
        for tip, knuckle in zip(tips, knuckles):
            # If Y coordinate of tip is less than Y coordinate of knuckle (origin is top-left)
            fingers_open.append(hand_landmarks.landmark[tip].y < hand_landmarks.landmark[knuckle].y)
            
        # Check thumb (X coordinate comparison)
        thumb_open = hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x
        fingers_open.insert(0, thumb_open)
        
        open_count = sum(fingers_open)
        
        # Map finger configs to commands
        if open_count == 5:
            return "STOP_PALM"
        elif open_count == 1 and fingers_open[1]: # Only index finger open
            return "POINT_FORWARD"
        elif open_count == 2 and fingers_open[1] and fingers_open[2]: # Index and Middle open (V sign)
            return "VICTORY_DANCE"
        
        return "UNKNOWN"

    def execute_gesture_command(self, gesture: str):
        twist = Twist()
        if gesture == "STOP_PALM":
            # HALT
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.cmd_vel_pub.publish(twist)
            self.get_logger().info("Gesture [STOP_PALM] -> Stopping robot")
        elif gesture == "POINT_FORWARD":
            # Move forward slowly
            twist.linear.x = 0.2
            twist.angular.z = 0.0
            self.cmd_vel_pub.publish(twist)
            self.get_logger().info("Gesture [POINT_FORWARD] -> Driving forward")
        elif gesture == "VICTORY_DANCE":
            # Spin in place
            twist.linear.x = 0.0
            twist.angular.z = 1.0
            self.cmd_vel_pub.publish(twist)
            self.get_logger().info("Gesture [VICTORY_DANCE] -> Spinning in place")

def main(args=None):
    rclpy.init(args=args)
    node = GestureDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
