# Thin compatibility wrapper for the historical DimOS path.
# Canonical split: docker/ros/Dockerfile + install-base.sh + install-runtime.sh
# Install semantics unchanged (Humble + Nav2 / foxglove / joy; no RMW/domain ENV).
#
# Build from repository root:
#   docker build -f dimos_bridge/docker/ros/Dockerfile .

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
