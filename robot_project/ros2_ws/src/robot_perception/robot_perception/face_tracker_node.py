#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import cv2
from std_msgs.msg import Int32
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class FaceTrackerNode(Node):
    def __init__(self):
        super().__init__('face_tracker_node')
        
        # Declare parameters
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('enable_cv_preview', False)
        self.declare_parameter('pan_p_gain', 0.05)
        self.declare_parameter('tilt_p_gain', 0.05)
        
        self.camera_topic = self.get_parameter('camera_topic').value
        self.enable_preview = self.get_parameter('enable_cv_preview').value
        self.pan_p_gain = self.get_parameter('pan_p_gain').value
        self.tilt_p_gain = self.get_parameter('tilt_p_gain').value
        
        # Bridge to convert ROS Image to OpenCV Frame
        self.bridge = CvBridge()
        
        # Face detection model (Haar Cascade)
        # In a real Jetson system, this can be accelerated using a TensorRT DNN model
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Initial head positions
        self.current_pan = 90
        self.current_tilt = 90
        
        # Publishers for pan/tilt angles
        self.pan_pub = self.create_publisher(Int32, '/head/pan', 10)
        self.tilt_pub = self.create_publisher(Int32, '/head/tilt', 10)
        
        # Subscriber to image topic
        self.create_subscription(Image, self.camera_topic, self.image_callback, 10)
        
        self.get_logger().info("Face Tracker Node initialized and listening on " + self.camera_topic)

    def image_callback(self, msg: Image):
        try:
            # Convert ROS Image message to OpenCV image
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return
            
        height, width, _ = frame.shape
        center_x = width // 2
        center_y = height // 2
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) > 0:
            # Sort by size to track the largest (closest) face
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            (x, y, w, h) = faces[0]
            
            # Calculate face center
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            # Calculate offsets from frame center
            offset_x = face_center_x - center_x
            offset_y = face_center_y - center_y
            
            # Calculate pan/tilt updates with proportional gain
            pan_delta = -int(offset_x * self.pan_p_gain)
            tilt_delta = -int(offset_y * self.tilt_p_gain)
            
            # Apply adjustments to current positions
            new_pan = max(0, min(180, self.current_pan + pan_delta))
            new_tilt = max(0, min(180, self.current_tilt + tilt_delta))
            
            # Publish if position changed
            if new_pan != self.current_pan:
                self.current_pan = new_pan
                pan_msg = Int32()
                pan_msg.data = self.current_pan
                self.pan_pub.publish(pan_msg)
                
            if new_tilt != self.current_tilt:
                self.current_tilt = new_tilt
                tilt_msg = Int32()
                tilt_msg.data = self.current_tilt
                self.tilt_pub.publish(tilt_msg)
                
            if self.enable_preview:
                # Draw bounding box and target point
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 0, 255), -1)
                
        if self.enable_preview:
            cv2.imshow("Face Tracking Preview", frame)
            cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = FaceTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
