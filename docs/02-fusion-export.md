# 2. Fusion 360에서 URDF 내보내기

이 단계에서는 Fusion 360 모델을 URDF 파일 1개와 부품별 STL 파일로 내보냅니다. URDF는 ROS가 로봇의 링크, 조인트, 질량, 모양을 읽는 형식입니다.

Fusion이 없다면 이 단계는 읽기만 하세요. 내보낸 결과물은 `fusion/export/basic_description/`에 이미 들어 있습니다.

## 모델 구조 확인하기

내보내기 스크립트는 모델이 아래 규칙을 지킨다고 가정합니다. Basic Robot Car는 이미 이 규칙대로 만들어져 있습니다.

- 모든 부품이 루트 바로 아래의 컴포넌트입니다. 루트에는 바디를 두지 않습니다.
- 차체 컴포넌트의 이름은 정확히 `base_link`입니다.
- 부품 사이에는 조인트가 있습니다. 바퀴는 **회전** 조인트, 나머지는 **강체** 조인트입니다.
- 회전 조인트에 각도 제한이 없으면 URDF에서 `continuous`(무한 회전)가 됩니다. 바퀴에는 제한을 두지 마세요.

Basic Robot Car의 구성은 다음과 같습니다.

| 컴포넌트 | 역할 | 조인트 |
| --- | --- | --- |
| `base_link` | 20 × 20 cm 차체 | (기준) |
| `left_wheel` | 지름 10 cm, 폭 2.5 cm 바퀴 | 회전 |
| `rignt_wheel` | 오른쪽 바퀴 | 회전 |
| `lidar` | 차체 위 라이다 | 강체 |
| `support` | 앞뒤로 바닥을 받치는 강철 받침 2개 | 강체 |

## 이름을 ROS에서 쓸 수 있게 바꾸기

URDF의 링크와 조인트 이름은 ROS 토픽, TF 프레임, Gazebo 플러그인 설정에 그대로 쓰입니다. 공백이나 한글이 들어가면 다루기 어려우므로 영문 소문자와 밑줄로 바꿉니다.

1. 브라우저 트리에서 `rignt_wheel` 컴포넌트를 `right_wheel`로 이름을 바꿉니다.
2. 브라우저 트리의 **조인트** 폴더에서 각 조인트의 이름을 바꿉니다.

| 원래 이름 | 연결된 부품 | 새 이름 |
| --- | --- | --- |
| 회전 1 | `rignt_wheel` | `right_wheel_joint` |
| 회전 2 | `left_wheel` | `left_wheel_joint` |
| 강체 3 | `lidar` | `lidar_joint` |
| 강체 4 | `support` | `support_joint` |

> [!NOTE]
> 조인트 이름은 다음 단계의 Gazebo 설정(`left_wheel_joint`, `right_wheel_joint`)과 맞아야 합니다. 링크 이름은 스크립트가 컴포넌트 이름 뒤에 `_1`을 붙여 만듭니다(`right_wheel_1`).

## 내보내기 스크립트 설치하기

[fusion360_urdf_script](https://github.com/LUKE-hyungjin/fusion360_urdf_script)를 받아 Fusion의 스크립트 폴더에 복사합니다.

macOS에서는 다음과 같이 합니다.

```bash
git clone https://github.com/LUKE-hyungjin/fusion360_urdf_script.git
cp -r fusion360_urdf_script/URDF "$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/"
```

Windows PowerShell에서는 다음과 같이 합니다.

```powershell
git clone https://github.com/LUKE-hyungjin/fusion360_urdf_script.git
Copy-Item ".\fusion360_urdf_script\URDF\" -Destination "${env:APPDATA}\Autodesk\Autodesk Fusion 360\API\Scripts\" -Recurse
```

## 스크립트 실행하기

> [!WARNING]
> 스크립트는 STL을 내보내려고 디자인 안에 컴포넌트를 복사하고, 원래 컴포넌트의 이름을 `old_component`로 바꿉니다. 내보낸 뒤에는 디자인을 **저장하지 마세요**. 실행 취소(Cmd+Z)로 되돌리거나 저장하지 않고 닫으세요.

1. **디자인** 작업공간에서 **유틸리티** 탭을 엽니다. 영어 UI에서는 **UTILITIES** 탭입니다.
2. **애드인** 패널에서 **스크립트 및 애드인...**을 클릭합니다. 영어 UI에서는 **ADD-INS > Scripts and Add-Ins**입니다.
3. **스크립트** 목록에서 `URDF`를 선택하고 **실행**을 클릭합니다. 목록에 `URDF`가 없으면 **+** 버튼으로 복사한 `URDF` 폴더를 직접 추가합니다.
4. 폴더 선택 창에서 결과물을 저장할 폴더를 고릅니다.
5. `Successfully create URDF file` 메시지가 나오면 끝입니다.

## 결과물 확인하기

선택한 폴더 안에 `<로봇 이름>_description` 폴더가 생깁니다. 로봇 이름은 디자인 이름의 첫 단어입니다. 디자인 이름이 `basic robot car`이므로 로봇 이름은 `basic`입니다.

```text
basic_description/
  basic.urdf
  meshes/
    base_link.stl
    left_wheel_1.stl
    right_wheel_1.stl
    lidar_1.stl
    support_1.stl
```

`basic.urdf`를 열어 바퀴 조인트를 확인합니다.

```xml
<joint name="left_wheel_joint" type="continuous">
  <origin xyz="0.0 0.1 0.05" rpy="0 0 0"/>
  <parent link="base_link"/>
  <child link="left_wheel_1"/>
  <axis xyz="0.0 1.0 0.0"/>
</joint>
```

조인트 이름이 영문이고, 종류가 `continuous`이고, 바퀴 중심 높이(`0.05`)가 바퀴 반지름과 같으면 제대로 내보낸 것입니다. 단위는 미터입니다. STL은 밀리미터 단위로 저장되고, URDF가 `scale="0.001 0.001 0.001"`로 미터로 바꿉니다.

이 저장소를 직접 따라 한다면, 내보낸 폴더를 `fusion/export/basic_description/`에 덮어씁니다.

다음 단계: [URDF를 시뮬레이션 패키지로 가져오기](03-import-urdf.md)
