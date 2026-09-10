# ROS Dockerfile 拆分（R3）

历史路径仍是 [`dimos_bridge/docker/ros/Dockerfile`](../../dimos_bridge/docker/ros/Dockerfile)（DimOS 拷贝位置）。  
**安装语义不变**：包名、`ROS_DISTRO=humble`、不设置 `RMW_IMPLEMENTATION` / `ROS_DOMAIN_ID` / `FASTRTPS_*`，与 `topsun_dimos` `docker/ros/Dockerfile` 一致。

## 拆成什么

| 文件 | 阶段 | 内容 |
|------|------|------|
| [`install-base.sh`](install-base.sh) | base | locale、基础 apt、ROS apt 源 |
| [`install-runtime.sh`](install-runtime.sh) | runtime | Humble desktop / Nav2 / foxglove / joy、rosdep、bashrc |
| [`Dockerfile`](Dockerfile) | 组装 | `FROM` → `base` → `runtime` |
| `dimos_bridge/docker/ros/Dockerfile` | 兼容包装 | 同一套脚本；给旧路径用 |

`install-nix.sh` 仍留在 `dimos_bridge/docker/ros/`，本拆分不改它。

## 怎么构建

必须从**仓库根**做 context（脚本在 `docker/ros/`）：

```bash
docker build -f docker/ros/Dockerfile .
docker build -f dimos_bridge/docker/ros/Dockerfile .
```

两条命令应装同一组包。本拆分**没有**加导航专用镜像，也没有偷偷写入域 42。

## 不是什么

- 不是 `docker/navigation/`（DimOS main 上不存在，本仓不伪造）
- 不是自定义 RMW
- 不改变已拷 DimOS 模块的运行时默认
