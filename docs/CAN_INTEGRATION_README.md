# COLIGEN USS UPPER CAN 集成说明

本文中的原有 CAN 功能基于 20 探头方案。新增 17 探头以太网功能见工程中的以太网接口说明。[17 探头以太网接口](ETHERNET_INTERFACE.md)

**本版专门为 S20 车位可视化制作。** 新总线把 `0x6BA/0x6BB` 等改成车位报文，
与 v3.3.0 的点云/PDC ID 冲突。默认按车位显示。打开「设备与显示」，在「图层与测距」中关闭车位后，冲突 ID
按点云/PDC 解析，可用于调试点线。

本版本把 `ASC/BLF/周立功 CAN → DBC 解码 → 可视化数据模型` 直接接入原界面，
不再依赖 `USS_PC_replay.exe` 或 TCP 中转。

## 直接运行

运行：

```text
dist\COLIGEN_USS_UPPER_CAN_v3.8.2.exe
```

点击「设备与显示」展开 Hardware 下拉框。Port 输入框仅在选择 Lauterbach TRACE32 时显示。

- `Lauterbach TRACE32` 通过 RCL 读取调试器变量。
- `Renesas CS+` 通过 Memory Bridge 读取调试器变量。
- `TCP/IP` 接入 17 探头方案的以太网数据。[网络接入说明](ETHERNET_INTERFACE.md)

- `ZLG-USBCANFD-200U`：实时读取 USBCANFD-200U（默认设备类型 41、设备 0、通道 0、500 kbit/s / 2 Mbit/s）。
- `CANoe/Vector`：通过 `library\vxlapi64.dll`（64 位）读取 CANoe/Vector XL 通道，默认使用 CANoe 通道映射和 CAN FD 500 kbit/s / 2 Mbit/s。同目录的 `vxlapi.dll` 只给 32 位解释器使用。

点击「打开日志」，在文件框里选择 `.asc` 或 `.blf`，按录制时间戳回放。TXT 日志也用这个按钮打开。

## 回放步骤

1. 点击「打开日志」。
2. 选择 ASC 或 BLF 文件。
3. 点击「数据详情」检查各页数据，进度条和倍速可在回放过程中调整。
4. 回放开始后，“在线连接”变为“断开连接”，用来停止回放。再次打开日志可换文件。

回放和周立功在线看图时都可以左键拖动、滚轮缩放。拖动时按像素平移当前画面，没有连接、正在回放或正在在线时都一样；松手后按最新视口整幅重绘。拖动期间暂停报文刷新。参照网格在默认视距下是 0.5 m 细格，整米用更深的实线；放大后细格会再加密。

默认回放文件是相邻 `CAN_S20\0904_2.asc`。回放倍速和循环行为可在 EXE
旁边的 `can_upper_config.toml` 中修改：`speed=0` 表示最快，`speed=1` 表示原始时序。

## 实时周立功 CAN 步骤

1. 安装周立功设备驱动，并确认 ZCANPRO 能识别设备。
2. 接入 USBCANFD-200U 和车辆 CAN FD 总线。
3. 关闭 ZXDoc、ZCANPRO 以及其他可能占用同一设备的 CAN 程序。
4. 展开「设备与显示」，在 Hardware 选择 `ZLG-USBCANFD-200U`。
5. 点击“在线连接”。

在线看图时可以拖动画布、用滚轮缩放。拖动和连续滚动期间不把新报文画到画布上，后台仍继续收包解码，松手或停轮后用最新报文刷新。相同报文不重复解码，也不再因此刷新画面。收包间隙会把界面线程让出来。点云、扇形、PDC 和车位像素没变就不挪图元，有变化时一批画完。

如现场位速率或设备索引不同，修改 EXE 旁边的 `can_upper_config.toml` 后重启。

周立功配置位于 `[can]`：

```toml
[can]
device_type = 41       # USBCANFD-200U
device_index = 0       # 第1块同型号设备；第2块填1
channel = 0            # CAN 1接口填0；CAN 2接口填1
bitrate = 500000       # 仲裁段500 kbit/s
data_bitrate = 2000000 # 数据段2 Mbit/s
resistance = true      # 启用120欧终端电阻
```

索引从 0 开始。只有一块 USBCANFD-200U 时，`device_index` 应保持为 0。当前版本
实时后端初始化物理通道 0，因此现场使用截图中的 CAN 1 接口时，`channel` 保持为 0。

## CANoe/Vector 步骤

1. 确认 CANoe 已安装 Vector XL 驱动并能看到目标通道。
2. 确认工程目录 `library\vxlapi64.dll` 与 CANoe/Vector 驱动版本匹配。当前随工程提供的是 XL API 11.0.14。
3. 展开「设备与显示」，在 Hardware 选择 `CANoe/Vector`，点击「在线连接」。
4. 如果 CANoe 已占用通道，先在 CANoe 中释放该通道，或把配置改为只监听模式：
   `canoe.listen_only = true`。

CANoe 参数在 `can_upper_config.toml` 的 `[canoe]` 节配置：`channel`、`app_name`、
`bitrate`、`data_bitrate`、`fd` 和 `listen_only`。

## DBC 与报文兼容

EXE 内置以下 DBC：

- `M18_Upper_Interface_241113.dbc`
- `ObstacleTrack_M20251104.dbc`

同时支持当前 S20 ID 和第一版录制的 0x740、0x748~0x74A、0x76A~0x779、
0x7E0~0x7F8 别名。点云按 120 点完整组帧。

默认识别冲突 ID 为车位。关闭车位图层后，`0x6BA~0x6BF` 改按 v3.3.0 点云/PDC
解析，可在同一条总线上调试点线。再次打开车位图层即可切回车位解析。

车位报文按固件 Rawdata 组映射到原 DBC：`0x6BA→0x6B6`、`0x6BB→0x6B7`、
`0x6BC→0x743`、`0x6BD→0x6B8`、`0x6CE→0x6B9`、`0x6CF→0x746`。
`recordings/车位.asc` 里左侧后两帧为 `0x6BE/0x6BF`，按同一 DBC 解析。
可用 ASC/BLF 回放该文件验证 SLOT 画布。车位相对自车的前后位移来自 `0x640` CarInfo 的 `VehiclePosition_X/Y/Angle`。

ASC/CAN 与 TXT 日志的坐标转换不同，详见 `docs/COORDINATE_SYSTEMS.md`。
TXT（如 `recordings/泊车3.txt`）保持引入周立功之前的规则；ASC 按当前 DBC 规则显示。

## 源码与构建

- 启动入口：`src/VehUpperDemo_CAN.py`
- CAN 适配器：`src/CanOnlinePort.py`
- 配置：`config/can_upper_config.toml`
- 运行环境定义：`pyproject.toml` + `uv.lock` + `.venv`
- 构建：右键用 PowerShell 运行 `scripts/build_can_upper.ps1`
- 源码运行：右键用 PowerShell 运行 `scripts/run_can_upper.ps1`

首次使用或依赖变更后，在工程根目录执行 `uv sync`；之后用 `uv run python ...`
或上述脚本运行，不需要调用系统 Python。

原 TSD 加密源码保持不变；CAN 集成通过同目录启动层扩展其公开接口。
