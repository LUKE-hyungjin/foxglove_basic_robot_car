"""Build the arena (walls + obstacles) and export it as one STL for Gazebo.

Run from the repo root:
    blender -b --factory-startup -P blender/make_map.py

Units are meters, Z is up. The floor is not here: the Gazebo world adds a
ground plane. The robot spawns at the origin facing +X, so keep that area clear.
"""
import math
import os

import bpy

ARENA_SIZE = 6.0        # inner width/length of the square arena
WALL_HEIGHT = 0.4
WALL_THICKNESS = 0.1

# (name, center x, center y, size x, size y, yaw degrees)
BOXES = [
    ("box_ahead", 1.5, 0.0, 0.4, 0.6, 0),       # front face at x = 1.3
    ("box_left", -1.2, 1.6, 0.6, 0.6, 30),
    ("box_corner", 2.0, 2.0, 0.5, 0.5, 0),
    ("l_wall_long", -2.0, -1.25, 0.1, 1.6, 0),  # L-wall: long leg along Y
    ("l_wall_short", -1.4, -2.0, 1.3, 0.1, 0),  # L-wall: short leg along X
]

# (name, center x, center y, radius)
CYLINDERS = [
    ("pillar", 0.8, -1.8, 0.3),
]

OUTPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "robot_car_sim", "models", "arena", "meshes", "arena.stl",
)


def add_box(name, x, y, size_x, size_y, yaw_deg):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, WALL_HEIGHT / 2))
    box = bpy.context.active_object
    box.name = name
    box.scale = (size_x, size_y, WALL_HEIGHT)
    box.rotation_euler = (0, 0, math.radians(yaw_deg))


def add_cylinder(name, x, y, radius):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48, radius=radius, depth=WALL_HEIGHT, location=(x, y, WALL_HEIGHT / 2)
    )
    bpy.context.active_object.name = name


def add_outer_walls():
    half = ARENA_SIZE / 2 + WALL_THICKNESS / 2   # wall center, so the inner face sits at +-3 m
    length = ARENA_SIZE + 2 * WALL_THICKNESS     # long enough to close the corners
    add_box("wall_east", half, 0, WALL_THICKNESS, length, 0)
    add_box("wall_west", -half, 0, WALL_THICKNESS, length, 0)
    add_box("wall_north", 0, half, length, WALL_THICKNESS, 0)
    add_box("wall_south", 0, -half, length, WALL_THICKNESS, 0)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    add_outer_walls()
    for box in BOXES:
        add_box(*box)
    for cylinder in CYLINDERS:
        add_cylinder(*cylinder)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    # forward_axis/up_axis match Blender's own axes, so nothing gets rotated.
    bpy.ops.wm.stl_export(
        filepath=os.path.abspath(OUTPUT),
        ascii_format=False,
        apply_modifiers=True,
        global_scale=1.0,
        forward_axis="Y",
        up_axis="Z",
    )
    print(f"Wrote {os.path.abspath(OUTPUT)}")


main()
