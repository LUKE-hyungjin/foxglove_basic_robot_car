FROM ros:jazzy-ros-base

RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-jazzy-ros-gz \
      ros-jazzy-foxglove-bridge \
      ros-jazzy-xacro \
      ros-jazzy-robot-state-publisher \
      libegl1 libgl1-mesa-dri mesa-utils \
    && rm -rf /var/lib/apt/lists/*

ENV ROS_DOMAIN_ID=0 \
    LIBGL_ALWAYS_SOFTWARE=1

WORKDIR /ws

# Shells opened with `docker compose exec sim bash` get ROS and the workspace too.
RUN echo 'source /opt/ros/jazzy/setup.bash; [ -f /ws/install/setup.bash ] && source /ws/install/setup.bash' >> /root/.bashrc

COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "robot_car_sim", "sim.launch.py"]
