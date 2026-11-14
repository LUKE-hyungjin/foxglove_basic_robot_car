"""Stop the robot when /cmd_vel goes quiet.

Gazebo's DiffDrive keeps the last command forever, and the Foxglove Teleop panel
only publishes while a button is held. If the last command was nonzero and no new
message arrives for `timeout` seconds, publish one zero Twist on /cmd_vel.
"""
import rclpy
from geometry_msgs.msg import Twist
from rclpy.clock import Clock, ClockType
from rclpy.node import Node


def is_zero(cmd):
    values = (cmd.linear.x, cmd.linear.y, cmd.linear.z, cmd.angular.x, cmd.angular.y, cmd.angular.z)
    return not any(values)


class CmdVelTimeout(Node):
    def __init__(self):
        super().__init__("cmd_vel_timeout")
        self.declare_parameter("timeout", 0.5)
        timeout = self.get_parameter("timeout").value
        self.pub = self.create_publisher(Twist, "/cmd_vel", 10)
        # Wall time, not sim time: Foxglove publishes on the browser's wall clock, so
        # a sim-time timeout would fire between commands whenever the simulation runs
        # faster than real time.
        self.timer = self.create_timer(timeout, self.on_timeout, clock=Clock(clock_type=ClockType.STEADY_TIME))
        self.timer.cancel()
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, 10)

    def on_cmd_vel(self, msg):
        if is_zero(msg):
            self.timer.cancel()
        else:
            self.timer.reset()

    def on_timeout(self):
        self.timer.cancel()
        self.get_logger().info("no /cmd_vel for a while, stopping")
        self.pub.publish(Twist())


def main():
    rclpy.init()
    rclpy.spin(CmdVelTimeout())


if __name__ == "__main__":
    main()
