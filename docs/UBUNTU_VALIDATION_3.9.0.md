# v3.9.0 Ubuntu 验证记录

日期：2026-11-10。环境：ubuntu@192.168.70.129，Ubuntu 22.04.5 LTS / x86_64，内核 6.8.0-106-generic，GNOME Wayland + XWayland，glibc 2.35。

## 已完成

- Windows 共享目录 `D:\Cenww_work\share` 已挂载到 `/mnt/hgfs/share`，可读写。
- 原生 PyInstaller 6.22.3 构建 Linux ELF 单文件程序，包含 Python 3.10.12、Tk、CustomTkinter 6.0.0、NumPy、CAN 解码及 PyRCL。终端用户无需安装 Python。
- Ubuntu 自动化测试：**77 passed, 1 skipped**。跳过项为仅在 Windows 加载的 Vector XL DLL；覆盖 TCP 分片、粘包、重连，UDP 超时，90 点、8 车位、PDC、录制回放、界面与网络设置回归。
- Linux 发行程序自检通过：105,620 帧 ASC，38,048 次解码，120 个点；主题、控件、DBC、RCL 导入和 17 探头协议解析正常。
- 通过真实 GNOME 桌面快捷方式启动发行程序，窗口标题为 v3.9.0，客户区 1440×790，未记录启动异常。程序安装在 `~/Applications/COLIGEN_USS_UPPER_v3.9.0_Ubuntu_x86_64`，桌面快捷方式已信任。
- 发行程序 `--pdc-sound-test` 正常退出，无 stderr；从虚拟机默认音频设备的 monitor 回录实际输出，检测到约 0.50 秒、0.25 秒的脉冲间隔和连续近档声音。退出后无残留 pacat 播放进程。
- TRACE32 R.2026.02.000190766 ARM Linux x86_64 已安装；`t32marm`、Qt5 界面库、`t32rem`、`t32api64.so` 及 J6E 离线认证工具的必需动态库均可解析。
- 安装目录 `~/Applications/TRACE32`，兼容链接 `/data/t32`、`/usr/trace32`；已配置 Lauterbach USB 0897 设备的 plugdev/uaccess 权限。保留现有 `~/T32_Ubuntu_J6E` 工程。
- 使用 TRACE32 离线模拟器（独立测试端口 20010）验证 Qt5 启动、PyRCL TCP、原生 C API 连接/状态读取、t32rem 命令。加载共享 ELF 的符号后，上位机连接函数成功解析 Vehicle / Point / PDC / Slot，并读取 Vehicle 52 字节。
- 日常上位机配置为本机 TRACE32 TCP **20000**，与 J6E 的 `hs.t32` 一致；Windows 默认端口继续为 20001。离线测试会话不会占用日常 20000。

## 实机验证边界

本次 USB 列表仅有 VMware Hub/Mouse 和 Linux Root Hub，未出现 Lauterbach PowerDebug（0897）。因此**尚未完成真实调试器、目标板在线读数验证**。未自动运行 J6E 中包含 reset、JTAG 认证和寄存器写入的完整初始化脚本。

共享 `USS_J6X_Demo.elf` 包含 `sf_Upper_VehicleOutSignal`、`sf_Upper_PointOutSignal`、`sf_Upper_PDCOutSignal`、`sf_Upper_SlotOutSignal`。符号存在和模拟器读数仅证明软件链路可用，不能证明它与目标当前运行固件、探头数量及字段布局一致。原有 TRACE32 路径仍按 20 探头数据模型维护，17 探头 TCP/IP 路径独立。

实际接板时，在 VMware 设备菜单将 PowerDebug USB 连接至 Ubuntu，确认 lsusb 出现 0897，再按现有工程初始化并连接上位机 TCP 20000。真实 RTE 设备的网络报文尚未接入本 VM；现有 TCP/IP 验证使用本机模拟报文。

证据 JSON 与 Ubuntu 音频回录位于发布包的 `validation/` 目录。已验证平台为 Ubuntu 22.04.5；Ubuntu 24.04 尚未实测。
