# Ubuntu 直接运行版本（v3.10.0）

已在 Ubuntu 22.04.5 x86_64 桌面验证；Ubuntu 24.04 尚未实测。程序是原生 Linux 单文件可执行程序，已包含 Python、Tk、CustomTkinter、NumPy、DBC 和 TRACE32 PyRCL，运行时无需配置 Python 环境。保留点位、线段（原有数据源）、PDC、车位、日志录制/回放及 TCP/IP；Ubuntu 在线硬件选择为 Lauterbach TRACE32 和 TCP/IP。Renesas CS+、ZLG 和 CANoe/Vector 使用工程现有 Windows 驱动，在 Windows 版本中保留。

## 画布操作

鼠标置于车辆画布内，向上滚轮放大、向下滚轮缩小，以鼠标位置为中心。按住左键拖动平移；右键或点击「适应视图」恢复自动取景。手动缩放后，新数据刷新及窗口尺寸变化保留当前比例。v3.9.1 修复了 Ubuntu / XWayland 滚轮无响应。

## 启动

解压 `COLIGEN_USS_UPPER_v3.10.0_Ubuntu_x86_64.tar.gz`，运行其中的可执行文件。若执行权限丢失，右键属性允许执行，或执行：

```bash
chmod +x COLIGEN_USS_UPPER_CAN_v3.10.0_Ubuntu_x86_64
./COLIGEN_USS_UPPER_CAN_v3.10.0_Ubuntu_x86_64
```

在发布目录运行 `bash install-desktop.sh` 会复制至当前用户的 `~/Applications` 并创建桌面和应用菜单快捷方式。已配置的虚拟机可直接双击桌面 **COLIGEN USS UPPER**。配置文件 `can_upper_config.toml` 保留在程序旁边，移动程序时请一起移动。

Ubuntu 基础运行依赖（新机器一次性安装）：

```bash
sudo apt-get install libx11-6 libxext6 libxrender1 libxft2 libfontconfig1 fonts-noto-cjk pulseaudio-utils alsa-utils
```

PDC 使用默认 PulseAudio / PipeWire 输出，缺少 pacat 时使用 ALSA aplay。远档 2 Hz、中档 4 Hz、近档长鸣，与 Windows 共用 WAV 波形。发行程序可直接试听：

```bash
./COLIGEN_USS_UPPER_CAN_v3.10.0_Ubuntu_x86_64 --pdc-sound-test
# 也可运行 bash test-pdc-sound.sh
```

## 车型配置

点击顶部「车型配置」编辑车型尺寸和探头安装参数，侧栏支持车型快速切换，JSON 可在 Windows / Ubuntu 间交换。配置保存在用户目录，升级程序后继续保留。详见随包 VEHICLE_PROFILES.md。

## TRACE32

本机 J6E 环境：`/data/t32` 为 TRACE32 安装位置，`/usr/trace32` 为兼容链接；启动工程位于 `~/T32_Ubuntu_J6E`。仅安装 ARM Linux x86_64、Qt5 图形界面、远程控制工具与 API，完整多平台安装包不需要全部解压。

TRACE32 运行依赖：

```bash
sudo apt-get install libqt5core5a libqt5gui5 libqt5widgets5 libqt5printsupport5 libqt5svg5 qtwayland5 libxcb-xinerama0 libxkbcommon-x11-0 libusb-1.0-0 libncurses5 libtinfo5
```

VMware 的设备菜单中将 PowerDebug USB 连接到 Ubuntu，再使用现有 J6E 启动工程。原工程 `_debug_mcu_j6e.sh` 包含目标复位、JTAG 认证和寄存器初始化，只在需要初始化目标时运行。

上位机默认连接本机 TCP 20000，与 `T32_Ubuntu_J6E/hs.t32` 中的 `RCL=NETTCP` 一致。Windows 默认仍为 20001。可在程序旁的 TOML 中修改：

```toml
[trace32]
host = "127.0.0.1"
port = 20000
probe_scheme = 17
```

也可将 host 改成另一台运行 TRACE32 的主机 IP，并确认端口和防火墙可达。上位机复用已连接会话，不会主动重启正在运行或暂停的目标。读取仍要求 ELF 包含匹配的 `sf_Upper_*OutSignal` 符号。TRACE32 通过 Probe Scheme 明确选择 17 / 20 探头格式；17 探头为 90 点、12 路回波 / PDC、6 个车位槽位且无线段。17 探头 PDC 单位为 cm。TCP/IP 的 17 探头报文模型保持独立。

## TCP/IP 与共享目录

在 Hardware 选择 TCP/IP，打开「网络设置」。默认 UDP 监听 `0.0.0.0:50000`；TCP 为连接 RTE 服务端的客户端。接收五类 512 字节数据包，可显示 90 点、8 车位、PDC 和回波。17 探头数据源没有线段输出。真实设备需要路由可达；设备主动发送 UDP 时建议将 VM 网卡桥接到设备所在网段。

Windows `D:\Cenww_work\share` 对应 Ubuntu `/mnt/hgfs/share`。建议将程序通过桌面安装器复制至本机目录运行，日志与发布包可放共享目录。

## 维护与自检

在 Ubuntu 源码根目录运行 `bash scripts/build_ubuntu.sh` 原生构建；Windows 不能直接交叉构建此包。构建要求 Python 3.10～3.12、python3-venv、python3-tk、binutils，DBC 目录保持工程同级的 CAN_S20/Database，随包 ASC 示例取自同级 CAN_S20/0904_2.asc 的前 3000 行。测试可使用 `xvfb-run -a build/ubuntu-venv/bin/python -m pytest -q`。

发行程序自检会加载主题、字体、DBC、CAN 日志、TRACE32 RCL，并校验 17 探头协议：

```bash
./COLIGEN_USS_UPPER_CAN_v3.10.0_Ubuntu_x86_64 --can-self-test sample-can.asc result.json
```

此自检与离线 TRACE32 模拟验证不能代替 PowerDebug 和目标板的实机读取。现场验证记录请查看发布目录中的 VALIDATION.md。
