# 4. Build the arena map with Blender

In this step, you build a 6 m × 6 m arena with a Blender script and export it as an STL file. A script builds the map instead of mouse modeling, so changing a number and running it again gives exactly the same map every time.

If you don't have Blender, read this step without running it. The output, `robot_car_sim/models/arena/meshes/arena.stl`, is already in the repository.

## Read the map definition

The top of `blender/make_map.py` defines the map in numbers. Units are meters, and Z points up.

```python
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
```

The robot starts at the origin, facing +X. That is why a box (`box_ahead`) sits 1.3 m straight ahead. In step 6, you check that the lidar reads this distance correctly.

The floor is not part of this map. The Gazebo world (`robot_car_sim/worlds/arena.sdf`) adds its own ground plane.

## Export the map

From the repository root, run Blender without a window:

```bash
blender -b --factory-startup -P blender/make_map.py
```

- `-b` runs without a window.
- `--factory-startup` ignores your Blender settings and starts from the defaults, so everyone gets the same result.
- `-P` runs the script.

The export worked when you see these lines:

```text
Info: File exported successfully
Wrote .../robot_car_sim/models/arena/meshes/arena.stl
```

On macOS, if there is no `blender` command, call the executable inside the app:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P blender/make_map.py
```

## Look at the map in Blender

To see the map, run the script with a window:

```bash
blender --factory-startup -P blender/make_map.py
```

You see 4 walls, 3 boxes, an L-shaped wall, and 1 cylinder.

## Change it yourself

Add a box to `BOXES` and export again. Keep the robot's start area clear (within 0.6 m of the origin).

```python
    ("my_box", 0.0, 1.5, 0.3, 0.3, 45),
```

Restart the simulation, and the new box appears in both Gazebo and Foxglove, because both read the same `arena.stl`.

Next: [Run the Gazebo simulation](05-gazebo-sim.md)
