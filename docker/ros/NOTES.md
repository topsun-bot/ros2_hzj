# ROS Dockerfile 拆分（R3）

规范路径是仓库根 [`docker/ros/`](.)。  
**安装语义不变**：包名、`ROS_DISTRO=humble`、不设置 `RMW_IMPLEMENTATION` / `ROS_DOMAIN_ID` / `FASTRTPS_*`，与 `topsun_dimos` `docker/ros/Dockerfile` 一致。

## 拆成什么

| 文件 | 阶段 | 内容 |
|------|------|------|
| [`install-base.sh`](install-base.sh) | base | locale、基础 apt、ROS apt 源 |
| [`install-runtime.sh`](install-runtime.sh) | runtime | Humble desktop / Nav2 / foxglove / joy、rosdep、bashrc |
| [`Dockerfile`](Dockerfile) | 组装 | `FROM` → `base` → `runtime` |

## 怎么构建

必须从**仓库根**做 context（脚本在 `docker/ros/`）：

```bash
docker build -f docker/ros/Dockerfile .
```

本拆分**没有**加导航专用镜像，也没有偷偷写入域 42。

## 不是什么

- 不是 `docker/navigation/`（DimOS main 上不存在，本仓不伪造）
- 不是自定义 RMW
- 不改变已拷 DimOS 模块的运行时默认
