from setuptools import setup

package_name = 'robot_motion'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='PREM KUMAR',
    maintainer_email='premkumar@example.com',
    description='Closed-loop balance, yaw assist, and dynamic trajectory motion control.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'balance_control = robot_motion.balance_control_node:main',
        ],
    },
)
