import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Hardware Communication Bridge
        Node(
            package='robot_bridge',
            executable='serial_bridge',
            name='serial_bridge_node',
            output='screen',
            parameters=[
                {'port': '/dev/ttyRobotMotion'},
                {'baudrate': 115200},
                {'heartbeat_interval': 1.0}
            ]
        ),
        
        # 2. Vision Perception (Face Tracking & Gesture Recognition)
        Node(
            package='robot_perception',
            executable='face_tracker',
            name='face_tracker_node',
            output='screen',
            parameters=[
                {'camera_topic': '/camera/image_raw'},
                {'enable_cv_preview': False},
                {'pan_p_gain': 0.05},
                {'tilt_p_gain': 0.05}
            ]
        ),
        Node(
            package='robot_perception',
            executable='gesture_detector',
            name='gesture_detector_node',
            output='screen',
            parameters=[
                {'camera_topic': '/camera/image_raw'}
            ]
        ),
        
        # 3. High-Level Brain (Ollama LLM Interface & Behavior Trees)
        Node(
            package='robot_brain',
            executable='llm_agent',
            name='llm_agent_node',
            output='screen',
            parameters=[
                {'ollama_url': 'http://localhost:11434/api/generate'},
                {'model_name': 'llama3:8b'}
            ]
        ),
        Node(
            package='robot_brain',
            executable='behavior_tree',
            name='behavior_tree_node',
            output='screen'
        ),
        
        # 4. System Diagnostics & Health Monitor
        Node(
            package='robot_diagnostics',
            executable='health_monitor',
            name='health_monitor_node',
            output='screen'
        )
    ])
