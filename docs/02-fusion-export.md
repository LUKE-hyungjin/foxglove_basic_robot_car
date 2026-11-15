# 2. Export a URDF from Fusion 360

In this step, you export the Fusion 360 model as one URDF file and one STL file per part. URDF is the format ROS uses to read a robot's links, joints, masses, and shapes.

If you don't have Fusion, read this step without running it. The exported files are already in `fusion/export/basic_description/`.

## Check the model's structure

The export script expects the model to follow these rules. Basic Robot Car already follows them.

- Every part is a component directly under the root. The root holds no bodies.
- The chassis component is named exactly `base_link`.
- Joints connect the parts. The wheels use **Revolute** joints, and the other parts use **Rigid** joints.
- A revolute joint without angle limits becomes `continuous` (endless rotation) in the URDF. Don't set limits on the wheels.

Basic Robot Car has these components:

| Component | Role | Joint |
| --- | --- | --- |
| `base_link` | 20 × 20 cm chassis | (reference) |
| `left_wheel` | Wheel, 10 cm diameter, 2.5 cm wide | Revolute |
| `rignt_wheel` | Right wheel | Revolute |
| `lidar` | Lidar on top of the chassis | Rigid |
| `support` | Two steel skids that rest on the floor, front and back | Rigid |

## Rename parts so that ROS can use them

The URDF's link and joint names become ROS topic names, TF frame names, and Gazebo plugin settings. Names with spaces or non-ASCII characters are hard to work with, so rename them with lowercase letters and underscores.

1. In the browser tree, rename the `rignt_wheel` component to `right_wheel`.
2. In the browser tree's **Joints** folder, rename each joint.

Fusion names each new joint after its type and a number, in the language of the UI. This model was built in a Korean UI, so its joints are named 회전 (revolute) and 강체 (rigid).

| Original name | Connected part | New name |
| --- | --- | --- |
| 회전 1 | `rignt_wheel` | `right_wheel_joint` |
| 회전 2 | `left_wheel` | `left_wheel_joint` |
| 강체 3 | `lidar` | `lidar_joint` |
| 강체 4 | `support` | `support_joint` |

> [!NOTE]
> The joint names must match the Gazebo settings in the next steps (`left_wheel_joint`, `right_wheel_joint`). The script makes each link name from its component name plus `_1` (`right_wheel_1`).

## Install the export script

Get [fusion360_urdf_script](https://github.com/LUKE-hyungjin/fusion360_urdf_script) and copy it into Fusion's scripts folder.

On macOS:

```bash
git clone https://github.com/LUKE-hyungjin/fusion360_urdf_script.git
cp -r fusion360_urdf_script/URDF "$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/"
```

In Windows PowerShell:

```powershell
git clone https://github.com/LUKE-hyungjin/fusion360_urdf_script.git
Copy-Item ".\fusion360_urdf_script\URDF\" -Destination "${env:APPDATA}\Autodesk\Autodesk Fusion 360\API\Scripts\" -Recurse
```

## Run the script

> [!WARNING]
> To export the STL files, the script copies components inside the design and renames the originals to `old_component`. After the export, **don't save** the design. Undo the changes (Cmd+Z) or close the design without saving.

1. In the **DESIGN** workspace, open the **UTILITIES** tab. In a Korean UI, it is the **유틸리티** tab.
2. In the **ADD-INS** panel, click **Scripts and Add-Ins**. In a Korean UI, it is **애드인 > 스크립트 및 애드인...**.
3. In the **Scripts** list, select `URDF` and click **Run**. If `URDF` is not in the list, add the copied `URDF` folder with the **+** button.
4. In the folder dialog, choose where to save the output.
5. The export is done when the message `Successfully create URDF file` appears.

## Check the output

The script creates a `<robot name>_description` folder inside the folder you chose. The robot name is the first word of the design name. The design is named `basic robot car`, so the robot name is `basic`.

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

Open `basic.urdf` and find a wheel joint:

```xml
<joint name="left_wheel_joint" type="continuous">
  <origin xyz="0.0 0.1 0.05" rpy="0 0 0"/>
  <parent link="base_link"/>
  <child link="left_wheel_1"/>
  <axis xyz="0.0 1.0 0.0"/>
</joint>
```

The export is correct when the joint name is in English, the type is `continuous`, and the wheel center height (`0.05`) equals the wheel radius. Units are meters. The STL files are in millimeters, and the URDF converts them to meters with `scale="0.001 0.001 0.001"`.

If you follow along with your own export, copy the exported folder over `fusion/export/basic_description/`.

Next: [Import the URDF into the simulation package](03-import-urdf.md)
