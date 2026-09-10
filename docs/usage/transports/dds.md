# Installing DDS Transport Libs on Ubuntu

> **Repo note.** This page is R0 reference copied from [`topsun-bot/topsun_dimos`](https://github.com/topsun-bot/topsun_dimos) (PR [#122](https://github.com/topsun-bot/topsun_dimos/pull/122)). The `.[dds]` extra, Nix recipe, and `uv` commands below belong to **DimOS** (Chain B / Cyclone).
>
> **R2.** `ros2_hzj` vendors **both** chains as plain copies under [`vendor/`](../../../vendor/): Fast-DDS (`rmw`, `rmw_implementation`, `rmw_fastrtps`, `Fast-DDS`) and Cyclone (`rmw_cyclonedds`, `CycloneDDS`). SHA 见 [`vendor/VERSIONS.md`](../../../vendor/VERSIONS.md)。CI **不**编译这些树。运行 Python `cyclonedds` 仍要本机 C 库（Nix / apt），与下面安装步骤相同。双链契约见 [R0 interface freeze](../../architecture/ros2-dds-r0-interface-freeze.md)。评测怎么跑见 [benchmark-dds.md](../benchmark-dds.md)（无伪造分数）。

The `dds` extra (in `topsun_dimos`) provides DDS (Data Distribution Service) transport support via [Eclipse Cyclone DDS](https://cyclonedds.io/docs/cyclonedds-python/latest/). The Python package builds C extensions against the CycloneDDS C library, so the C library must be installed before the Python package.

## Recommended: nix-provided cyclonedds

No `sudo`, no system pollution. Requires [Nix](https://nixos.org/) (DimOS also documents Nix under `docs/installation/nix.md` in `topsun_dimos`).

```bash
nix build nixpkgs#cyclonedds        # creates ./result symlink (GC root)
export CYCLONEDDS_HOME=$PWD/result
export LD_LIBRARY_PATH="$CYCLONEDDS_HOME/lib:$LD_LIBRARY_PATH"
uv pip install -e '.[dds]'
```

`LD_LIBRARY_PATH` must stay set at runtime. Persist with one of:

```bash
# Per-venv (auto-set on `source .venv/bin/activate`)
cat >> .venv/bin/activate <<EOF
export CYCLONEDDS_HOME=$(readlink -f ./result)
export LD_LIBRARY_PATH="\$CYCLONEDDS_HOME/lib:\${LD_LIBRARY_PATH:-}"
EOF
```

```bash
# Global (every shell)
cat >> ~/.bashrc <<EOF
export CYCLONEDDS_HOME=$(readlink -f ./result)
export LD_LIBRARY_PATH="\$CYCLONEDDS_HOME/lib:\${LD_LIBRARY_PATH:-}"
EOF
```

## Alternative: Ubuntu apt + symlink shim

```bash
# Install the CycloneDDS development library
sudo apt install cyclonedds-dev

# Create a compatibility directory structure
# (required because Ubuntu's multiarch layout doesn't match the expected CMake layout)
sudo mkdir -p /opt/cyclonedds/{lib,bin,include}
sudo ln -sf /usr/lib/x86_64-linux-gnu/libddsc.so* /opt/cyclonedds/lib/
sudo ln -sf /usr/lib/x86_64-linux-gnu/libcycloneddsidl.so* /opt/cyclonedds/lib/
sudo ln -sf /usr/bin/idlc /opt/cyclonedds/bin/
sudo ln -sf /usr/bin/ddsperf /opt/cyclonedds/bin/
sudo ln -sf /usr/include/dds /opt/cyclonedds/include/

# Install with the dds extra
CYCLONEDDS_HOME=/opt/cyclonedds uv pip install -e '.[dds]'
```

To install all extras including DDS:

```bash
CYCLONEDDS_HOME=/opt/cyclonedds uv sync --extra dds
```

See also: [ROS 2 / DDS R0 interface freeze](../../architecture/ros2-dds-r0-interface-freeze.md) (dual-chain map, frozen nav-path topics/QoS, LCM out of scope).
