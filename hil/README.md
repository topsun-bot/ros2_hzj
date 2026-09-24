# hil — 原生 DDS 实测与时延探针

在 Colima VM（原生 arm64 Linux）内对 ROS 2 做真实 pub/sub 与时延分布测试。
报告：`docs/testing/2026-09-mac-hil-native.md`。

## 边界
- Apple Silicon 上若只有 **amd64** ROS 镜像，会经 qemu 模拟，DDS 数据面静默不通（见报告 BUG-H1）；务必用**原生 arm64 runtime**。
- 本套默认在 VM 内用 Jazzy（Ubuntu 24.04）。它是功能/时延代理，**不是 Humble 认证**；loopback、单机，跨机/真实网卡不在此覆盖。

## 文件
- `lat_talker.py` / `lat_listener.py`：单向时延探针（`seq,monotonic_ns`，纯 Python 算 p50/p90/p95/p99）。
- `run_latency.sh`：跑 FastDDS 默认、FastDDS UDP-only、Cyclone 三配置。
- `run_fast.sh`：只跑 FastDDS 两配置。
- `udp_only.xml`：测试专用，强制 FastDDS UDPv4、禁 SHM（**非**冻结的 `config/fastdds.xml`）。
- `mc_rx.py` / `mc_tx.py`：跨容器多播可达性自检。

## 运行
```bash
colima start
# VM 内安装好 ROS（Jazzy）后：
colima ssh -- bash /Users/zhang/colima-work/ros2_hzj/hil/run_latency.sh 1000 300 100
# 参数：need=1000 有效样本，warmup=300 丢弃，rate=100 Hz
```

## 说明
- 两进程同核，CLOCK_MONOTONIC 一致，单向时延 = recv−send。
- 结果仅代表所测 runtime/环境；**不要**写入冻结的 `docs/artifacts/bench/SCOREBOARD.md`，也不要编辑 `config/fastdds.xml`。
