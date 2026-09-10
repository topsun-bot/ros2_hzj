#!/usr/bin/env bash
# 链外 ROS 镜像 — runtime 阶段。包列表与 DimOS docker/ros/Dockerfile 一致。
# 依赖 ENV ROS_DISTRO（Dockerfile 设为 humble）。
set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"
: "${ROS_DISTRO:?ROS_DISTRO must be set (humble)}"

apt-get update && apt-get install -y \
    ros-${ROS_DISTRO}-desktop \
    ros-${ROS_DISTRO}-ros-base \
    ros-${ROS_DISTRO}-image-tools \
    ros-${ROS_DISTRO}-compressed-image-transport \
    ros-${ROS_DISTRO}-vision-msgs \
    ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-rqt \
    ros-${ROS_DISTRO}-rqt-common-plugins \
    ros-${ROS_DISTRO}-twist-mux \
    ros-${ROS_DISTRO}-joy \
    ros-${ROS_DISTRO}-teleop-twist-joy \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-nav2-amcl \
    ros-${ROS_DISTRO}-nav2-map-server \
    ros-${ROS_DISTRO}-nav2-util \
    ros-${ROS_DISTRO}-pointcloud-to-laserscan \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-foxglove-bridge \
    python3-rosdep \
    python3-rosinstall \
    python3-rosinstall-generator \
    python3-wstool \
    python3-colcon-common-extensions \
    python3-vcstool \
    build-essential \
    screen \
    tmux

rosdep init
rosdep update

echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc
