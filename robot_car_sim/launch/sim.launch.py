"""Start the whole simulation: Gazebo, the robot, the ROS bridge, debug nodes, Foxglove.

    ros2 launch robot_car_sim sim.launch.py
"""
import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, ExecuteProcess
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory("robot_car_sim")
    with open(os.path.join(share, "config", "robot.yaml")) as f:
        robot = yaml.safe_load(f)

    robot_description = ParameterValue(
        Command(["xacro ", os.path.join(share, "urdf", "robot_car.urdf.xacro")]),
        value_type=str,
    )
    sim_time = {"use_sim_time": True}

    return LaunchDescription([
        # Gazebo finds model://arena in <share>/models and package://robot_car_sim in <share>/..
        AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", os.path.join(share, "models")),
        AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", os.path.dirname(share)),

        # Server only (-s), start running (-r). --headless-rendering lets the lidar
        # render without a display.
        ExecuteProcess(
            cmd=["gz", "sim", "-s", "-r", "--headless-rendering",
                 os.path.join(share, "worlds", "arena.sdf")],
            output="screen",
        ),

        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}, sim_time],
        ),

        # Spawn the robot from the URDF that robot_state_publisher publishes.
        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=["-topic", "robot_description", "-name", "robot_car", "-z", "0.01"],
            output="screen",
        ),

        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            parameters=[{"config_file": os.path.join(share, "config", "bridge.yaml")}, sim_time],
        ),

        # The robot spawns at the origin, so odom starts exactly on world.
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=["--frame-id", "world", "--child-frame-id", "odom"],
            parameters=[sim_time],
        ),

        Node(
            package="robot_car_sim",
            executable="wheel_debug",
            parameters=[{
                "wheel_radius": robot["wheel"]["radius"],
                "wheel_separation": robot["wheel"]["separation"],
            }, sim_time],
        ),

        Node(package="robot_car_sim", executable="map_marker", parameters=[sim_time]),

        Node(
            package="foxglove_bridge",
            executable="foxglove_bridge",
            parameters=[{"port": 8765, "address": "0.0.0.0"}, sim_time],
        ),
    ])
