#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import urllib.request
import json
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from robot_interfaces.msg import RobotStatus

class LlmAgentNode(Node):
    def __init__(self):
        super().__init__('llm_agent_node')
        
        # Declare parameters
        self.declare_parameter('ollama_url', 'http://localhost:11434/api/generate')
        self.declare_parameter('model_name', 'llama3:8b')
        self.declare_parameter('system_prompt', (
            "You are the cognitive brain of the Omni-Morph Robot, a bimodal transformer humanoid. "
            "You can control the robot by outputting special tags in your response. "
            "To move the robot forward, include [CMD:FORWARD]. To stop, include [CMD:STOP]. "
            "To trigger transformation between humanoid and car, include [CMD:TRANSFORM]. "
            "Keep verbal answers concise, friendly, and helpful."
        ))
        
        self.ollama_url = self.get_parameter('ollama_url').value
        self.model_name = self.get_parameter('model_name').value
        self.system_prompt = self.get_parameter('system_prompt').value
        
        # Publishers
        self.speak_pub = self.create_publisher(String, '/speech/speak', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.transform_pub = self.create_publisher(String, '/cmd_transform', 10)
        
        # Subscriber for user speech (input from STT node)
        self.create_subscription(String, '/voice/user_speech', self.user_speech_callback, 10)
        
        # Subscriber for robot state
        self.create_subscription(RobotStatus, '/robot/status', self.status_callback, 10)
        self.current_mode = "HUMANOID"
        
        self.get_logger().info("LLM Agent Node initialized. Connecting to Ollama at " + self.ollama_url)

    def status_callback(self, msg: RobotStatus):
        if msg.mode == RobotStatus.MODE_HUMANOID:
            self.current_mode = "HUMANOID"
        elif msg.mode == RobotStatus.MODE_CAR:
            self.current_mode = "CAR"
        elif msg.mode == RobotStatus.MODE_TRANSFORMING:
            self.current_mode = "TRANSFORMING"

    def user_speech_callback(self, msg: String):
        user_text = msg.data
        self.get_logger().info(f"Received user voice query: '{user_text}'")
        
        # Call local Ollama LLM
        response_text = self.query_local_llm(user_text)
        
        if response_text:
            self.get_logger().info(f"LLM Response: {response_text}")
            
            # Extract control actions from special tokens
            self.parse_and_execute_actions(response_text)
            
            # Strip tags for verbalization
            speech_output = self.strip_tokens(response_text)
            
            # Publish to text-to-speech engine
            speak_msg = String()
            speak_msg.data = speech_output
            self.speak_pub.publish(speak_msg)

    def query_local_llm(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": f"System: {self.system_prompt}\nRobot Current Mode: {self.current_mode}\nUser: {prompt}\nResponse:",
            "stream": False
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.ollama_url, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_payload = json.loads(response.read().decode('utf-8'))
                return res_payload.get('response', '')
        except Exception as e:
            self.get_logger().error(f"Failed to query local LLM at {self.ollama_url}: {e}")
            return "System alert: local cognitive engine offline."

    def parse_and_execute_actions(self, text: str):
        # Scan for action tags
        if "[CMD:FORWARD]" in text:
            twist = Twist()
            twist.linear.x = 0.3
            self.cmd_vel_pub.publish(twist)
            self.get_logger().info("Action: Drive Forward triggered by LLM.")
        elif "[CMD:STOP]" in text:
            twist = Twist()
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.cmd_vel_pub.publish(twist)
            self.get_logger().info("Action: STOP triggered by LLM.")
            
        if "[CMD:TRANSFORM]" in text:
            trans_msg = String()
            trans_msg.data = "TRANSFORM"
            self.transform_pub.publish(trans_msg)
            self.get_logger().info("Action: Mechanical transformation triggered by LLM.")

    def strip_tokens(self, text: str) -> str:
        # Remove tags from speech synthesis text
        clean = text.replace("[CMD:FORWARD]", "")
        clean = clean.replace("[CMD:STOP]", "")
        clean = clean.replace("[CMD:TRANSFORM]", "")
        return clean.strip()

def main(args=None):
    rclpy.init(args=args)
    node = LlmAgentNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
