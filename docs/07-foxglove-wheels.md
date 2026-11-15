# 7. Debug the wheels in Foxglove

In this step, you drive the robot with the Teleop panel and check three things: whether the wheels turn as commanded, whether wheel odometry follows the true position, and what goes wrong when the wheel radius is measured wrong.

As in step 6, Foxglove must be connected with the `robot_car_debug.json` layout open.

## Topics for wheel debugging

| Topic | Published by | Content |
| --- | --- | --- |
| `/cmd_vel` | Teleop panel | Target linear speed (`linear.x`) and angular speed (`angular.z`) |
| `/joint_states` | Gazebo JointStatePublisher | Actual wheel angles and angular speeds (rad/s) |
| `/wheel_debug/expected` | `wheel_debug` node | Wheel angular speeds computed from `/cmd_vel` |
| `/wheel_debug/error` | `wheel_debug` node | Measured − expected |
| `/odom` | Gazebo DiffDrive | Position computed from wheel rotation |
| `/ground_truth/odom` | Gazebo OdometryPublisher | True position known to the simulator |

`wheel_debug` computes the expected speeds with the differential-drive formula. `v` is the linear speed, `ω` the angular speed, `L` the wheel separation, and `r` the wheel radius.

```text
left wheel  = (v − ω × L / 2) / r
right wheel = (v + ω × L / 2) / r
```

`L` and `r` come from `robot_car_sim/config/robot.yaml`. The DiffDrive plugin reads the same file.

## Drive the robot

While you hold the up button in the Teleop panel, the robot drives forward at 0.2 m/s. The left and right buttons turn it at 0.8 rad/s.

When you release a button, the robot stops within 0.5 seconds. The Teleop panel sends commands only while a button is held, and Gazebo's DiffDrive keeps the last command forever. So the `cmd_vel_timeout` node sends one stop command when `/cmd_vel` is quiet for 0.5 seconds.

If you turn **Stop on release** to **On** in the Teleop panel settings, the panel itself sends a stop command when you release a button. The layout leaves this setting at its default, **Off**. `cmd_vel_timeout` also stops the robot when the Foxglove connection drops.

## Read the wheel speed plot

Hold the up button and watch the **wheel speed** plot.

- The measured and expected speeds of both wheels overlap near 4.0 rad/s, because 0.2 m/s ÷ 0.05 m = 4.0 rad/s.
- When you press a turn button, the two wheels get opposite signs: 0.8 rad/s × 0.225 m ÷ 2 ÷ 0.05 m = 1.8 rad/s.

The **wheel error** plot stays close to 0. The short spikes right after you press or release a button are the difference while the wheels accelerate.

> [!NOTE]
> The plots pick each wheel by position, as in `/joint_states.velocity[0]` (left) and `velocity[1]` (right). This order is the order of the `name` array in `/joint_states`. To check the order, open `/joint_states` in a Raw Messages panel.

## Compare odometry with the true position

The **odom vs truth** plot draws x and y of `/odom` and `/ground_truth/odom` together. As you drive around, the two lines nearly overlap. The more the robot turns, the further they drift apart, because the wheels slip slightly on the floor. Turning at 0.2 m/s and 0.5 rad/s for 4 seconds, odometry reports 114.6°, while the robot really turns 117.5°.

You also see the difference in the 3D panel. The robot model is drawn at the position `/odom` computes, while the arena is drawn at its true coordinates. As odometry drifts, the lidar points shift off the walls by the same amount.

## Put in a wrong wheel radius

On a real robot, the most common odometry error is a wrongly measured wheel radius. Make that error on purpose.

In `robot_car_sim/config/robot.yaml`, make the radius 10% too large:

```yaml
wheel:
  radius: 0.055
```

Restart the simulation, enter the container, and command 1 m straight:

```bash
docker compose down
docker compose up -d
docker compose exec sim bash
python3 /ws/scripts/check_sim.py drive 0.2 0 5
```

```text
             wheel  measured  expected    error  (rad/s, mean of 4447 samples)
  left_wheel_joint     3.633     3.636   -0.003
 right_wheel_joint     3.633     3.636   -0.003
             /odom: start x=+0.000 y=-0.000  end x=+1.000 y=-0.000 yaw=-0.0 deg  moved 1.000 m, turned -0.0 deg
/ground_truth/odom: start x=+0.000 y=-0.000  end x=+0.910 y=-0.000 yaw=-0.0 deg  moved 0.910 m, turned -0.0 deg
```

Read the result:

- The wheel error is -0.003 rad/s, nearly 0. DiffDrive and `wheel_debug` use the same wrong radius, so the wheels turned "as commanded".
- `/odom` reports 1.000 m, but the robot moved only 0.910 m, because 0.05 ÷ 0.055 ≈ 0.909.

The wheel error plot alone can't find this problem. Only a comparison with the true position shows it. On a real robot, a tape-measured distance or the distance to a wall seen by the lidar plays the role of the true position. In the Foxglove 3D panel, the lidar points land behind the wall ahead. The robot model is drawn at the 1.000 m that `/odom` reports, but the lidar measures the wall from the true position at 0.910 m.

When you're done, set the radius back to 0.05. The original value was measured from the Fusion meshes, so you can also run the import script from step 3 again:

```bash
python3 tools/import_fusion_urdf.py fusion/export/basic_description
```

Next: [Troubleshooting](08-troubleshooting.md)
