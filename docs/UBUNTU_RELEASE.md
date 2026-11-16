# Ubuntu 原生使用与构建

当前版本 4.5.0，提供 Ubuntu 22.04 x86_64 原生单文件程序，与 Windows 同版本发布。

## 从源码使用

安装 Python 3.10～3.12、`python3-tk`、`python3-venv`、`binutils` 与 uv。需要 PDC 提示音时安装可用的 PipeWire/PulseAudio/ALSA 播放工具。

```bash
uv sync --locked
uv run python src/app.py
```

Linux 界面支持 LAUTERBACH TRACE32、TCP/IP、SERIES、REPLAY DEBUG；ASC/BLF 从「打开日志」进入回放。CS+ 和附带的 Windows ZLG/Vector DLL 不用于 Linux。

TRACE32 默认 host 为 `127.0.0.1`、TCP RCL 端口 20000、17 PROBE；实际端口和探头方案须与目标一致。用 `config/ubuntu_config.toml` 作为 Linux 配置模板，发布包内文件名为 `viewer.toml`。串口默认 921600 8N1，访问 `/dev/ttyUSB*` 可能需加入 dialout 组后重新登录。

## 构建包

```bash
bash scripts/build_ubuntu.sh
```

脚本使用 `viewer_linux.spec`，从本项目 `assets/dbc/` 获取 DBC；不依赖外部项目或历史验证报告。输出：

```text
dist/COLIGEN_USS_UPPER_v4.5.0_Ubuntu_x86_64.tar.gz
```

使用 `tar -xzf COLIGEN_USS_UPPER_v4.5.0_Ubuntu_x86_64.tar.gz` 解压，进入不带版本号的 `COLIGEN_USS_UPPER` 目录，再运行其中 `COLIGEN_USS_UPPER_v4.5.0_Ubuntu_x86_64`。可执行 `bash install-desktop.sh` 安装当前用户快捷方式；配置文件 `viewer.toml` 保持在程序旁边。包内不携带历史采集日志，可使用自己的 TXT/ASC/BLF 或从完整 Git 仓库取得示例。

## 验证

```bash
./COLIGEN_USS_UPPER_v4.5.0_Ubuntu_x86_64 --pdc-sound-test
./COLIGEN_USS_UPPER_v4.5.0_Ubuntu_x86_64 --self-test /path/to/sample.asc /tmp/upper-self-test.json
```

音频自检依次播放远、中、近提示。EXE 自检验证解析、界面和打包资源；真实设备连接、声音设备与实车轨迹需在运行环境验证。

车型、探头、串口和硬件设置默认保存在 `~/.config/coligen-uss-upper/`，支持 `COLIGEN_CONFIG_DIR` 隔离。功能操作见项目 [README](../README.md)。

## 下载与包内容

从同版本 GitHub/Gitea Release 或 SVN 当前发布目录下载 `COLIGEN_USS_UPPER_v4.5.0_Ubuntu_x86_64.tar.gz` 和 `SHA256SUMS.txt`。先校验，再解压：

```bash
sha256sum --ignore-missing -c SHA256SUMS.txt
tar -xzf COLIGEN_USS_UPPER_v4.5.0_Ubuntu_x86_64.tar.gz
cd COLIGEN_USS_UPPER
./COLIGEN_USS_UPPER_v4.5.0_Ubuntu_x86_64
```

归档保留 Linux 可执行权限，无需 Python 虚拟环境即可启动。`validation/` 保存发行程序自检、源码回归及现场日志世界坐标回放的验证结果，不携带现场日志原文件。验证通过 SSH 与 Xvfb/X11 在 Ubuntu 22.04.5、Python 3.10.12 上完成。
