# 3. Import the URDF into the simulation package

The URDF that Fusion exports does not drive correctly if you put it straight into Gazebo. In this step, you turn the raw export into a simulation URDF with `tools/import_fusion_urdf.py`, and you see why each change is needed.

The raw export (`fusion/export/basic_description/`) stays untouched. When you export from Fusion again, run this script again.

## Run the script

Run it from the repository root. It needs Python 3.9 or later on your computer and no extra packages.

```bash
python3 tools/import_fusion_urdf.py fusion/export/basic_description
```

The script prints each change on its own line:

```text
read    fusion/export/basic_description/basic.urdf
copy    fusion/export/basic_description/meshes/base_link.stl -> robot_car_sim/meshes/base_link.stl
...
path    meshes/base_link.stl -> package://robot_car_sim/meshes/base_link.stl
...
fix     right_wheel_joint axis 0 -1 0 -> 0 1 0
fix     support_1 collision: skid foot sphere r=0.01 at x=0.075 z=-0.014 (1 mm above floor)
fix     support_1 collision: skid foot sphere r=0.01 at x=-0.075 z=-0.014 (1 mm above floor)
write   robot_car_sim/urdf/basic_robot_car.urdf
yaml    wheel.radius = 0.05
yaml    wheel.separation = 0.225
yaml    lidar.z_offset = 0.0125
```

Running it twice gives the same result.

## What the script changes

### Mesh paths become `package://` paths

The raw URDF uses relative paths such as `meshes/base_link.stl`. In ROS, the URDF travels as a string on the `/robot_description` topic, not as a file, so a relative path has no folder to be relative to. With `package://robot_car_sim/meshes/base_link.stl`, both Gazebo and Foxglove find the mesh in the package.

### The right wheel axis points the same way as the left

In the raw export, the left wheel axis is `0 1 0` and the right wheel axis is `0 -1 0`. Fusion sets each axis from the direction in which the joint was created.

To drive forward, Gazebo's DiffDrive plugin gives both wheel joints a speed with the same sign. If the right axis points the other way, the right wheel spins backward and the robot turns in place. The script flips the right axis to `0 1 0`. A wheel is a cylinder, so the flip doesn't change its shape.

### The skids slide on the floor

The two wheels and the two skids of Basic Robot Car all touch the floor at z = 0. On a real robot, the skids sit a little higher or slide. In the simulator, rigid bodies share the weight across all four contacts. The wheels then carry less weight and spin without grip.

The script replaces the skid collision shape with one sphere of 1 cm radius at the tip of each skid, 1 mm above the floor. The skid's visual shape stays the same. Two spheres are also much cheaper to collide than a mesh of 9,496 triangles, so the lidar keeps its 10 Hz rate.

### Measured values go into `robot.yaml`

The script measures the wheel radius, the wheel separation, and the lidar height directly from the STL files and writes them to `robot_car_sim/config/robot.yaml`. The DiffDrive plugin and the wheel debug node both read this one file, so their values can't disagree.

```yaml
wheel:
  radius: 0.05
  separation: 0.225
lidar:
  z_offset: 0.0125
```

## Why the fixes matter, in numbers

Each row drives the robot straight for 1 m (0.2 m/s for 5 seconds) with some fixes left out. In every row, the wheels spun exactly as commanded, at 4.000 rad/s. Only the contact with the floor changed.

| URDF in the simulation | `/odom` moved | Robot really moved |
| --- | --- | --- |
| Raw export | 1.000 m | 0.000 m |
| Wheel axis fixed only | 1.000 m | 0.000 m |
| Wheel axis + skid fix (final) | 0.999 m | 1.001 m |

`/odom` is computed from how far the wheels turned, so it reports 1 m even when the wheels slip. The true position comes from the simulator on `/ground_truth/odom`. In step 7, you compare the two in Foxglove.

## The final robot model

`robot_car_sim/urdf/robot_car.urdf.xacro` is the final robot. It includes the imported URDF as is and adds only what Gazebo needs:

- Friction for the wheels and the skids
- A GPU lidar sensor on the `lidar_1` link
- The DiffDrive plugin. It turns `/cmd_vel` into wheel speeds and publishes `/odom`.
- The JointStatePublisher plugin. It publishes the wheel angles and speeds on `/joint_states`.
- The OdometryPublisher plugin. It publishes the true pose on `/ground_truth/odom`.

Next: [Build the arena map with Blender](04-blender-map.md)
