"""Compare the wheel speeds Gazebo measures with the speeds /cmd_vel asks for.

Publishes:
  /wheel_debug/expected  wheel speeds (rad/s) that /cmd_vel should produce
  /wheel_debug/error     measured - expected, per wheel
"""
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import JointState

WHEEL_JOINTS = ["left_wheel_joint", "right_wheel_joint"]


def expected_wheel_speeds(linear_x, angular_z, wheel_radius, wheel_separation):
    """Differential-drive kinematics: body velocity -> (left, right) wheel rad/s."""
    left = (linear_x - angular_z * wheel_separation / 2) / wheel_radius
    right = (linear_x + angular_z * wheel_separation / 2) / wheel_radius
    return left, right


class WheelDebug(Node):
    def __init__(self):
        super().__init__("wheel_debug")
        # No defaults on purpose: the launch file reads them from config/robot.yaml.
        self.declare_parameter("wheel_radius", Parameter.Type.DOUBLE)
        self.declare_parameter("wheel_separation", Parameter.Type.DOUBLE)
        self.wheel_radius = self.get_parameter("wheel_radius").value
        self.wheel_separation = self.get_parameter("wheel_separation").value
        if self.wheel_radius is None or self.wheel_separation is None:
            raise RuntimeError("set wheel_radius and wheel_separation (see launch/sim.launch.py)")

        self.last_cmd = Twist()
        self.expected_pub = self.create_publisher(JointState, "/wheel_debug/expected", 10)
        self.error_pub = self.create_publisher(JointState, "/wheel_debug/error", 10)
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, 10)
        self.create_subscription(JointState, "/joint_states", self.on_joint_states, 10)

    def on_cmd_vel(self, msg):
        self.last_cmd = msg

    def on_joint_states(self, measured):
        expected_speeds = expected_wheel_speeds(
            self.last_cmd.linear.x, self.last_cmd.angular.z,
            self.wheel_radius, self.wheel_separation,
        )
        measured_speeds = dict(zip(measured.name, measured.velocity))

        expected = JointState(header=measured.header, name=WHEEL_JOINTS)
        expected.velocity = list(expected_speeds)
        error = JointState(header=measured.header, name=WHEEL_JOINTS)
        error.velocity = [
            measured_speeds.get(joint, float("nan")) - speed
            for joint, speed in zip(WHEEL_JOINTS, expected_speeds)
        ]
        self.expected_pub.publish(expected)
        self.error_pub.publish(error)


def main():
    rclpy.init()
    rclpy.spin(WheelDebug())


if __name__ == "__main__":
    main()
