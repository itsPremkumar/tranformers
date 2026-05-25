from setuptools import setup

package_name = 'robot_perception'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'opencv-python', 'numpy'],
    zip_safe=True,
    maintainer='PREM KUMAR',
    maintainer_email='premkumar@example.com',
    description='Computer vision perception nodes for tracking and hand gestures.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'face_tracker = robot_perception.face_tracker_node:main',
            'gesture_detector = robot_perception.gesture_detector_node:main',
        ],
    },
)
