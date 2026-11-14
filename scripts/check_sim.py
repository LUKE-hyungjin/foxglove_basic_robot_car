"""Check the running simulation from inside the container.

    python3 /ws/scripts/check_sim.py scan
        Compare every /scan beam with a ray cast against arena.stl from the
        robot's true pose (/ground_truth/odom).
    python3 /ws/scripts/check_sim.py drive 0.2 0.5 4
        Send /cmd_vel (0.2 m/s, 0.5 rad/s) for 4 s of sim time, then compare
        measured wheel speeds with /wheel_debug/expected, and /odom with
        /ground_truth/odom.
Exits non-zero when a check fails.
"""
import math
import struct
import sys
from pathlib import Path

import numpy as np
import rclpy
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState, LaserScan
from tf2_ros import Buffer, TransformListener

WHEELS = ["left_wheel_joint", "right_wheel_joint"]
# The arena is made of vertical walls from z=0 to 0.4 m, so any height in between
# gives the same 2D ranges.
RAYCAST_HEIGHT = 0.2


class Watcher(Node):
    """Keeps the latest message of every topic the checks read."""

    def __init__(self):
        super().__init__("check_sim", parameter_overrides=[Parameter("use_sim_time", value=True)])
        self.latest = {}
        for topic, msg_type in [
            ("/scan", LaserScan), ("/odom", Odometry), ("/ground_truth/odom", Odometry),
            ("/joint_states", JointState), ("/wheel_debug/expected", JointState),
        ]:
            self.create_subscription(msg_type, topic, self.keeper(topic), qos_profile_sensor_data)
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def keeper(self, topic):
        def keep(msg):
            self.latest[topic] = msg
        return keep

    def wait_for(self, topics, timeout=20.0):
        for _ in range(int(timeout * 20)):
            if all(t in self.latest for t in topics):
                return
            rclpy.spin_once(self, timeout_sec=0.05)
        sys.exit(f"no messages on {[t for t in topics if t not in self.latest]}")

    def spin_sim_seconds(self, seconds, every_step=None):
        start = self.get_clock().now()
        while (self.get_clock().now() - start).nanoseconds < seconds * 1e9:
            rclpy.spin_once(self, timeout_sec=0.05)
            if every_step:
                every_step()

    def send(self, linear, angular):
        msg = Twist()
        msg.linear.x, msg.angular.z = float(linear), float(angular)
        self.cmd_pub.publish(msg)


def pose_2d(odom):
    p, q = odom.pose.pose.position, odom.pose.pose.orientation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    return np.array([p.x, p.y, yaw])


def load_triangles(path):
    data = Path(path).read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    rows = [struct.unpack_from("<12f", data, 84 + 50 * i)[3:] for i in range(count)]
    return np.array(rows, dtype=float).reshape(count, 3, 3)


def raycast(origin, directions, triangles):
    """Distance along each direction to the nearest triangle (Moller-Trumbore), inf if none."""
    v0, e1, e2 = triangles[:, 0], triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    p = np.cross(directions[:, None, :], e2[None])
    det = np.einsum("mk,nmk->nm", e1, p)
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = 1.0 / det
        s = origin - v0
        u = np.einsum("mk,nmk->nm", s, p) * inv
        q = np.cross(s, e1)
        v = np.einsum("nk,mk->nm", directions, q) * inv
        t = np.einsum("mk,mk->m", e2, q)[None] * inv
        hit = (np.abs(det) > 1e-12) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
    return np.where(hit, t, np.inf).min(axis=1)


