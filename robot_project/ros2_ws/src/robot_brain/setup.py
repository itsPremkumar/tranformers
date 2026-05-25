from setuptools import setup

package_name = 'robot_brain'

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
    description='High-level AI cognitive and behavior tree decision nodes.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'llm_agent = robot_brain.llm_agent_node:main',
            'behavior_tree = robot_brain.behavior_tree_node:main',
        ],
    },
)
