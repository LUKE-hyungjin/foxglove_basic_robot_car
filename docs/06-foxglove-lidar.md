# 6. Debug the lidar in Foxglove

In this step, you connect Foxglove to the simulation and use the prepared layout to check that the lidar scan lines up with the arena walls.

The simulation must be running. If it isn't, start it first with `docker compose up`.

## Connect Foxglove

1. Open Foxglove and click **Open connection**.
2. Choose **Foxglove WebSocket**.
3. Enter `ws://localhost:8765` and click **Open**.

`foxglove_bridge` listens on port 8765 in the container, and `compose.yaml` opens that port on your computer.

If the connection fails, test the bridge from a terminal on your computer. This script connects the same way Foxglove does and prints the topics the bridge offers.

```bash
python3 scripts/check_bridge.py
```

```text
connected to ws://localhost:8765 (subprotocol foxglove.sdk.v1)
...
15 advertised topics:
...
PASS
```

While Foxglove is connected, the count is higher. Foxglove's 3D panel adds its own topics, such as `/clicked_point`.

## Import the layout

1. Open the layout menu at the top right.
2. Choose **Import from file...**.
3. Choose `foxglove/robot_car_debug.json` in the repository.

After the import, you see this screen:

![The robot_car_debug layout](images/foxglove-debug.png)

The layout has 6 panels:

| Panel | What it shows |
| --- | --- |
| 3D | Robot model, lidar points, arena, odometry |
| Plot: wheel speed | Measured and expected speed of each wheel |
| Plot: wheel error | Measured speed − expected speed |
| Plot: odom vs truth | x and y of `/odom` and `/ground_truth/odom` |
| Teleop | Sends `/cmd_vel` with arrow buttons |
| Raw Messages | The raw `/scan` message |

## Look at the lidar in the 3D panel

The 3D panel shows these on top of each other:

- The semi-transparent orange arena. It is `arena.stl`, published on `/map` by the `map_marker` node.
- The robot from Fusion. Foxglove draws it from `/robot_description`.
- The lidar points, from the `/scan` topic.

> [!IMPORTANT]
> The layout sets the 3D panel's **Scene > Mesh up axis** to **Z-up**. When an STL file carries no orientation, Foxglove assumes by default that Y points up and rotates the mesh. The STL files from Fusion and Blender have Z pointing up, which is the ROS convention (REP-103). With **Y-up**, the arena lies on its side by 90°, and the wheel meshes spin on their sides, so the wheel axes look wrong. Foxglove applies this setting only after a reload.

When the lidar points sit exactly on the inner faces of the arena walls, the lidar, the TF tree, and the map all agree. If the points float off the walls or are rotated, suspect these:

- If all the points are shifted parallel to the walls, the robot position is wrong. Check the odometry in step 7.
- If all the points are rotated, the robot heading (yaw) is wrong.
- If the points continue past the walls, the map and the Gazebo world use different STL files.

> [!NOTE]
> If a mesh doesn't appear, Foxglove could not get the STL at its `package://` path. `foxglove_bridge` sends these files over the WebSocket. Check that the `scripts/check_bridge.py` output has `fetchAsset ... bytes` lines.

## Read ranges in Raw Messages

In the Raw Messages panel, expand the `/scan` message.

| Field | Value | Meaning |
| --- | --- | --- |
| `header.frame_id` | `lidar_1` | Lidar link frame |
| `angle_min` | -3.1416 | Angle of the first beam (straight back) |
| `angle_increment` | 0.01745 | 1° between beams |
| `ranges` | 360 values | Distance of each beam (m) |

The angle of beam `i` is `angle_min + i × angle_increment`. Straight ahead (0°) is `ranges[180]`. While the robot is at its start position, check that this value equals 1.249 m, the distance to the box placed straight ahead in step 4.

## Change it yourself

Double the lidar resolution. In `robot_car_sim/config/robot.yaml`, change `samples`:

```yaml
lidar:
  samples: 720
```

Restart the simulation:

```bash
docker compose down
docker compose up
```

`ranges` now has 720 values, 0.5° apart. Straight ahead is now `ranges[360]`, and it still reads 1.249 m. The points in the 3D panel are twice as dense. When you're done, set `samples` back to 360.

Next: [Debug the wheels in Foxglove](07-foxglove-wheels.md)
