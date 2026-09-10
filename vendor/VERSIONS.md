# Vendor 上游版本钉扎

本目录是**整树文件拷贝**，不是 git submodule，也不是 subtree 远端跟踪。
源码以本仓 `vendor/` 为准。上游 URL 只用于追溯，不是运行时源。

拷贝日期：2026-09-10。策略：各仓库 **default branch 当前 HEAD**（浅克隆后去掉 `.git`）。

未使用 git LFS。未发明自定义 RMW。本轮**不** vendor CycloneDDS / `rmw_cyclonedds`：链 B 作为 Unitree / 系统侧依赖，见仓库根 [README.md](../README.md)。

## 公开 ROS 2 / Fast-DDS 栈

| 目录 | 上游 | 分支 | 标签（若 HEAD 正好是 tag） | 完整 SHA |
|------|------|------|------------------------------|----------|
| `vendor/rmw/` | https://github.com/ros2/rmw | `rolling` | `7.11.2` | `1e58706ed978ff8a9066f17dc11c61d3a644bf76` |
| `vendor/rmw_implementation/` | https://github.com/ros2/rmw_implementation | `rolling` | （HEAD 无 tag；近旁 tag `3.2.1`） | `ff8818df2328396011543db07e8ddca99b54345a` |
| `vendor/rmw_fastrtps/` | https://github.com/ros2/rmw_fastrtps | `rolling` | （HEAD 无 tag；近旁 tag `9.5.2`） | `83471d45c448dfc7f4d408bc36cff593df14eb90` |
| `vendor/Fast-DDS/` | https://github.com/eProsima/Fast-DDS | `master` | （HEAD 无 tag；近旁稳定 tag `v3.6.2`） | `343f155c36b561db3d9f047a65d866ce0f3da300` |

`rmw_fastrtps` 含 `rmw_fastrtps_cpp` / `rmw_fastrtps_dynamic_cpp` / `rmw_fastrtps_shared_cpp`。链 A 契约 RMW 名仍是 **`rmw_fastrtps_cpp`**。

## Fast-DDS thirdparty（原 gitlink，已摊成普通目录）

上游 `Fast-DDS/.gitmodules` 仍保留作历史记录，但本仓**没有** submodule。下列空 gitlink 已按 Fast-DDS 记录的 commit 整树拷入：

| 路径 | 上游 | SHA |
|------|------|-----|
| `vendor/Fast-DDS/thirdparty/android-ifaddrs/` | https://github.com/michalsrb/android-ifaddrs | `7b1ce82817226e481d3cda0a5d06b66ebcc211f8` |
| `vendor/Fast-DDS/thirdparty/asio/` | https://github.com/chriskohlhoff/asio | `ed6aa8a13d51dfc6c00ae453fc9fb7df5d6ea963` |
| `vendor/Fast-DDS/thirdparty/fastcdr/` | https://github.com/eProsima/Fast-CDR | `7d33a3b51a1585f5631b0a8d905bcc4f249d0f34` |
| `vendor/Fast-DDS/thirdparty/tinyxml2/` | https://github.com/leethomason/tinyxml2 | `8c8293ba8969a46947606a93ff0cb5a083aab47a` |
| `vendor/Fast-DDS/thirdparty/dds-types-test/` | https://github.com/eProsima/dds-types-test | `2d2cfd15e36b323a12889454ffb09f9dc9d3ebe9` |

`boost` / `filewatch` / `nlohmann-json` / `optionparser` / `taocpp-pegtl` 本来就是 Fast-DDS 树内普通目录，原样保留。

## DimOS 双链代码（不在本目录）

见 [`dimos_bridge/SOURCE.md`](../dimos_bridge/SOURCE.md)。上游 `topsun_dimos` `main` @ `a5259958db23c8ea6648544ed138eab19726ce93`。

## 许可

各 vendor 树保留上游 LICENSE（多为 Apache-2.0）。本仓根 LICENSE 为 MIT，不覆盖这些拷贝。
