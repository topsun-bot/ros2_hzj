"""R0 冻结 topic / QoS 常量（R4）。只提供名字，不改 publisher 行为。

DimOS 已拷模块（如 ``unitree_go2_ros.py``）**尚未**改成从这里 import。
可选：新代码可以 ``from dimos.protocol.dds_topics import TOPIC_GOAL_POSE``。

权威表：``docs/architecture/ros2-dds-r0-interface-freeze.md``。
YAML 镜像：``config/topics.yaml``。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# 发现域（两条链，不要混用）
CHAIN_A_ROS_DOMAIN_ID: Final[int] = 42
CHAIN_B_CYCLONE_DOMAIN_ID: Final[int] = 0

# 链 A 导航契约 topic
TOPIC_FOXGLOVE_TELEOP: Final[str] = "/foxglove_teleop"
TOPIC_CMD_VEL: Final[str] = "/cmd_vel"
TOPIC_GOAL_POSE: Final[str] = "/goal_pose"
TOPIC_WAY_POINT: Final[str] = "/way_point"
TOPIC_JOY: Final[str] = "/joy"

# Go2 ROS bridge（unitree_go2_ros.py 里的 ROSTransport 名）
GO2_LIDAR: Final[str] = "lidar"
GO2_GLOBAL_MAP: Final[str] = "global_map"
GO2_ODOM: Final[str] = "odom"
GO2_COLOR_IMAGE: Final[str] = "color_image"


@dataclass(frozen=True)
class QosContract:
    reliability: str
    durability: str | None
    history: str
    depth: int


@dataclass(frozen=True)
class TopicContract:
    topic: str
    type_name: str
    qos: QosContract | None
    maps_to: str | None = None
    dest_type: str | None = None


# 冻结表 §2。不是 DimosROS 库默认 QoS。
NAV_PATH_TOPICS: Final[tuple[TopicContract, ...]] = (
    TopicContract(
        topic=TOPIC_FOXGLOVE_TELEOP,
        type_name="geometry_msgs/Twist",
        maps_to=TOPIC_CMD_VEL,
        dest_type="geometry_msgs/TwistStamped",
        qos=QosContract("BEST_EFFORT", "VOLATILE", "KEEP_LAST", 1),
    ),
    TopicContract(
        topic=TOPIC_GOAL_POSE,
        type_name="geometry_msgs/PoseStamped",
        qos=QosContract("RELIABLE", "VOLATILE", "KEEP_LAST", 5),
    ),
    TopicContract(
        topic=TOPIC_WAY_POINT,
        type_name="geometry_msgs/PointStamped",
        qos=QosContract("RELIABLE", "VOLATILE", "KEEP_LAST", 5),
    ),
    TopicContract(
        topic=TOPIC_JOY,
        type_name="sensor_msgs/Joy",
        qos=None,
    ),
)

GO2_ROS_BINDINGS: Final[tuple[tuple[str, str], ...]] = (
    (GO2_LIDAR, "sensor_msgs/PointCloud2"),
    (GO2_GLOBAL_MAP, "sensor_msgs/PointCloud2"),
    (GO2_ODOM, "geometry_msgs/PoseStamped"),
    (GO2_COLOR_IMAGE, "sensor_msgs/Image"),
)


__all__ = [
    "CHAIN_A_ROS_DOMAIN_ID",
    "CHAIN_B_CYCLONE_DOMAIN_ID",
    "GO2_COLOR_IMAGE",
    "GO2_GLOBAL_MAP",
    "GO2_LIDAR",
    "GO2_ODOM",
    "GO2_ROS_BINDINGS",
    "NAV_PATH_TOPICS",
    "QosContract",
    "TOPIC_CMD_VEL",
    "TOPIC_FOXGLOVE_TELEOP",
    "TOPIC_GOAL_POSE",
    "TOPIC_JOY",
    "TOPIC_WAY_POINT",
    "TopicContract",
]
