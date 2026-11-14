"""Publish the arena mesh as a Marker on /map so Foxglove draws it under the lidar points."""
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from visualization_msgs.msg import Marker

ARENA_MESH = "package://robot_car_sim/models/arena/meshes/arena.stl"


class MapMarker(Node):
    def __init__(self):
        super().__init__("map_marker")
        # transient_local: a viewer that connects later still gets the one message.
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        publisher = self.create_publisher(Marker, "/map", latched)

        marker = Marker()
        marker.header.frame_id = "world"
        marker.ns = "arena"
        marker.type = Marker.MESH_RESOURCE
        marker.action = Marker.ADD
        marker.mesh_resource = ARENA_MESH
        marker.frame_locked = True
        marker.pose.orientation.w = 1.0
        marker.scale.x = marker.scale.y = marker.scale.z = 1.0
        marker.color.r, marker.color.g, marker.color.b, marker.color.a = 0.9, 0.6, 0.3, 0.6
        publisher.publish(marker)


def main():
    rclpy.init()
    rclpy.spin(MapMarker())


if __name__ == "__main__":
    main()
