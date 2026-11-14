# 5. Gazebo 시뮬레이션 실행하기

이 단계에서는 명령 하나로 Gazebo, 로봇, ROS 2 브리지, 디버그 노드, Foxglove 브리지를 모두 띄웁니다. 그리고 컨테이너 안에서 토픽이 제대로 나오는지 확인합니다.

## 시뮬레이션 시작하기

저장소 루트에서 실행합니다.

```bash
docker compose up
```

컨테이너가 시작되면 패키지를 빌드하고 `ros2 launch robot_car_sim sim.launch.py`를 실행합니다. 다음 줄들이 보이면 준비가 끝났습니다.

```text
[foxglove_bridge-9] ... [foxglove_bridge]: Server listening on port 8765
[create-3] ... [ros_gz_sim]: Entity creation successful.
[parameter_bridge-4] ... Creating GZ->ROS Bridge: [/scan (gz.msgs.LaserScan) -> /scan (sensor_msgs/msg/LaserScan)] (Lazy 0)
```

- `Server listening on port 8765`는 Foxglove가 접속할 준비가 되었다는 뜻입니다.
- `Entity creation successful`은 로봇이 Gazebo에 나타났다는 뜻입니다.
- `Creating GZ->ROS Bridge`는 Gazebo 토픽이 ROS 2 토픽으로 연결되었다는 뜻입니다.

아래 경고 두 개는 무시해도 됩니다.

- `XML Element[gz_frame_id], child of element[sensor], not defined in SDF`는 라이다 프레임 이름을 지정하는 설정입니다. 경고와 달리 실제로 적용됩니다.
- `KDL does not support a root link with an inertia`는 `robot_state_publisher`의 안내 메시지입니다. TF 계산에는 영향이 없습니다.

Gazebo 화면은 열리지 않습니다. Gazebo를 서버 모드(`gz sim -s`)로만 띄우고, 화면은 Foxglove로 봅니다.

## 실행되는 것

`robot_car_sim/launch/sim.launch.py`가 다음을 실행합니다.

| 프로세스 | 하는 일 |
| --- | --- |
| `gz sim` | `worlds/arena.sdf` 월드를 물리 엔진과 함께 실행 |
| `robot_state_publisher` | xacro로 만든 URDF를 `/robot_description`으로 내보내고, 바퀴 TF 계산 |
| `ros_gz_sim create` | `/robot_description`을 읽어 Gazebo에 로봇 생성 |
| `parameter_bridge` | `config/bridge.yaml`에 적힌 토픽을 Gazebo와 ROS 2 사이에 연결 |
| `static_transform_publisher` | `world` → `odom` 고정 변환 |
| `wheel_debug` | 바퀴 속도 기대값과 오차 계산 |
| `map_marker` | 경기장 메시를 `/map` 마커로 내보내기 |
| `cmd_vel_timeout` | `/cmd_vel`이 0.5초 동안 끊기면 정지 명령 보내기 |
| `foxglove_bridge` | 모든 토픽을 `ws://localhost:8765`로 공개 |

## 컨테이너 안에서 토픽 확인하기

새 터미널을 열고 실행 중인 컨테이너에 들어갑니다.

```bash
docker compose exec sim bash
```

토픽 목록을 봅니다.

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

라이다 주기를 확인합니다. 설정값은 10 Hz입니다. 끝내려면 Ctrl+C를 누르세요.

```bash
ros2 topic hz /scan
```

```text
average rate: 9.993
```

컴퓨터가 다른 일로 바쁘면 9 Hz대로 떨어질 수 있습니다. 시뮬레이터가 실제 시간보다 느리게 돌기 때문입니다.

## 라이다 값이 맵과 맞는지 확인하기

`scripts/check_sim.py scan`은 라이다 빔 360개를 하나씩 `arena.stl`에 직접 광선을 쏴서 구한 거리와 비교합니다.

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

정면 거리 1.25 m는 4단계에서 둔 상자 앞면(x = 1.3 m)에서 라이다 위치(x = 0.05 m)를 뺀 값입니다. 좌우 3.0 m는 경기장 벽까지의 거리입니다.

## 로봇 움직여 보기

`/cmd_vel`로 0.2 m/s 직진 명령을 5초 동안 보내고 결과를 비교합니다.

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

기대 속도 4.000 rad/s는 0.2 m/s를 바퀴 반지름 0.05 m로 나눈 값입니다. 측정 속도는 실행할 때마다 3.997–4.000 rad/s 사이에서 조금씩 다릅니다.

## 전체 점검 한 번에 돌리기

호스트 터미널에서 `scripts/smoke_test.sh`를 실행하면 위 확인과 Foxglove 브리지 접속까지 한 번에 점검합니다. 이 스크립트는 시뮬레이션을 내렸다가 다시 띄웁니다.

```bash
./scripts/smoke_test.sh
```

마지막 줄이 `SMOKE TEST PASSED`이면 모든 점검을 통과한 것입니다.

## 시뮬레이션 끄기

`docker compose up`을 실행한 터미널에서 Ctrl+C를 누르거나, 다른 터미널에서 실행합니다.

```bash
docker compose down
```

다음 단계: [Foxglove로 라이다 디버그하기](06-foxglove-lidar.md)
