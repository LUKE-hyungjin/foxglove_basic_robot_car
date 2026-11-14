from glob import glob

from setuptools import setup

package_name = "robot_car_sim"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
        ("share/" + package_name + "/urdf", glob("urdf/*")),
        ("share/" + package_name + "/worlds", glob("worlds/*.sdf")),
        ("share/" + package_name + "/models/arena/meshes", glob("models/arena/meshes/*")),
        ("share/" + package_name + "/meshes", glob("meshes/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="hyungjin",
    maintainer_email="hyungjin.lee@makinarocks.ai",
    description="Basic Robot Car in Gazebo, debugged in Foxglove.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "wheel_debug = robot_car_sim.wheel_debug:main",
            "map_marker = robot_car_sim.map_marker:main",
            "cmd_vel_timeout = robot_car_sim.cmd_vel_timeout:main",
        ],
    },
)
