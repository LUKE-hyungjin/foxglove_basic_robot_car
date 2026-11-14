# 4. Blender로 경기장 맵 만들기

이 단계에서는 Blender 스크립트로 6 m × 6 m 경기장을 만들고 STL로 내보냅니다. 마우스로 모델링하지 않고 스크립트로 만들기 때문에, 숫자만 바꿔 다시 실행하면 같은 맵이 정확히 다시 나옵니다.

Blender가 없다면 읽기만 하세요. 결과물 `robot_car_sim/models/arena/meshes/arena.stl`은 저장소에 이미 들어 있습니다.

## 맵 구성 보기

`blender/make_map.py`의 위쪽에 맵이 숫자로 정의되어 있습니다. 단위는 미터이고, Z축이 위쪽입니다.

```python
ARENA_SIZE = 6.0        # inner width/length of the square arena
WALL_HEIGHT = 0.4
WALL_THICKNESS = 0.1

# (name, center x, center y, size x, size y, yaw degrees)
BOXES = [
    ("box_ahead", 1.5, 0.0, 0.4, 0.6, 0),       # front face at x = 1.3
    ("box_left", -1.2, 1.6, 0.6, 0.6, 30),
    ("box_corner", 2.0, 2.0, 0.5, 0.5, 0),
    ("l_wall_long", -2.0, -1.25, 0.1, 1.6, 0),  # L-wall: long leg along Y
    ("l_wall_short", -1.4, -2.0, 1.3, 0.1, 0),  # L-wall: short leg along X
]

# (name, center x, center y, radius)
CYLINDERS = [
    ("pillar", 0.8, -1.8, 0.3),
]
```

로봇은 원점에서 +X 방향을 보고 출발합니다. 그래서 정면 1.3 m 지점에 상자(`box_ahead`)를 두었습니다. 6단계에서 라이다가 이 거리를 정확히 읽는지 확인합니다.

바닥은 이 맵에 넣지 않습니다. Gazebo 월드(`robot_car_sim/worlds/arena.sdf`)가 바닥 평면을 따로 추가합니다.

## 맵 내보내기

저장소 루트에서 Blender를 화면 없이 실행합니다.

```bash
blender -b --factory-startup -P blender/make_map.py
```

- `-b`는 화면 없이 실행합니다.
- `--factory-startup`은 내 Blender 설정을 무시하고 기본 상태로 시작합니다. 그래서 누가 실행해도 결과가 같습니다.
- `-P`는 스크립트를 실행합니다.

다음 줄이 보이면 성공입니다.

```text
Info: File exported successfully
Wrote .../robot_car_sim/models/arena/meshes/arena.stl
```

macOS에서 `blender` 명령이 없으면 앱 안의 실행 파일을 직접 부릅니다.

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P blender/make_map.py
```

## Blender 화면에서 확인하기

화면에서 보고 싶다면 스크립트를 열어 실행합니다.

```bash
blender --factory-startup -P blender/make_map.py
```

벽 4개, 상자 3개, L자 벽, 원기둥 1개가 보입니다.

## 직접 바꿔 보기

`BOXES`에 상자를 하나 추가하고 다시 내보내세요. 로봇 출발 지점(원점에서 반지름 0.6 m 이내)은 비워 둡니다.

```python
    ("my_box", 0.0, 1.5, 0.3, 0.3, 45),
```

시뮬레이션을 다시 시작하면 Gazebo와 Foxglove에 새 상자가 나타납니다. 두 프로그램 모두 같은 `arena.stl`을 읽기 때문입니다.

다음 단계: [Gazebo 시뮬레이션 실행하기](05-gazebo-sim.md)
