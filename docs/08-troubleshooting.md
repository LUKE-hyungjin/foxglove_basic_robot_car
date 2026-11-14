# 8. 문제 해결

증상별로 원인과 해결 방법을 정리했습니다.

## Docker와 시뮬레이션

### `failed to connect to the docker API`

Docker Desktop이 실행되어 있지 않습니다. Docker Desktop을 열고, `docker info`가 서버 버전을 출력할 때까지 기다리세요.

### `Bind for 0.0.0.0:8765 failed: port is already allocated`

다른 프로그램이나 이전 시뮬레이션이 8765 포트를 쓰고 있습니다. 어떤 컨테이너가 포트를 쓰는지 확인합니다.

```bash
docker ps --format '{{.Names}}\t{{.Ports}}'
```

이 저장소의 시뮬레이션이 남아 있다면 `docker compose down`으로 끄세요.

### `/scan`이 10 Hz보다 느림

라이다는 CPU로 렌더링되므로, 컴퓨터가 바쁘면 시뮬레이터 전체가 실제 시간보다 느려집니다. 다른 컨테이너가 CPU를 많이 쓰는 상태에서는 9.4~9.8 Hz까지 떨어지는 것을 확인했습니다. 다른 컨테이너를 끄거나 Docker Desktop의 CPU 할당을 늘리세요.

### 로봇이 Gazebo에 나타나지 않음

`docker compose up` 로그에서 `Entity creation successful`을 찾으세요. 없다면 `robot_state_publisher`가 URDF를 만들지 못한 것입니다. 컨테이너 안에서 xacro를 직접 실행해 오류를 봅니다.

```bash
docker compose run --rm sim bash
xacro /ws/src/robot_car_sim/urdf/robot_car.urdf.xacro > /tmp/robot.urdf
```

## Foxglove

### 연결은 되는데 3D 패널에 로봇이나 맵이 없음

Foxglove는 `package://robot_car_sim/...` 경로의 STL을 `foxglove_bridge`에서 받아 옵니다. 호스트에서 점검 스크립트를 실행하세요.

```bash
python3 scripts/check_bridge.py
```

`fetchAsset ... bytes` 줄이 두 개 있으면 브리지는 정상입니다. 그래도 안 보이면 3D 패널 설정에서 `/map` 토픽과 로봇 모델 레이어가 켜져 있는지 확인하세요.

### 경기장이 90° 누워 있고 바퀴가 이상하게 돎

3D 패널이 STL 메시를 Y축이 위인 것으로 읽고 있습니다. Gazebo 안의 로봇과 맵은 정상입니다. 3D 패널 설정의 **Scene > Mesh up axis**를 **Z-up**으로 바꾸고, Foxglove를 다시 불러오세요(Cmd+R). `foxglove/robot_car_debug.json` 레이아웃은 이 값을 이미 Z-up으로 설정합니다.

### Teleop 버튼을 눌러도 로봇이 움직이지 않음

Teleop 패널의 토픽이 `/cmd_vel`인지 확인하세요. 컨테이너 안에서 명령이 들어오는지 봅니다.

```bash
docker compose exec sim bash
ros2 topic echo /cmd_vel
```

버튼을 누를 때 메시지가 찍히지 않으면 Foxglove 연결 문제입니다.

## Fusion 360 내보내기

### `No module named 'distutils'`

이전 버전의 `fusion360_urdf_script`입니다. Fusion은 이제 Python 3.12 이상을 쓰는데, 이 버전부터 `distutils`가 없습니다. 최신 `main`을 받아 `URDF` 폴더를 다시 복사하세요.

### `cannot unpack non-iterable NoneType object`

이전 버전의 `fusion360_urdf_script`가 색상을 영어 속성 이름 `Color`로만 찾았기 때문입니다. 한국어 등 다른 언어 UI의 Fusion에서 이 오류가 납니다. 최신 `main`을 받으세요.

### `There is no base_link. Please set base_link and run again.`

차체 컴포넌트의 이름이 정확히 `base_link`가 아닙니다. 브라우저 트리에서 이름을 바꾸세요.

### 내보낸 뒤 디자인에 `old_component`가 생김

스크립트가 STL을 내보내려고 컴포넌트를 복사한 흔적입니다. 디자인을 저장하지 말고, 실행 취소하거나 저장하지 않고 닫으세요.

## 로봇 동작

### 로봇이 앞으로 가지 않고 제자리에서 돔

오른쪽 바퀴 조인트 축이 왼쪽과 반대 방향입니다. `tools/import_fusion_urdf.py`를 거치지 않은 원본 URDF를 쓰고 있는지 확인하세요. 3단계를 참고하세요.

### `/odom`은 움직이는데 로봇은 제자리에 있음

바퀴가 헛돌고 있습니다. 받침이 바퀴와 같은 높이에서 무게를 나눠 받으면 이렇게 됩니다. 3단계의 받침 보정이 적용되었는지 `robot_car_sim/urdf/basic_robot_car.urdf`의 `support_1` 충돌 모양이 구(`sphere`)인지 확인하세요.
