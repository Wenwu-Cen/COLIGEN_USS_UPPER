# COLIGEN USS UPPER

超声波上位机，当前版本 **5.2.8**。用于实时采集、日志回放、点线与车位可视化、后轴中心行车轨迹和异常快照对比。

统一启动入口为 `src/app.py`，Windows 程序为 `COLIGEN_USS_UPPER_v5.2.8.exe`。

## 从这里开始

- **第一次使用**：[下载和启动 EXE](#1-直接使用-windows-程序)。按实车接口查 [数据源与连接操作](#2-数据源与连接操作)。
- **采集或回灌比对**：[录制与回灌](#录制与回灌)。这里集中列出 S20、D4M3、E211 的模式、输入来源和输出文件。
- **回看日志和定位问题**：[日志与时间](#3-日志回放录制与时间) · [视图和轨迹](#4-视图轨迹和测距) · [点线快照](#5-点线高光与点击快照) · [常见问题](#9-常见问题)。
- **修改源码或发布**：[源码运行和构建](#7-源码运行与构建) · [维护手册](docs/PROJECT_DOCUMENTATION.md) · [版本变更](docs/CHANGELOG.md)。

## 1. 直接使用 Windows 程序

1. 从 Gitea 的 v5.2.8 Release、内网 SVN `Algo/可视化工具/COLIGEN_USS_UPPER` 或 [GitHub Release](https://github.com/Wenwu-Cen/COLIGEN_USS_UPPER/releases/tag/v5.2.8) 下载 EXE 和 `SHA256SUMS.txt`。
2. 双击运行；「设备与显示」默认展开，可点击「收起设置」折叠；选择数据源；CAN 设备先选 **CAN**，再选 **ZLG / TOSUN / VECTOR** 及对应通道。英文选项统一大写，串口按界面约定命名为 **SERIES**，回灌快照命名为 **REPLAY DEBUG**。
3. 在线采集先设置设备参数，再点击「在线连接」；离线 TXT / ASC / BLF 点击「打开日志」。
4. 根据项目选择车型、探头方案和显示图层。默认车型仅作显示占位，实车使用前应确认安装参数。
5. 需要检查字段时打开「数据详情」；需要世界地图或轨迹时展开「视角与轨迹」。

支持 Windows x64。EXE 已包含 Python、界面资源、DBC、Vector XL、ZLG SDK 和同星 libTSCAN 用户态库；连接实体设备仍需安装对应厂商 USB/硬件驱动。单文件程序首次启动解压资源时可能稍慢。

如需修改 TOML 参数，将源码包中的 `config/viewer.toml` 复制到 EXE 同目录，文件名保持 `viewer.toml`。未放置该文件时使用程序内置默认值。界面保存的用户硬件、串口和车型选择优先于初始默认值。

## 2. 数据源与连接操作

### LAUTERBACH TRACE32

1. 启动 TRACE32，加载带调试符号的目标程序并连接目标。
2. 在 TRACE32 配置中启用 NETTCP RCL；Windows 默认端口 `20001`，Ubuntu 默认 `20000`。远程目标通过 TOML 的 `[trace32] host` 配置。
3. 选择 `LAUTERBACH TRACE32`，填写 RCL 端口，选择与固件一致的 `17 PROBE` 或 `20 PROBE`，再连接。
4. 固件需提供对应的 `sf_Upper_*` 调试变量；符号不匹配时，按状态区错误检查 ELF、目标运行状态、端口和探头方案。

17 探头接口没有线段输出，不能通过切换显示图层补出线段。17/20 是解码方案，与车型安装参数独立。

### RENESAS CS+

1. 在 Windows 上启动 CS+，打开目标工程并连接调试器，保留一个需要连接的 CS+ 实例。
2. 选择 `RENESAS CS+` 后连接。上位机会自动启动 CS+ 远程服务和内存桥，端口输入框不用于该数据源。
3. 首次使用若提示远程接口未启用，在 CS+ Python Console 的启动设置中启用远程连接后重试。CS+ 中的 `debugger` API 由 IDE 提供，不能把桥脚本当普通 CPython 程序执行。
4. 状态栏显示完整采集频率、耗时和数据新鲜度；断点或读取变慢时观察等待/滞后提示。点、线、车位由一轮完整快照发布。

### ZLG-USBCANFD

安装 ZLG 驱动、连接硬件，选择 `CAN → ZLG`，再设置型号、硬件索引和通道索引。

- 支持 USBCANFD-100U / 200U / 400U / 800U，SDK 类型分别为 42 / 41 / 76 / 59。
- 硬件索引只列出实际检测到的同型号设备，单台通常为 `0`；连接设备后可点击「刷新设备」。
- 通道索引按型号和设备实际通道数显示：100U 为 `0`，200U 为 `0～1`，400U 为 `0～3`，800U 为 `0～7`。
- 仅初始化所选通道；默认仲裁速率 500000 bit/s、数据速率 2000000 bit/s、终端电阻开启，在 `[can]` 修改。

详细操作见 [CAN 硬件说明](docs/CAN_HARDWARE.md)。设备占用、索引错误、驱动未装、波特率或终端不匹配都会导致无法连接或无有效报文。

### VECTOR

安装 Vector 驱动，选择 `CAN → VECTOR`、设备型号及对应 CAN 通道。具体型号按驱动检测的 CAN 接口连接；旧配置可选择 `CANoe 应用映射`，使用 Vector Hardware Configuration 的 `CANoe` 应用通道 CAN1～CAN10。

应用名、速率、FD 和监听模式在 `[canoe]` 配置。应用名必须与 Vector 通道映射一致；显示名称统一大写不会改动配置中的厂商应用名 `CANoe`。

### XCP

在「设备与显示」选择 **CAN、TCP/IP 或 UDP**，将「采集协议」设为 **XCP**。进入「XCP 设置」，按 ECU 配置填写请求/响应 CAN ID 或 IP 和服务端口，导入与运行固件匹配的 ELF、MAP 或变量地址 JSON，保存后点击「在线连接」。

CAN FD 请求长度、地址扩展、符号布局和 E211 固件要求见 [XCP 连接与变量说明](docs/XCP.md)。录制和比对见下方 [录制与回灌](#录制与回灌)。

### TCP/IP 下的 USS 以太网

USS 以太网为 TCP/IP 下默认的 **17 探头**底软协议。

1. 选择「TCP/IP」→「USS 以太网」，点击「网络设置」。
2. `UDP` 模式填写本机监听 IP 和端口；`TCP` 模式填写 RTE 服务端 IP 和端口。默认 UDP `0.0.0.0:50000`。
3. 字节序默认 `LITTLE`、C 结构体对齐默认 8、负载前缀默认 0，必须匹配发送端。
4. 发送端提供标识 1～5 的完整 512 字节包。必要时允许本机防火墙对应端口。

字段布局、对齐和验证方法见 [以太网接口](docs/ETHERNET_INTERFACE.md)。

### UDP（USSD / IPC DBC）

在「UDP」下将采集协议设为「USSD / IPC DBC」，点击「UDP 设置」填写本机监听 IP、端口和接收来源设备 IP，保存后再在线连接。默认监听 `192.168.98.123:39001`，仅接收设备 `192.168.98.233` 主动发送的数据；监听 IP 可填 `0.0.0.0`，端口范围为 `1..65535`。不发送启动指令或心跳。

未保存界面设置时，默认值取自 `config/viewer.toml`（Ubuntu 为 `config/ubuntu_config.toml`）的 `[udp]`。保存到用户配置目录后，重启继续使用；侧栏直接修改端口仅在本次运行保留。UDP 与 TRACE32 分别保留端口。

使用内置 IPC DBC 和 USSD v1 协议（16 字节包头 + 64 字节 CAN FD 数据），收齐 27 包后更新 80 点、20 线、状态、里程计、12 路回波和 PDC。支持数据详情、点线快照、PDC 声音、TXT / CSV 录制和 TXT 回放，保留设备微秒时间戳、点 ID 和线段编号。无车位信号，车身与探头沿用当前车型配置；2 秒无完整周期时显示「等待数据」。

顶栏显示当前 UDP 完整周期的 ODO X、Y（m）和航向（°），方向与车图统一为 X 向前、Y 向左。

UDP 的「原始数据」按报文索引显示。0–5 为 RRS 到 RLS，6–11 为 FRS 到 FLS，包含直波和左右交叉回波的峰值与宽度。

此接口从 V3.5 移植，与 `TCP/IP` 的 17 探头 512 字节协议分别配置。[UDP 协议与配置](docs/UDP_INTERFACE.md)

### SERIES（串口）

1. 接好 UART 转 USB，关闭占用同一串口的其他工具。
2. 选择 `SERIES`，点击串口配置，刷新或输入端口，如 `COM3`；Ubuntu 如 `/dev/ttyUSB0`。
3. 推荐 `921600、8N1`，默认数据超时 1 秒。波特率、校验位和停止位需与底软一致。
4. 输入坐标默认 X 前/Y 左；发送端明确使用 Y 右正时才选择相应转换。
5. 连接后接收 **USSV / UPPER v1 二进制完整帧**。接收端校验长度、TLV 和 CRC32，普通串口打印文本不能直接解析成点云。

配套 C 代码在 `firmware/upper_serial/`。实车已有 `Lauterbach_Var.*` 时沿用其变量定义，编译 `UpperSerialDebug.c`、`UpperSerialVariables.c`，在 `sfType.h` 开启 `LAUTERBACH_UPPER_DEBUG`，注册 `UpperSerialDebug_SetWriter(writer, context)`，在一轮 `OutputSignalRead_*` 完成后调用 `UpperSerialDebug_SendVariables()`。

回调 `int writer(const uint8_t *data, uint16_t size, void *context)` 对接域控底软 UART/DMA 队列，成功返回 0；必须在返回前复制或接管整帧。`UpperSerialReplay.*` 仅用于 PC 回灌。详见 [串口协议及移植](docs/SERIAL_PROTOCOL.md)、[C 端说明](firmware/upper_serial/README.md)。

### REPLAY DEBUG（PC 回灌单步）

此模式读取回灌程序持续更新的 USSV/CRC32 最新快照，不是 ASC/BLF 文件播放。

- 从配套回灌工程启动单步调试时，通过 `REPLAY_UPPER_SNAPSHOT` 指定快照文件并自动连接。
- 手动使用时选择 `REPLAY DEBUG`，点击连接并选择 `.bin` 快照。
- 断点停住时保留最后完整帧，显示「暂停 / 等待下一步」；继续运行后接收新完整帧。
- 文件临时不存在、写入未完成或 CRC 错误时保留上一个有效画面并重试。此模式不播放实时 PDC 提示音。

详见 [回灌单步说明](docs/REPLAY_DEBUG.md)。

## 3. 日志回放、录制与时间

「打开日志」支持 TXT、ASC、BLF。ASC/BLF 自动进入报文回放，可播放/暂停、调倍率和拖动进度；TXT 支持逐帧、首尾跳转和播放。日志采样时间优先保留；没有绝对日期时显示相对时间，不推测日期。

顶部显示时间戳、挡位、车速和温度；在线显示电脑当前北京时间，回放显示采样时间。温度原始值编码为 `(℃ + 40) × 2`，在线和回放均按 `原始值 / 2.0 - 40` 显示，保留一位小数；TXT 录制保留原始编码值。无数据或协议未提供的字段需结合数据详情确认。[时间说明](docs/TIME_DISPLAY.md)

S20 部分 CAN ID 在车位与点云/PDC 格式间复用，默认按车位解析；「图层与测距」关闭车位图层后切换到点云/PDC 解析。当前支持附带 DBC 和约定接口，其他项目协议需要适配。

### 录制与回灌

1. 先在主窗口连接实车结果源，确认画面持续更新。
2. 打开「录制设置」，选择项目和回灌输入来源。选 ZLG、TOSUN 或 Vector 时只显示对应设备和通道。选 UDP 时填写监听 IP、端口、来源 IP 和封装。XCP 使用主窗口的在线连接。
3. 选择录制模式，点「保存」和「开始录制」。对比前可点「检查连接」，确认硬件或端口可用。
4. 结束后点「停止录制」。会话默认位于程序目录的 `recordings/sessions`，也可在录制设置中指定保存根目录。

#### 录制模式和输出

- **仅采集**同步保存实车结果和所选输入。实车输出为 `real_vehicle.txt` 和前后探头 CSV。原始 CAN 输入自动导出 ASC，UDP 输入自动导出 JSONL。依赖来源选 `none` 可单独保存实车结果。
- **实时回灌比对**为 S20 和 D4M3 启动支持 `--stream` 的 RCP1 v2 回灌程序，按启动号、输入周期和输出序号配对。会话同时保存 `replay.txt`、回灌探头 CSV 和 `differences.csv`。
- `session.db` 保存采集数据，`manifest.json` 记录设置和计数。停止后可从「对比」重新打开会话，导出原始依赖或 `comparison_timeline.csv`。对比窗口支持叠加、逐周期播放、字段对照、问题标记及使用新版本程序重跑完整输入。

#### 按项目设置

- **S20**：实车选 CS+ 或 XCP on CAN FD / TCP/IP / UDP/IP，回灌输入选原始 CAN FD 或已适配的 UDP，依赖 ID 选 `s20`。实时比对需要启用 `SUPPORT_REPLAY_COMPARE` 的固件；通过 XCP 比对时导入带 `sf_Upper_Compare*` 的变量文件。[S20 依赖、固件与排查](docs/S20_REPLAY_RECORDING.md)
- **D4M3**：实时比对使用 UDP 实车结果和 `UDP / can68 / legacy` 回灌输入。仅采集还支持原始 CAN FD 和其他 UDP 封装。[D4M3 网卡、端口与协议设置](docs/D4M3_UDP_REPLAY.md)
- **E211**：在线连接 XCP，选择「仅采集」。固件发布回灌输入快照时，依赖选对应的 XCP 传输或「XCP（跟随在线连接）」，另存 `replay_dependency.bin`、周期索引 JSONL 和 PDC 结果 CSV。CAN/CAN FD 链路还会导出 XCP 收发帧 ASC。[E211 符号与导出格式](docs/XCP.md#e211-联调与录制)

## 4. 视图、轨迹和测距

- **跟随车辆**：默认视角，以后轴中心为视图参考，车辆方向固定。
- **固定世界坐标**：默认以首个有效后轴中心为原点，也可选择停车场内的墙角或车位角点。车辆随位姿移动和旋转，网格保持固定。默认以 **100 m × 100 m** 方框查看地图；TXT 行程能放入方框时以整段行程居中，较长的行程可拖动查看。播放时镜头保持不动。连续采集时识别设备 ODO 回零并接续地图位置和航向；整次采集观测到的点、线和车位按世界坐标保留。历史点线以可辨认的灰蓝色显示，已记录的车位轮廓保持在地图原位。TXT 跳帧后会恢复截至目标帧的地图历史。
- **显示行车轨迹**：将后轴中心走过的世界位置连成轨迹。关闭开关仅隐藏；「清空行车轨迹」清除历史，后续继续记录。
- **ODO 与转向**：顶栏显示统一为 X 向前、Y 向左的 ODO 坐标（m）和车身航向（°，左转为正）。车图用连续 ODO 表示前轮偏转和胎纹滚动。顶栏的「方向盘模拟」和车图内方向盘均按默认 16:1 转向比换算，即方向盘模拟角 = 前轮估算角 × 16（例如前轮左转 10°，方向盘模拟左转 160°）。两者均来自 ODO；短暂掉帧或单次估算为零时保留上一轮向，之后平滑过渡。没有有效 ODO 时坐标和航向显示 `—`。若要提高前轮角估算的准确性，在「车型配置」填写实车轴距。
- **后刹车灯**：在线和回放均按连续车速变化估算；明显减速时，车图两侧尾灯亮红约 250 ms，持续减速会续亮。前进和倒车都按速度大小判断。缺少车速、跳帧或在线数据中断时清除估算；该显示无法确认实际刹车踏板或灯具状态。
- 拖动画布平移，滚轮以鼠标位置为中心缩放。在固定世界坐标下点「100 m × 100 m」「适应视图」或在画布右键，重新以当前车身居中；点「近车位」可查看近处点线与库位。
- 可分别开关扇区、PDC、点、线、车位和标注。点位、线段、车位标注默认关闭，连接或切换数据源不自动开启，可在「标注」栏手动打开。在固定世界坐标下，点线和车位标注及测距都使用选定地图原点。点击「导出地图」生成覆盖整张地图的 SVG 和 CSV。
- 「设备与显示」下方「标注」栏内的「PDC 静音」可立即关闭警报声，静音时显示「PDC 已静音」，再次点击恢复。在线采集与日志播放共用开关，切换数据源时保持当前选择；每次启动默认开启声音。静音期间 PDC 图形、数据和录制继续更新。

轨迹需要有效位置与航向，不通过车速积分伪造。缺后轴参数时沿用数据原点即后轴中心的约定，有车型参数时换算后轴中心。跳帧、回退、切换源或明显位姿跳变会按规则断开/重置轨迹。[世界坐标与轨迹](docs/WORLD_MAP.md)、[坐标转换](docs/COORDINATE_SYSTEMS.md)

## 5. 点线高光与点击快照

1. 打开「数据详情」，切换 `POINT` 或 `LINE`。
2. 点击数组元素或其字段：黄色高光对应实时点/线，青色虚线保存点击时的几何位置。
3. 「点击快照」并排显示点击值与实时值，变化字段着色，便于观察坐标、ObjID/cNum、收发探头等异常。
4. 实时元素暂时消失时快照仍保留；再次点击或点击「更新」重新采样，「清除」删除快照。

实时跟踪以数组下标为准，下一帧可能对应其他目标，需结合 ObjID/cNum 判断。世界视角中的冻结几何保留点击时世界位置；不会把所有历史障碍物累积成地图。

## 6. 车型、探头和本机设置

「车型配置」支持车长/车宽、轴距/悬长、数据原点、探头位置/角度/FOV/启用状态，多车型及 JSON 导入导出。「跟随在线 / 日志数据」使用源中的车型，手动选定车型用于指定安装参数。[车型说明](docs/VEHICLE_PROFILES.md)

Windows 设置位于 `%APPDATA%/COLIGEN_USS_UPPER/`，Ubuntu 设置位于 `$XDG_CONFIG_HOME/coligen-uss-upper/`，未设 XDG 路径时使用 `~/.config/coligen-uss-upper/`。`COLIGEN_CONFIG_DIR` 可隔离车型、网络、串口、硬件和数据详情布局。用户目录还保存 `more_panel_state.json`，记录详情面板的可见性与树节点展开状态。已有的源码目录布局文件会在用户目录尚无布局时读取，并在下次保存时写入用户目录。

## 7. 源码运行与构建

需要 Python 3.10～3.12（推荐 3.12 x64）和 `uv`。源码包含 DBC、静态资源和 Windows 用户态运行库，不依赖同级外部项目。

在项目根目录打开 PowerShell：

```powershell
uv sync --locked
.\scripts\run_viewer.ps1
# 或直接运行，可选传入 TXT / ASC / BLF 路径
uv run python src/app.py "D:\logs\sample.asc"
```

Windows 构建：

```powershell
.\scripts\check_runtime.ps1
.\scripts\build_windows.ps1
```

输出 `dist/COLIGEN_USS_UPPER_v5.2.8.exe`，打包配置位于 `scripts/pyinstaller/windows.spec`。如需内置回灌程序，构建前将匹配的 Windows worker 和清单放到对应的 `build/*-stream/bin/` 目录。也可在界面指定独立 worker。详见[维护说明](docs/PROJECT_DOCUMENTATION.md)。

Ubuntu 需要系统 Tk 库，例如安装 `python3-tk`、`python3-venv` 和可用音频播放器，再执行 `uv sync --locked`、`uv run python src/app.py`。串口可能需加入 `dialout` 组并重新登录。原生打包用 `bash scripts/build_ubuntu.sh`，见 [Ubuntu 说明](docs/UBUNTU_RELEASE.md)。Windows DLL 和 CS+ 不适用于 Linux；Linux 显示 TRACE32、TCP/IP、UDP、SERIES、REPLAY DEBUG，ASC/BLF 仍可通过打开日志回放。

源码回归与 EXE 自检：

```powershell
uv run --locked python -m pytest -q
$sample = "D:\logs\S20test.asc"
$test = Start-Process -FilePath .\dist\COLIGEN_USS_UPPER_v5.2.8.exe `
    -ArgumentList "--self-test `"$sample`" `"$PWD\build\self-test.json`"" -Wait -PassThru
$test.ExitCode
Get-Content .\build\self-test.json
```

部分 Windows Tk 环境不支持同一进程反复创建根窗口；若批量 GUI 测试出现 Tcl 图标/主题错误，将相应用例分别在新进程运行。实体收包和实车坐标/轨迹效果需用对应设备及数据验证。

## 8. 目录与发布

```text
README.md              使用、联调与维护入口
pyproject.toml         Python 版本、依赖与测试配置
uv.lock                固定依赖版本
assets/                图标和 DBC
config/                Windows、Ubuntu 与 XCP 配置模板
src/                   上位机代码，统一入口为 src/app.py
firmware/              CAN、串口和回灌采集的 C 端适配
library/               Windows 厂商运行库及配套资源
scripts/               构建、诊断、回灌验证和 PyInstaller 配置
tests/                 回归用例与小型协议夹具
docs/                  专题说明、维护与变更记录
```

开发生成的 `.venv/`、`build/` 和 `dist/` 已加入忽略规则。录制设置中的「自动保存根目录」可指定项目外的目录。历史示例日志可从 v5.2.6 及更早标签取回。下例将 EXE 自检样本解到项目外。

```powershell
$sampleDir = Join-Path (Get-Item ..).FullName 'upper-test-data'
$sampleZip = Join-Path $sampleDir 's20test.zip'
New-Item -ItemType Directory -Force $sampleDir | Out-Null
git archive --format=zip --output=$sampleZip v5.2.6 recordings/
Expand-Archive -LiteralPath $sampleZip -DestinationPath $sampleDir -Force
$env:COLIGEN_TEST_RECORDINGS = Join-Path $sampleDir 'recordings'
```

GitHub 和 Gitea 发布源码提交、`v版本号` 标签及 Release 附件。SVN 固定发布目录提供当前 Windows EXE、源码 ZIP、README、变更记录、校验清单，以及文件名标明版本的 Ubuntu 原生包和 S20 回灌 worker。SVN 历史快照位于 `Algo/可视化工具/tags/COLIGEN_USS_UPPER/v版本号`。已发布的 Ubuntu 原生包为 **v4.5.0**，新版本源码可按上文流程构建 Ubuntu 包。

下载后用 `Get-FileHash .\COLIGEN_USS_UPPER_v5.2.8.exe -Algorithm SHA256` 计算校验值，与 `SHA256SUMS.txt` 的对应项比较。模块职责、打包输入和发布检查见[维护说明](docs/PROJECT_DOCUMENTATION.md)。[变更日志](docs/CHANGELOG.md) · [Git 解密差异配置](docs/GIT_DECRYPT_DIFF.md)

## 9. 常见问题

- **设备可选但收不到数据**。按对应章节检查通道索引、速率、端口绑定、来源 IP 和接线。UDP 与 USS 以太网分别使用各自的协议和设置。
- **实车和回灌都在刷新，同周期配对数为零**。先看「依赖完整周期」是否增加，再核对项目、依赖 ID、发送端周期标识和 worker 握手版本。[S20 录制](docs/S20_REPLAY_RECORDING.md) · [D4M3 回灌](docs/D4M3_UDP_REPLAY.md)
- **车体或点线位置异常**。先检查车型原点、后轴参数及发送端坐标。程序识别到旧版 S20 CS+ 录制时会按兼容规则修正绘图位姿，原始字段可在详情里核对。[坐标转换](docs/COORDINATE_SYSTEMS.md) · [世界地图](docs/WORLD_MAP.md)
