# Canonical ROS image recipe (R3 split).
# Install semantics match DimOS docker/ros/Dockerfile (Humble + Nav2 / foxglove / joy).
# Does NOT set RMW_IMPLEMENTATION, ROS_DOMAIN_ID, or FASTRTPS_DEFAULT_PROFILES_FILE
# — same as the DimOS original. Use config/env/ at runtime if needed.
#
# Build from repository root:
#   docker build -f docker/ros/Dockerfile .
#
# Historical path: dimos_bridge/docker/ros/Dockerfile (thin wrapper, same stages).

ARG FROM_IMAGE=ubuntu:22.04

FROM ${FROM_IMAGE} AS base
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV ROS_DISTRO=humble
COPY docker/ros/install-base.sh /tmp/ros-hzj/install-base.sh
RUN bash /tmp/ros-hzj/install-base.sh

FROM base AS runtime
COPY docker/ros/install-runtime.sh /tmp/ros-hzj/install-runtime.sh
RUN bash /tmp/ros-hzj/install-runtime.sh
