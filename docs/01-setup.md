# 1. Set up your environment

In this step, you install Docker to run the simulation and Foxglove to view it, and you get the repository. ROS 2 and Gazebo run inside a container, so you don't install them on your computer.

## What you need

| Program | Used for | Required |
| --- | --- | --- |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Runs ROS 2 Jazzy and Gazebo Harmonic | Yes |
| [Foxglove](https://foxglove.dev/download) | Shows the lidar and wheel data | Yes |
| Git | Gets the repository | Yes |
| Autodesk Fusion | Exports the robot model (step 2) | No |
| [Blender](https://www.blender.org/download/) 4.2 or later | Builds the arena map (step 4) | No |

The repository already contains what Fusion and Blender produce. If you don't have them, read steps 2 and 4 without running them.

On macOS, you can install Foxglove with Homebrew:

```bash
brew install --cask foxglove
```

## Check Docker's resources

Gazebo renders the lidar on the CPU, so it uses a fair amount of memory and CPU. In Docker Desktop, open **Settings > Resources** and give Docker at least 4 GB of memory.

Check that Docker is running:

```bash
docker info --format '{{.ServerVersion}} {{.Architecture}}'
```

You see the version and the architecture on one line:

```text
29.3.1 aarch64
```

If you see `failed to connect to the docker API`, start Docker Desktop and check again.

## Get the repository

```bash
git clone https://github.com/LUKE-hyungjin/foxglove_basic_robot_car.git
cd foxglove_basic_robot_car
```

## Build the container image now

The first build downloads the ROS 2 and Gazebo packages, so it takes a few minutes. Build it now, and step 5 starts right away.

```bash
docker compose build
```

The build is done when the last line names the image:

```text
 Image robot-car-sim:dev Built
```

Next: [Export a URDF from Fusion 360](02-fusion-export.md)
