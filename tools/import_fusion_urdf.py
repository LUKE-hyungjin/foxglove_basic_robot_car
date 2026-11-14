"""Bring a Fusion 360 URDF export into the robot_car_sim package.

    python3 tools/import_fusion_urdf.py fusion/export/basic_description

Reads <export_dir>/*.urdf and <export_dir>/meshes/*.stl, then:
  1. copies the meshes to robot_car_sim/meshes/
  2. rewrites mesh paths to package://robot_car_sim/meshes/...
  3. applies the fixes listed in FIXES (each one was proven necessary in the sim)
  4. writes robot_car_sim/urdf/basic_robot_car.urdf
  5. measures wheel radius, wheel separation and lidar height from the meshes
     and writes them into robot_car_sim/config/robot.yaml
Every change is printed. Running it twice gives the same result.
"""
import re
import shutil
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "robot_car_sim"
MESH_URI = "package://robot_car_sim/meshes/"
OUTPUT_URDF = PACKAGE / "urdf" / "basic_robot_car.urdf"
ROBOT_YAML = PACKAGE / "config" / "robot.yaml"

LEFT_WHEEL_JOINT = "left_wheel_joint"
RIGHT_WHEEL_JOINT = "right_wheel_joint"
LIDAR_LINK = "lidar_1"


def stl_points(path):
    """Every vertex of a binary STL, in the file's own units."""
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        sys.exit(f"{path} is not a binary STL; export binary STL from Fusion")
    points = []
    for i in range(count):
        values = struct.unpack_from("<12f", data, 84 + 50 * i)
        points += [values[3:6], values[6:9], values[9:12]]
    return points


def xyz(element, attribute="xyz"):
    return [float(v) for v in element.get(attribute, "0 0 0").split()]


def mesh_points_in_link(link, mesh_dir):
    """Vertices of a link's visual mesh, in meters, in the link's frame."""
    visual = link.find("visual")
    mesh = visual.find("geometry/mesh")
    origin = visual.find("origin")
    if origin is not None and any(xyz(origin, "rpy")):
        sys.exit(f"{link.get('name')}: rotated visual origins are not supported")
    offset = xyz(origin) if origin is not None else [0, 0, 0]
    scale = xyz(mesh, "scale") if mesh.get("scale") else [1, 1, 1]
    return [
        [offset[i] + p[i] * scale[i] for i in range(3)]
        for p in stl_points(mesh_dir / Path(mesh.get("filename")).name)
    ]


def bounds(points):
    """(min xyz, max xyz)"""
    return (
        [min(p[axis] for p in points) for axis in range(3)],
        [max(p[axis] for p in points) for axis in range(3)],
    )


def mesh_bounds_in_link(link, mesh_dir):
    return bounds(mesh_points_in_link(link, mesh_dir))


def find(robot, tag, name):
    element = robot.find(f"{tag}[@name='{name}']")
    if element is None:
        sys.exit(f"the export has no {tag} named {name}")
    return element


# Fixes ---------------------------------------------------------------------------
# Each fix was added only after the simulation showed the raw export misbehaving.
def fix_wheel_axes(robot, mesh_dir):
    """DiffDrive spins both wheel joints the same way to drive forward, so both
    axes must point the same way (+Y: positive speed rolls the wheel forward)."""
    for joint_name in (LEFT_WHEEL_JOINT, RIGHT_WHEEL_JOINT):
        axis = find(robot, "joint", joint_name).find("axis")
        if xyz(axis) == [0.0, -1.0, 0.0]:
            axis.set("xyz", "0 1 0")
            print(f"fix     {joint_name} axis 0 -1 0 -> 0 1 0")


SUPPORT_LINK = "support_1"
SKID_TIP_RADIUS = 0.01
SKID_LIFT = 0.001


