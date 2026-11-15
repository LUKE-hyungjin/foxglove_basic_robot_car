# 8. Troubleshooting

This page lists each symptom with its cause and its fix.

## Docker and the simulation

### `failed to connect to the docker API`

Docker Desktop is not running. Start Docker Desktop and wait until `docker info` prints a server version.

### `Bind for 0.0.0.0:8765 failed: port is already allocated`

Another program or an earlier simulation uses port 8765. Find the container that holds the port:

```bash
docker ps --format '{{.Names}}\t{{.Ports}}'
```

If a simulation from this repository is still running, stop it with `docker compose down`.

### `/scan` is slower than 10 Hz

The lidar renders on the CPU, so when your computer is busy, the whole simulator runs slower than real time. The robot also moves slower than the Teleop command.

First, check for containers that use a lot of CPU:

```bash
docker stats --no-stream --format '{{.Name}}\t{{.CPUPerc}}'
```

While another Gazebo simulation container used 435% CPU, this simulation's real-time factor dropped to about 0.5. When that container stopped, the factor returned to 0.96~0.99, with Foxglove still connected. Stop the other simulation or give Docker Desktop more CPUs.

You can read the real-time factor inside the container. It is an instantaneous value and jumps a lot, from 0.02 up to 5.58 during one measurement, so read it several times before you judge.

```bash
gz topic -e -t /world/arena/stats -n 1 | grep real_time_factor
```

### The robot doesn't appear in Gazebo

Look for `Entity creation successful` in the `docker compose up` log. If it's missing, `robot_state_publisher` could not build the URDF. Run xacro yourself inside a container to see the error:

```bash
docker compose run --rm sim bash
xacro /ws/src/robot_car_sim/urdf/robot_car.urdf.xacro > /tmp/robot.urdf
```

## Foxglove

### Connected, but the 3D panel shows no robot or map

Foxglove gets the STL files at `package://robot_car_sim/...` paths from `foxglove_bridge`. Run the check script on your computer:

```bash
python3 scripts/check_bridge.py
```

If the output has two `fetchAsset ... bytes` lines, the bridge works. If the meshes still don't appear, check in the 3D panel settings that the `/map` topic and the robot model layer are turned on.

### The arena lies on its side by 90° and the wheels spin strangely

The 3D panel reads the STL meshes as Y-up. The robot and the map inside Gazebo are fine. In the 3D panel settings, set **Scene > Mesh up axis** to **Z-up** and reload Foxglove (Cmd+R). The `foxglove/robot_car_debug.json` layout already sets this to Z-up.

### The robot doesn't move when you press a Teleop button

Check that the Teleop panel's topic is `/cmd_vel`. Then check inside the container that commands arrive:

```bash
docker compose exec sim bash
ros2 topic echo /cmd_vel
```

If no messages appear when you press a button, the problem is the Foxglove connection.

## Fusion 360 export

### `No module named 'distutils'`

You have an older version of `fusion360_urdf_script`. Fusion now uses Python 3.12 or later, which no longer has `distutils`. Get the latest `main` and copy the `URDF` folder again.

### `cannot unpack non-iterable NoneType object`

Older versions of `fusion360_urdf_script` looked up colors only by the English property name `Color`. Fusion with a Korean or other non-English UI raises this error. Get the latest `main`.

### `There is no base_link. Please set base_link and run again.`

The chassis component is not named exactly `base_link`. Rename it in the browser tree.

### `old_component` appears in the design after the export

The script copied components to export the STL files. Don't save the design. Undo the changes, or close the design without saving.

## Robot behavior

### The robot turns in place instead of driving forward

The right wheel joint axis points the opposite way from the left one. Check whether you use the raw URDF without running `tools/import_fusion_urdf.py`. See step 3.

### `/odom` moves, but the robot stays in place

The wheels are slipping. This happens when the skids carry part of the weight at the same height as the wheels. Check that step 3's skid fix is applied: in `robot_car_sim/urdf/basic_robot_car.urdf`, the `support_1` collision shapes must be spheres (`sphere`).
