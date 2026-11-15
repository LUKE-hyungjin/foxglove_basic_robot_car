# 5. Run the Gazebo simulation

In this step, one command starts Gazebo, the robot, the ROS 2 bridge, the debug nodes, and the Foxglove bridge. Then you check from inside the container that the topics come out correctly.

## Start the simulation

Run this from the repository root:

```bash
docker compose up
```

The container builds the package and runs `ros2 launch robot_car_sim sim.launch.py`. The simulation is ready when you see these lines:

```text
[foxglove_bridge-9] ... [foxglove_bridge]: Server listening on port 8765
[create-3] ... [ros_gz_sim]: Entity creation successful.
[parameter_bridge-4] ... Creating GZ->ROS Bridge: [/scan (gz.msgs.LaserScan) -> /scan (sensor_msgs/msg/LaserScan)] (Lazy 0)
```

- `Server listening on port 8765` means Foxglove can connect.
- `Entity creation successful` means the robot appeared in Gazebo.
- `Creating GZ->ROS Bridge` means a Gazebo topic is now connected to a ROS 2 topic.

You can ignore these two warnings:

- `XML Element[gz_frame_id], child of element[sensor], not defined in SDF` is about the setting that names the lidar frame. Despite the warning, the setting takes effect.
- `KDL does not support a root link with an inertia` is a notice from `robot_state_publisher`. It doesn't affect the TF calculation.

No Gazebo window opens. Gazebo runs as a server only (`gz sim -s`), and you watch it in Foxglove.

## What runs

`robot_car_sim/launch/sim.launch.py` starts these processes:

| Process | What it does |
| --- | --- |
| `gz sim` | Runs the `worlds/arena.sdf` world with the physics engine |
| `robot_state_publisher` | Publishes the xacro-built URDF on `/robot_description` and computes the wheel TFs |
| `ros_gz_sim create` | Reads `/robot_description` and creates the robot in Gazebo |
| `parameter_bridge` | Connects the topics listed in `config/bridge.yaml` between Gazebo and ROS 2 |
| `static_transform_publisher` | Publishes the fixed `world` → `odom` transform |
| `wheel_debug` | Computes the expected wheel speeds and their error |
| `map_marker` | Publishes the arena mesh as the `/map` marker |
| `cmd_vel_timeout` | Sends a stop command when `/cmd_vel` is quiet for 0.5 seconds |
| `foxglove_bridge` | Serves every topic at `ws://localhost:8765` |

## Check the topics inside the container

Open a new terminal and enter the running container:

```bash
docker compose exec sim bash
```

List the topics:

```bash
ros2 topic list
```

```text
/clock
/cmd_vel
/ground_truth/odom
/joint_states
/map
/odom
/parameter_events
/robot_description
/rosout
/scan
/tf
/tf_static
/wheel_debug/error
/wheel_debug/expected
```

Check the lidar rate. The setting is 10 Hz. Press Ctrl+C to stop.

```bash
ros2 topic hz /scan
```

```text
average rate: 9.993
```

If your computer is busy with other work, the rate can drop into the 9 Hz range, because the simulator then runs slower than real time.

## Check that the lidar matches the map

`scripts/check_sim.py scan` compares each of the 360 lidar beams with a ray cast straight into `arena.stl`.

```bash
python3 /ws/scripts/check_sim.py scan
```

```text
robot (ground truth): x=0.000 y=-0.000 yaw=0.0 deg; scan origin in world: x=0.050 y=0.000; frame_id=lidar_1
        beam  scan [m]  mesh [m]  diff [m]
     front 0     1.249     1.250    -0.001
     left 90     3.000     3.000    +0.000
    back 180     3.052     3.050    +0.002
   right -90     3.000     3.000    +0.000
...
PASS
```

The 1.25 m to the front is the box face placed in step 4 (x = 1.3 m) minus the lidar position (x = 0.05 m). The 3.0 m to the left and right is the distance to the arena walls.

## Drive the robot

Send a 0.2 m/s straight command on `/cmd_vel` for 5 seconds and compare the results:

```bash
python3 /ws/scripts/check_sim.py drive 0.2 0 5
```

```text
cmd_vel linear.x=0.2 m/s angular.z=0.0 rad/s for 5.0 s sim time
             wheel  measured  expected    error  (rad/s, mean of 3999 samples)
  left_wheel_joint     3.997     4.000   -0.003
 right_wheel_joint     3.997     4.000   -0.003
             /odom: start x=+0.000 y=-0.000  end x=+0.999 y=-0.000 yaw=-0.0 deg  moved 0.999 m, turned -0.0 deg
/ground_truth/odom: start x=+0.000 y=-0.000  end x=+1.001 y=+0.000 yaw=+0.0 deg  moved 1.001 m, turned +0.0 deg
PASS
```

The expected 4.000 rad/s is 0.2 m/s divided by the 0.05 m wheel radius. The measured speed varies a little between runs, from 3.997 to 4.000 rad/s.

## Run every check at once

From a terminal on your computer, `scripts/smoke_test.sh` runs the checks above and also connects to the Foxglove bridge. The script stops the simulation and starts it again.

```bash
./scripts/smoke_test.sh
```

Every check passed when the last line is `SMOKE TEST PASSED`.

## Stop the simulation

Press Ctrl+C in the terminal that runs `docker compose up`, or run this in another terminal:

```bash
docker compose down
```

Next: [Debug the lidar in Foxglove](06-foxglove-lidar.md)
