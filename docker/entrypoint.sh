#!/bin/bash
# Build the workspace (fast: one Python package), then run the given command.
set -e
source /opt/ros/jazzy/setup.bash
cd /ws
colcon build --symlink-install --event-handlers console_direct- >/dev/null
source /ws/install/setup.bash
exec "$@"
