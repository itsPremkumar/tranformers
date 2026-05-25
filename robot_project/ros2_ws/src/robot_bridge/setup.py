from setuptools import setup

package_name = 'robot_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyserial', 'python-can'],
    zip_safe=True,
    maintainer='PREM KUMAR',
    maintainer_email='premkumar@example.com',
    description='ROS 2 hardware bridge to ESP32 Motion Controller over Serial UART or CAN Bus.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'serial_bridge = robot_bridge.serial_bridge_node:main',
            'can_bridge = robot_bridge.can_bridge_node:main',
        ],
    },
)
