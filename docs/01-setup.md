# 1. 환경 준비

이 단계에서는 시뮬레이션을 돌릴 Docker와 화면을 볼 Foxglove를 설치하고, 저장소를 받습니다. ROS 2와 Gazebo는 컨테이너 안에서 돌기 때문에 내 컴퓨터에 따로 설치하지 않습니다.

## 필요한 프로그램

| 프로그램 | 용도 | 필수 여부 |
| --- | --- | --- |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | ROS 2 Jazzy와 Gazebo Harmonic 실행 | 필수 |
| [Foxglove](https://foxglove.dev/download) | 라이다와 바퀴 데이터 시각화 | 필수 |
| Git | 저장소 받기 | 필수 |
| Autodesk Fusion | 로봇 모델 내보내기 (2단계) | 선택 |
| [Blender](https://www.blender.org/download/) 4.2 이상 | 경기장 맵 만들기 (4단계) | 선택 |

Fusion과 Blender로 만든 결과물은 저장소에 이미 들어 있습니다. 두 프로그램이 없으면 2단계와 4단계는 읽기만 하고 넘어가도 됩니다.

## Docker 메모리 확인하기

Gazebo는 라이다를 CPU로 렌더링하므로 메모리와 CPU를 꽤 씁니다. Docker Desktop의 **Settings > Resources**에서 메모리를 4 GB 이상으로 잡으세요.

Docker가 실행 중인지 확인합니다.

```bash
docker info --format '{{.ServerVersion}} {{.Architecture}}'
```

버전과 아키텍처가 한 줄로 나오면 준비가 끝났습니다.

```text
29.3.1 aarch64
```

`failed to connect to the docker API`가 나오면 Docker Desktop을 실행한 뒤 다시 확인하세요.

## 저장소 받기

```bash
git clone https://github.com/LUKE-hyungjin/foxglove_basic_robot_car.git
cd foxglove_basic_robot_car
```

## 컨테이너 이미지 미리 빌드하기

처음 빌드할 때 ROS 2와 Gazebo 패키지를 내려받으므로 몇 분 걸립니다. 지금 미리 빌드해 두면 5단계에서 바로 시작할 수 있습니다.

```bash
docker compose build
```

마지막 줄에 이미지 이름이 보이면 성공입니다.

```text
 Image robot-car-sim:dev Built
```

다음 단계: [Fusion 360에서 URDF 내보내기](02-fusion-export.md)