def check_scan(node):
    node.send(0, 0)
    node.spin_sim_seconds(1.0)
    node.latest.pop("/scan", None)
    node.wait_for(["/scan", "/ground_truth/odom"])
    scan, robot = node.latest["/scan"], pose_2d(node.latest["/ground_truth/odom"])
    while not node.tf_buffer.can_transform("base_link", scan.header.frame_id, rclpy.time.Time()):
        rclpy.spin_once(node, timeout_sec=0.05)
    lidar = node.tf_buffer.lookup_transform("base_link", scan.header.frame_id, rclpy.time.Time())
    lx, ly = lidar.transform.translation.x, lidar.transform.translation.y

    x, y, yaw = robot
    origin = np.array([x + lx * math.cos(yaw) - ly * math.sin(yaw),
                       y + lx * math.sin(yaw) + ly * math.cos(yaw), RAYCAST_HEIGHT])
    angles = scan.angle_min + scan.angle_increment * np.arange(len(scan.ranges))
    directions = np.stack([np.cos(angles + yaw), np.sin(angles + yaw), np.zeros_like(angles)], axis=1)
    mesh = Path(get_package_share_directory("robot_car_sim")) / "models/arena/meshes/arena.stl"
    expected = raycast(origin, directions, load_triangles(mesh))
    expected[expected > scan.range_max] = np.inf
    measured = np.array(scan.ranges)

    print(f"robot (ground truth): x={x:.3f} y={y:.3f} yaw={math.degrees(yaw):.1f} deg; "
          f"scan origin in world: x={origin[0]:.3f} y={origin[1]:.3f}; frame_id={scan.header.frame_id}")
    print(f"{'beam':>12} {'scan [m]':>9} {'mesh [m]':>9} {'diff [m]':>9}")
    for label, degrees in [("front 0", 0), ("left 90", 90), ("back 180", -180), ("right -90", -90)]:
        i = int(round((math.radians(degrees) - scan.angle_min) / scan.angle_increment))
        print(f"{label:>12} {measured[i]:9.3f} {expected[i]:9.3f} {measured[i] - expected[i]:+9.3f}")

    both = np.isfinite(measured) & np.isfinite(expected)
    errors = np.abs(measured[both] - expected[both])
    mismatched_inf = int((np.isfinite(measured) != np.isfinite(expected)).sum())
    worst = int(np.nanargmax(np.where(both, np.abs(measured - expected), np.nan)))
    print(f"worst beam {math.degrees(angles[worst]):+.0f} deg: scan {measured[worst]:.3f} m, mesh {expected[worst]:.3f} m")
    print(f"all beams: {both.sum()}/{len(measured)} compared, |diff| median={np.median(errors):.4f} m, "
          f"p95={np.percentile(errors, 95):.4f} m, max={errors.max():.4f} m, "
          f"hit/no-hit disagreements={mismatched_inf}")
    return np.median(errors) < 0.02 and np.percentile(errors, 95) < 0.05 and mismatched_inf <= 3


def check_drive(node, linear, angular, seconds):
    node.wait_for(["/odom", "/ground_truth/odom", "/joint_states"])
    node.send(0, 0)
    node.spin_sim_seconds(1.0)
    odom_start, truth_start = pose_2d(node.latest["/odom"]), pose_2d(node.latest["/ground_truth/odom"])

    samples = []

    def record():
        node.send(linear, angular)
        measured, expected = node.latest.get("/joint_states"), node.latest.get("/wheel_debug/expected")
        if measured and expected and expected.velocity[0] != 0:
            by_name = dict(zip(measured.name, measured.velocity))
            samples.append([by_name[w] for w in WHEELS] + list(expected.velocity))

    node.spin_sim_seconds(1.0, record)  # let the wheels spin up
    samples.clear()
    node.spin_sim_seconds(seconds - 1.0, record)
    node.send(0, 0)
    node.spin_sim_seconds(0.5)
    odom_end, truth_end = pose_2d(node.latest["/odom"]), pose_2d(node.latest["/ground_truth/odom"])

    s = np.array(samples)
    print(f"cmd_vel linear.x={linear} m/s angular.z={angular} rad/s for {seconds} s sim time")
    print(f"{'wheel':>18} {'measured':>9} {'expected':>9} {'error':>8}  (rad/s, mean of {len(s)} samples)")
    for i, wheel in enumerate(WHEELS):
        m, e = s[:, i].mean(), s[:, i + 2].mean()
        print(f"{wheel:>18} {m:9.3f} {e:9.3f} {m - e:+8.3f}")

    def describe(name, start, end):
        d = end - start
        d[2] = math.atan2(math.sin(d[2]), math.cos(d[2]))
        print(f"{name:>18}: start x={start[0]:+.3f} y={start[1]:+.3f}  end x={end[0]:+.3f} y={end[1]:+.3f} "
              f"yaw={math.degrees(end[2]):+.1f} deg  moved {math.hypot(d[0], d[1]):.3f} m, "
              f"turned {math.degrees(d[2]):+.1f} deg")
    describe("/odom", odom_start, odom_end)
    describe("/ground_truth/odom", truth_start, truth_end)

    wheel_error = np.abs(s[:, :2] - s[:, 2:]).mean()
    moved = math.hypot(*(truth_end - truth_start)[:2])
    return wheel_error < 0.1 * np.abs(s[:, 2:]).mean() + 0.05 and moved > 0.5 * abs(linear) * seconds


def main():
    rclpy.init()
    node = Watcher()
    if sys.argv[1:2] == ["scan"]:
        ok = check_scan(node)
    elif sys.argv[1:2] == ["drive"] and len(sys.argv) == 5:
        ok = check_drive(node, *map(float, sys.argv[2:5]))
    else:
        sys.exit(__doc__)
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
