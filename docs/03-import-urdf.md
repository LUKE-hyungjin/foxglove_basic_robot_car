# 3. URDF를 시뮬레이션 패키지로 가져오기

Fusion에서 내보낸 URDF는 그대로 Gazebo에 넣으면 제대로 달리지 않습니다. 이 단계에서는 `tools/import_fusion_urdf.py`로 원본을 시뮬레이션용 URDF로 바꾸고, 왜 바꿔야 하는지 확인합니다.

원본(`fusion/export/basic_description/`)은 수정하지 않습니다. Fusion에서 다시 내보내면 이 스크립트를 다시 실행하기만 하면 됩니다.

## 스크립트 실행하기

저장소 루트에서 실행합니다. 호스트의 Python 3.9 이상이면 되고, 추가 패키지는 필요 없습니다.

```bash
python3 tools/import_fusion_urdf.py fusion/export/basic_description
```

스크립트는 바꾸는 내용을 한 줄씩 출력합니다.

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

두 번 실행해도 결과는 같습니다.

## 스크립트가 바꾸는 것

### 메시 경로를 `package://`로 바꾸기

원본 URDF는 `meshes/base_link.stl`처럼 상대 경로를 씁니다. ROS에서 URDF는 파일이 아니라 `/robot_description` 토픽의 문자열로 전달되므로, 상대 경로의 기준 폴더가 없습니다. `package://robot_car_sim/meshes/base_link.stl`로 바꾸면 Gazebo와 Foxglove가 모두 패키지에서 메시를 찾습니다.

### 오른쪽 바퀴 축 방향 맞추기

원본에서 왼쪽 바퀴 축은 `0 1 0`, 오른쪽 바퀴 축은 `0 -1 0`입니다. Fusion은 조인트를 만든 방향대로 축을 정하기 때문입니다.

Gazebo의 DiffDrive 플러그인은 앞으로 갈 때 두 바퀴 조인트에 같은 부호의 속도를 줍니다. 오른쪽 축이 반대이면 오른쪽 바퀴는 뒤로 돌고, 로봇은 제자리에서 회전합니다. 스크립트는 오른쪽 축을 `0 1 0`으로 뒤집습니다. 바퀴는 원통이므로 축을 뒤집어도 모양은 같습니다.

### 받침이 바닥을 미끄러지게 하기

Basic Robot Car는 바퀴 2개와 앞뒤 받침 2개가 모두 z = 0에서 바닥에 닿습니다. 실제 로봇이라면 받침이 살짝 들려 있거나 미끄러지지만, 시뮬레이터의 강체는 네 점에 무게를 나눠 싣습니다. 그러면 바퀴에 걸리는 무게가 줄어 바퀴가 헛돕니다.

스크립트는 받침의 충돌 모양을 받침 끝마다 반지름 1 cm 구 하나로 바꾸고, 바닥에서 1 mm 띄웁니다. 받침의 겉모양(visual)은 그대로입니다. 구 2개는 9,496개 삼각형 메시보다 충돌 계산이 훨씬 가벼워서 라이다 주기도 10 Hz를 유지합니다.

### 측정한 값을 `robot.yaml`에 쓰기

바퀴 반지름, 바퀴 간격, 라이다 높이를 STL에서 직접 재서 `robot_car_sim/config/robot.yaml`에 씁니다. DiffDrive 플러그인과 바퀴 디버그 노드가 이 파일 하나를 읽으므로, 두 곳의 값이 어긋나지 않습니다.

```yaml
wheel:
  radius: 0.05
  separation: 0.225
lidar:
  z_offset: 0.0125
```

## 보정이 필요한 이유를 숫자로 보기

아래는 각 보정을 빼고 1 m 직진 명령(0.2 m/s로 5초)을 준 결과입니다. 모든 경우에 바퀴는 명령대로 정확히 4.000 rad/s로 돌았습니다. 달라진 것은 바닥과의 접촉뿐입니다.

| 시뮬레이션에 넣은 URDF | `/odom` 이동 | 실제 이동 |
| --- | --- | --- |
| 원본 그대로 | 1.000 m | 0.000 m |
| 바퀴 축만 고침 | 1.000 m | 0.000 m |
| 바퀴 축 + 받침 보정 (최종) | 0.999 m | 1.001 m |

`/odom`은 바퀴가 돈 양으로 계산한 위치라서 바퀴가 헛돌아도 1 m를 갔다고 말합니다. 실제 위치는 시뮬레이터가 알려 주는 `/ground_truth/odom`입니다. 7단계에서 이 두 값을 Foxglove로 직접 비교합니다.

## 최종 로봇 모델 보기

`robot_car_sim/urdf/robot_car.urdf.xacro`가 최종 로봇입니다. 가져온 URDF를 그대로 포함하고, Gazebo에만 필요한 부분을 덧붙입니다.

- 바퀴와 받침의 마찰 계수
- `lidar_1` 링크의 GPU 라이다 센서
- DiffDrive 플러그인. `/cmd_vel`을 바퀴 속도로 바꾸고 `/odom`을 냅니다.
- JointStatePublisher 플러그인. 바퀴 각도와 속도를 `/joint_states`로 냅니다.
- OdometryPublisher 플러그인. 실제 위치를 `/ground_truth/odom`으로 냅니다.

다음 단계: [Blender로 경기장 맵 만들기](04-blender-map.md)