def fix_support_collision(robot, mesh_dir):
    """The skids and the wheels all touch z=0 in the export. Rigid physics then lets
    the skids carry the weight and the wheels slip (1 m on /odom, 0.47 m real).
    Replace the skid collision with one small sphere per foot, 1 mm above the
    floor, so the wheels carry the weight. Spheres instead of the ~10k-triangle
    mesh also keep /scan at 10 Hz (9.2 Hz with the mesh)."""
    link = find(robot, "link", SUPPORT_LINK)
    points = mesh_points_in_link(link, mesh_dir)
    floor = min(p[2] for p in points)
    feet = [p for p in points if p[2] < floor + 0.001]
    link.remove(link.find("collision"))
    for side in (1, -1):
        foot = [p for p in feet if p[0] * side > 0]
        x = round(sum(p[0] for p in foot) / len(foot), 4)
        z = round(floor + SKID_TIP_RADIUS + SKID_LIFT, 4)
        collision = ET.SubElement(link, "collision")
        ET.SubElement(collision, "origin", xyz=f"{x} 0 {z}", rpy="0 0 0")
        ET.SubElement(ET.SubElement(collision, "geometry"), "sphere", radius=str(SKID_TIP_RADIUS))
        print(f"fix     {SUPPORT_LINK} collision: skid foot sphere r={SKID_TIP_RADIUS} at x={x} "
              f"z={z} ({SKID_LIFT * 1000:.0f} mm above floor)")


FIXES = [fix_wheel_axes, fix_support_collision]


# Steps ---------------------------------------------------------------------------
def copy_meshes(export_dir):
    target = PACKAGE / "meshes"
    target.mkdir(exist_ok=True)
    for stl in sorted((export_dir / "meshes").glob("*.stl")):
        shutil.copy2(stl, target / stl.name)
        print(f"copy    {stl} -> {(target / stl.name).relative_to(REPO)}")


def rewrite_mesh_paths(robot):
    changed = {}
    for mesh in robot.iter("mesh"):
        old = mesh.get("filename")
        new = MESH_URI + Path(old).name
        if old != new:
            mesh.set("filename", new)
            changed[old] = new
    for old, new in changed.items():
        print(f"path    {old} -> {new}")


def measure(robot, mesh_dir):
    """Wheel radius, wheel separation, lidar scan height, all from the meshes."""
    wheel_centers_y = {}
    radii = []
    for joint_name in (LEFT_WHEEL_JOINT, RIGHT_WHEEL_JOINT):
        joint = find(robot, "joint", joint_name)
        link = find(robot, "link", joint.find("child").get("link"))
        lows, highs = mesh_bounds_in_link(link, mesh_dir)
        radii.append((highs[2] - lows[2]) / 2)
        wheel_centers_y[joint_name] = xyz(joint.find("origin"))[1] + (lows[1] + highs[1]) / 2

    lows, highs = mesh_bounds_in_link(find(robot, "link", LIDAR_LINK), mesh_dir)
    return {
        "radius": round(sum(radii) / 2, 4),
        "separation": round(wheel_centers_y[LEFT_WHEEL_JOINT] - wheel_centers_y[RIGHT_WHEEL_JOINT], 4),
        "lidar_z_offset": round((lows[2] + highs[2]) / 2, 4),
    }


def set_yaml_value(text, section, key, value):
    """Replace `key: ...` inside `section:` and keep every comment in the file."""
    pattern = rf"(^{section}:\n(?:[ #].*\n)*?  {key}: )\S+"
    text, count = re.subn(pattern, rf"\g<1>{value}", text, flags=re.M)
    if count != 1:
        sys.exit(f"{ROBOT_YAML.name}: could not find {section}.{key}")
    print(f"yaml    {section}.{key} = {value}")
    return text


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    export_dir = Path(sys.argv[1])
    urdf_files = list(export_dir.glob("*.urdf"))
    if len(urdf_files) != 1:
        sys.exit(f"expected exactly one .urdf in {export_dir}, found {len(urdf_files)}")

    tree = ET.parse(urdf_files[0])
    robot = tree.getroot()
    print(f"read    {urdf_files[0]}")

    copy_meshes(export_dir)
    mesh_dir = PACKAGE / "meshes"
    rewrite_mesh_paths(robot)
    for fix in FIXES:
        fix(robot, mesh_dir)

    ET.indent(tree, space="  ")
    tree.write(OUTPUT_URDF, encoding="utf-8", xml_declaration=True)
    print(f"write   {OUTPUT_URDF.relative_to(REPO)}")

    sizes = measure(robot, mesh_dir)
    text = ROBOT_YAML.read_text()
    text = set_yaml_value(text, "wheel", "radius", sizes["radius"])
    text = set_yaml_value(text, "wheel", "separation", sizes["separation"])
    text = set_yaml_value(text, "lidar", "z_offset", sizes["lidar_z_offset"])
    ROBOT_YAML.write_text(text)


if __name__ == "__main__":
    main()
