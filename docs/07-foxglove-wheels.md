# 7. Foxglove로 바퀴 디버그하기

이 단계에서는 Teleop 패널로 로봇을 움직이면서 세 가지를 확인합니다. 바퀴가 명령대로 도는지, 바퀴 오도메트리가 실제 위치를 따라가는지, 그리고 바퀴 반지름을 잘못 재면 무엇이 틀어지는지입니다.

6단계처럼 Foxglove가 연결되어 있고 `robot_car_debug.json` 레이아웃이 열려 있어야 합니다.

## 바퀴 디버그에 쓰는 토픽

| 토픽 | 만드는 곳 | 내용 |
| --- | --- | --- |
| `/cmd_vel` | Teleop 패널 | 목표 선속도(`linear.x`)와 각속도(`angular.z`) |
| `/joint_states` | Gazebo JointStatePublisher | 바퀴의 실제 각도와 각속도 (rad/s) |
| `/wheel_debug/expected` | `wheel_debug` 노드 | `/cmd_vel`로 계산한 바퀴 각속도 |
| `/wheel_debug/error` | `wheel_debug` 노드 | 측정 − 기대 |
| `/odom` | Gazebo DiffDrive | 바퀴 회전량으로 계산한 위치 |
| `/ground_truth/odom` | Gazebo OdometryPublisher | 시뮬레이터가 아는 실제 위치 |

`wheel_debug`는 차동 구동 공식으로 기대 속도를 계산합니다. `v`는 선속도, `ω`는 각속도, `L`은 바퀴 간격, `r`은 바퀴 반지름입니다.

```text
왼쪽 바퀴 = (v − ω × L / 2) / r
오른쪽 바퀴 = (v + ω × L / 2) / r
```

`L`과 `r`은 `robot_car_sim/config/robot.yaml`에서 읽습니다. DiffDrive 플러그인도 같은 파일을 씁니다.

## 로봇 움직이기

Teleop 패널의 위쪽 버튼을 누르고 있으면 로봇이 0.2 m/s로 앞으로 갑니다. 왼쪽과 오른쪽 버튼은 0.8 rad/s로 회전합니다.

버튼을 떼면 0.5초 안에 로봇이 멈춥니다. Teleop 패널은 버튼을 누르고 있는 동안에만 명령을 보내고, Gazebo의 DiffDrive는 마지막 명령을 계속 유지합니다. 그래서 `cmd_vel_timeout` 노드가 명령이 0.5초 동안 끊기면 정지 명령을 한 번 보냅니다.

## 바퀴 속도 그래프 읽기

위쪽 버튼을 누르고 있는 동안 **바퀴 속도** 그래프를 봅니다.

- 두 바퀴의 측정값과 기대값이 모두 4.0 rad/s 근처에 겹칩니다. 0.2 m/s ÷ 0.05 m = 4.0 rad/s입니다.
- 회전 버튼을 누르면 두 바퀴의 부호가 반대가 됩니다. 0.8 rad/s × 0.225 m ÷ 2 ÷ 0.05 m = 1.8 rad/s입니다.

**바퀴 오차** 그래프는 거의 0에 붙어 있어야 합니다. 버튼을 누르거나 뗀 직후에 잠깐 튀는 것은 바퀴가 가속하는 동안의 차이입니다.

> [!NOTE]
> 그래프는 `/joint_states.velocity[0]`(왼쪽)과 `velocity[1]`(오른쪽)처럼 순서로 바퀴를 고릅니다. 이 순서는 `/joint_states`의 `name` 배열 순서와 같습니다. Raw Messages 패널에서 `/joint_states`를 열어 순서를 확인할 수 있습니다.

## 오도메트리와 실제 위치 비교하기

**odom vs 실제** 그래프는 `/odom`과 `/ground_truth/odom`의 x, y를 함께 그립니다. 로봇을 이리저리 움직여 보면 두 선이 거의 겹칩니다. 회전을 많이 할수록 조금씩 벌어지는데, 바퀴가 바닥에서 미세하게 미끄러지기 때문입니다. 0.2 m/s, 0.5 rad/s로 4초 동안 돌면 오도메트리는 114.6° 돌았다고 하고, 실제로는 117.5° 돕니다.

3D 패널에서도 차이가 보입니다. 로봇 모델은 `/odom`이 계산한 위치에 그려지고, 경기장은 실제 좌표에 그려집니다. 오도메트리가 틀어진 만큼 라이다 점이 벽에서 밀려납니다.

## 바퀴 반지름을 틀리게 넣어 보기

실제 로봇에서 가장 흔한 오도메트리 오류는 바퀴 반지름을 잘못 잰 것입니다. 일부러 만들어 봅니다.

`robot_car_sim/config/robot.yaml`에서 반지름을 10% 크게 바꿉니다.

```yaml
wheel:
  radius: 0.055
```

시뮬레이션을 다시 시작하고, 컨테이너에 들어가 1 m 직진을 명령합니다.

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

결과를 읽어 봅니다.

- 바퀴 오차는 -0.003 rad/s로 거의 0입니다. DiffDrive와 `wheel_debug`가 같은 틀린 반지름을 쓰기 때문에, 바퀴는 "명령대로" 돌았습니다.
- `/odom`은 1.000 m를 갔다고 하지만, 실제로는 0.910 m만 갔습니다. 0.05 ÷ 0.055 ≈ 0.909입니다.

바퀴 오차 그래프만 보면 이 문제를 찾을 수 없습니다. 실제 위치와 비교해야 보입니다. 실제 로봇이라면 줄자로 잰 거리나 라이다로 본 벽까지의 거리가 실제 위치 역할을 합니다. Foxglove의 3D 패널에서는 라이다 점이 정면 벽 너머에 찍힙니다. 로봇 모델은 `/odom`이 말하는 1.000 m 지점에 그려지지만, 라이다는 실제 위치인 0.910 m 지점에서 벽까지 거리를 재기 때문입니다.

확인했으면 반지름을 0.05로 되돌리세요. 원래 값은 Fusion 메시에서 잰 값이므로, 3단계의 가져오기 스크립트를 다시 실행해도 됩니다.

```bash
python3 tools/import_fusion_urdf.py fusion/export/basic_description
```

다음 단계: [문제 해결](08-troubleshooting.md)
