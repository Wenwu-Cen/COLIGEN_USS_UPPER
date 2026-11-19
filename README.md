# COLIGEN USS UPPER

超声波上位机，当前版本 **5.2.2**。用于实时采集、日志回放、点线与车位可视化、后轴中心行车轨迹和异常快照对比。

统一启动入口为 `src/app.py`，Windows 程序为 `COLIGEN_USS_UPPER_v5.2.2.exe`。项目及 SVN 外层目录统一为 `COLIGEN_USS_UPPER`，版本记录在程序、变更说明和 Git tag 中。

## 1. 直接使用 Windows 程序

1. 从 GitHub、Gitea 对应版本 Release，或 SVN `Algo/可视化工具/COLIGEN_USS_UPPER` 下载 EXE。
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

- 在 **TCP/IP** 下，将采集协议设为 **XCP**。打开「XCP 设置」，填写 ECU 的 IP 地址或主机名、TCP 端口及地址扩展。端口预填 5555，可按 ECU 配置修改。
- 在 **UDP** 下，将采集协议设为 **XCP**。在「XCP 设置」填写 ECU 的 IP 地址或主机名、UDP 服务端口及地址扩展。端口预填 5555，可按 ECU 配置修改。
- 在 **CAN** 下，将采集协议设为 **XCP**，再选 **ZLG / TOSUN / VECTOR** 的型号、设备及通道。在「XCP 设置」填写 ECU 的请求/响应 CAN ID、CAN/CAN FD 类型、请求帧长度、速率及地址扩展。

使用上述方式时，均需在「XCP 设置」选择与当前固件匹配的 ELF（含无后缀 mca）、GHS/HighTec MAP 或变量地址 JSON，保存后点击「在线连接」。

上位机读取 `LAUTERBACH_UPPER_DEBUG` 原生变量并识别 S20 或 E211 布局。E211 支持 80 点、24 条线、12 路探头和 PDC 功能输出。录制时可导出实车结果，并从支持采集的 E211 固件读取回灌输入快照。XCP on CAN 录制同时导出带录制日期和时间的 ASC。只读顺序轮询可能跨 ECU 周期。ECU 须开启对应传输的 XCP 服务。配置、变量布局和使用步骤见 [XCP 说明](docs/XCP.md)。

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

「开始录制」记录显示的完整帧，停止后保存 TXT，并按保存流程导出前后探头 RAW CSV。TXT 包含点、线、车位、原始数据、车型/安装参数、可用位姿和采样时间，便于再次打开对照。切换源前先停止录制。

顶部显示时间戳、挡位、车速和温度；在线显示电脑当前北京时间，回放显示采样时间。温度原始值编码为 `(℃ + 40) × 2`，在线和回放均按 `原始值 / 2.0 - 40` 显示，保留一位小数；TXT 录制保留原始编码值。无数据或协议未提供的字段需结合数据详情确认。[时间说明](docs/TIME_DISPLAY.md)

S20 部分 CAN ID 在车位与点云/PDC 格式间复用，默认按车位解析；「图层与测距」关闭车位图层后切换到点云/PDC 解析。当前支持附带 DBC 和约定接口，其他项目协议需要适配。

### S20 实车与回灌同周期对比

实车画面由 **RENESAS CS+** 读取。S20 PC 回灌从 **CANFD 或已适配的 UDP** 收集算法输入，两路在同一个录制会话中保存。当前严格对比覆盖点位、线段及其属性。

#### 连接和录制

1. 在实车 ECU 上运行与程序配套、启用 `SUPPORT_REPLAY_COMPARE` 的 S20 固件。在 CS+ 打开对应工程和调试符号，让 ECU 保持运行。在上位机选「RENESAS CS+ → 在线连接」，先确认主画面持续更新。
2. 打开「录制设置」，项目选 `S20`，依赖 ID 配置选 `s20`。依赖 DBC 使用内置的 `assets/dbc/E541_PAS_20260609_FS21.dbc`，也可点「选择 DBC」指定同名文件。
3. 根据实车发出的依赖设置采集入口。
   - **CANFD**：选择实际设备厂商和通道。以 ZLG USBCANFD-200U 单台接线为例，设备索引为 `0`，若接 CAN1 则通道索引为 `0`。先核对速率、终端和接线。
   - **UDP**：填写本机监听 IP、端口和可选的来源 IP，封装按发送端选 `can68` 或 `ussd`。严格对比还要求收到带 S20 周期标识的完整依赖输入。选 `raw` 可以保存未适配的原始数据报。
4. 勾选「启用实时回灌及严格同周期对比」，使用内置 S20 回灌程序，或点「选择程序」指定支持 `--stream` 且握手版本为 2 的 `dataReplay_main.exe`。需要另存位置时设置「自动保存根目录」。可先点「检查连接」观察临时收包结果，再点「保存」。
5. 点「开始录制」。对比窗口左侧为「实车 · CS+」，右侧为「回灌 · S20 PC」。观察「依赖完整周期」「回灌」「同周期配对」是否持续增加。录制结束在主窗口点「停止录制」，等待状态提示保存完成。

#### 查看与复查

- 「冻结画面」保留当前配对供检查，「继续实时」回到实时结果。可以用滑块、「上一周期 / 下一周期」和「播放」检查已保存的配对。「叠加」用粉色在实车图上画出回灌的点线。
- 实车和回灌点线统一使用 X 向前、Y 向左的毫米坐标。旧版 S20 对比会话打开后会按该坐标显示。
- 「点位标注」「线段标注」默认关闭，勾选后两侧同步显示该类对象的坐标和属性。用「字段对照」分别选择两侧的对象查看字段差值，用「标记问题」记录当前配对。
- 会话目录内的 `manifest.json` 保存设备、DBC、算法和计数，`session.db` 保存原始依赖、快照和配对。停止后可查看 `real_vehicle.txt`、`replay.txt`、前后探头 CSV 和 `differences.csv`。「对比 → 选择录制会话目录」或对比窗口内「打开会话」可重新查看。
- 「导出依赖」将 CANFD 或已适配的 UDP CAN 帧导出为 ASC / BLF，原始 UDP 数据报可导出为 JSONL。「新版本重跑」在停止录制后可用，以原始完整输入重跑，输出另存子会话。
- 停止录制后，从对比窗口点「导出对比」保存 `comparison_timeline.csv`。每个严格配对一行，列出输入、实车输出、回灌输出的微秒时间戳、有效点线数量，以及两侧的完整点线坐标和属性（JSON 列）。缺少一侧时保留单侧记录并标记 `real_only` 或 `replay_only`；未取得周期键时对应列留空。旧会话可打开后导出。两侧输出时钟起点可能不同，请以启动号、输入周期、输出序号对齐，不能直接用时间戳相减当作延迟。
- 每组结果使用同一个 **启动号 / 输入周期 / 输出序号** 配对。CS+ 采样频率、两侧输出节奏和录制边界会影响配对数量。PC 以自己的算法初始状态运行，算法版本也可能不同，应逐周期核对差异。

#### 常见问题

- **有实车画面，完整周期为 0**：从「录制设置」检查 CANFD 通道和速率，或 UDP 端口、来源 IP、封装。确认 ECU 在实际发出 S20 回灌输入，ID 配置为 `s20`。
- **完整周期有增长，回灌为 0**：检查回灌程序路径、`--stream` 版本及会话目录内的 `replay.log`。
- **回灌有增长，配对为 0**：确认实车固件带 `sf_Upper_Compare*` 符号和 `SCP2` 快照格式，CS+ 加载的是同一版调试符号。刷写后重新连接上位机，再开始新的会话。
- **中间出现缺帧、异常或 ECU 重启**：停止并保存会话，检查接线或数据源后开启新会话，以免用不连续输入继续算法状态。

更多协议和固件要求见 [S20 录制与回灌说明](docs/S20_REPLAY_RECORDING.md)。

### D4M3 实车与回灌同周期对比

D4M3 实车画面与 E541 回灌依赖共用 UDP：本机 `192.168.98.123:39001`，来源设备 `192.168.98.233`。在「录制设置」选 `D4M3`、`UDP / can68 / legacy`，使用 E541 DBC 和内置 D4M3 回灌程序；如需自定义，可选择支持 RCP1 v2 的 D4M3 worker。勾选实时回灌后开始录制。

停止录制后，「导出依赖 → ASC」将依赖还原为 CAN FD 帧，保留报文 ID 和原始负载；完整 UDP 数据报可另存 JSONL。「导出对比」记录输入和两侧输出的微秒时间戳、点线坐标及属性、PDC 系统状态与各探头结果；D4M3 不提供车位对比。详见 [D4M3 UDP 回灌说明](docs/D4M3_UDP_REPLAY.md)。

## 4. 视图、轨迹和测距

- **跟随车辆**：默认视角，以后轴中心为视图参考，车辆方向固定。
- **固定世界坐标**：首次有效后轴中心为地图原点，车辆随位姿移动/旋转，镜头和网格固定。TXT 回放会一次容纳整段车辆行程，播放时镜头保持不动。
- **显示行车轨迹**：将后轴中心走过的世界位置连成轨迹。关闭开关仅隐藏；「清空行车轨迹」清除历史，后续继续记录。
- **ODO 与转向**：顶栏显示统一为 X 向前、Y 向左的 ODO 坐标（m）和车身航向（°，左转为正）。车图用连续 ODO 表示前轮偏转和胎纹滚动。顶栏的「方向盘模拟」和车图内方向盘均按默认 16:1 转向比换算，即方向盘模拟角 = 前轮估算角 × 16（例如前轮左转 10°，方向盘模拟左转 160°）。两者均来自 ODO，静止或位姿不连续时显示 `—`；没有 ODO 的数据源不显示坐标或航向值。若要提高前轮角估算的准确性，在「车型配置」填写实车轴距。
- **后刹车灯**：在线和回放均按连续车速变化估算；明显减速时，车图两侧尾灯亮红约 250 ms，持续减速会续亮。前进和倒车都按速度大小判断。缺少车速、跳帧或在线数据中断时清除估算；该显示无法确认实际刹车踏板或灯具状态。
- 拖动画布平移，滚轮以鼠标位置为中心缩放；右键或「适应视图」重新取景。
- 可分别开关扇区、PDC、点、线、车位和标注。点位、线段、车位标注默认关闭，连接或切换数据源不自动开启，可在「标注」栏手动打开。开启测距后选择位置，「清除测距」清除标记。
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

设置按用户保存：Windows `%APPDATA%/COLIGEN_USS_UPPER/`；Ubuntu `~/.config/coligen-uss-upper/`。`COLIGEN_CONFIG_DIR` 可隔离车型、探头方案、UDP、串口和硬件设置。数据详情另存显示布局。个人设置无需放入源码或 SVN。

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

输出 `dist/COLIGEN_USS_UPPER_v5.2.2.exe`，使用 `viewer.spec` 和统一入口 `src/app.py`。旧演示入口、CAN 专用启动脚本和闲置 Python ZLG 包已移除。

Ubuntu 需要系统 Tk 库，例如安装 `python3-tk`、`python3-venv` 和可用音频播放器，再执行 `uv sync --locked`、`uv run python src/app.py`。串口可能需加入 `dialout` 组并重新登录。原生打包用 `bash scripts/build_ubuntu.sh`，见 [Ubuntu 说明](docs/UBUNTU_RELEASE.md)。Windows DLL 和 CS+ 不适用于 Linux；Linux 显示 TRACE32、TCP/IP、UDP、SERIES、REPLAY DEBUG，ASC/BLF 仍可通过打开日志回放。

源码回归与 EXE 自检：

```powershell
uv run python -m pytest -q
.\dist\COLIGEN_USS_UPPER_v5.2.2.exe --self-test .\recordings\S20test.asc .\build\self-test.json
```

部分 Windows Tk 环境不支持同一进程反复创建根窗口；若批量 GUI 测试出现 Tcl 图标/主题错误，将相应用例分别在新进程运行。实体收包和实车坐标/轨迹效果需用对应设备及数据验证。

## 8. 维护与发布约定

```text
src/app.py                    唯一入口和数据源选择
src/viewer_controller.py      采集生命周期、回放、录制
src/viewer_models.py           独立数据模型
src/log_parser.py              TXT 解析
src/viewer_canvas.py           地图、轨迹、高光、冻结几何
src/data_details.py            实时字段和点击快照
src/modern_ui.py               统一界面
src/*_source.py                各数据源适配
src/*_transport.py             TRACE32 / CS+ 读取
assets/dbc/                   项目内 DBC
config/                       Windows / Ubuntu 默认配置
firmware/upper_serial/        配套 C 发送和回灌适配
library/                      Windows SDK 运行库
scripts/                      启动、构建、桥接、诊断
tests/                        回归和协议夹具
docs/                         当前专题说明
recordings/                   Git 示例日志（精简源码包不含）
build/、dist/、.venv/          本机生成，不提交
```

详见 [维护说明](docs/PROJECT_DOCUMENTATION.md)。协议名称中的 CAN 保留实际含义，软件整体名称和入口统一为 COLIGEN USS UPPER。

发布时同步 `app_version.py`、`pyproject.toml`、`uv.lock` 和变更说明，创建 `v版本号` tag。GitHub、Gitea 保存源码提交、tag 和 Release。精简源码包包含构建资源和测试代码，省略历史采集日志；需要全部示例日志时使用完整 Git 仓库。

SVN 固定目录只放当前版 **Windows EXE、Ubuntu TAR.GZ、源码 ZIP、README.md、CHANGELOG.md、SHA256SUMS.txt**。不再重复铺开源码树、保存多套 EXE、缓存、虚拟环境或个人采集数据，版本标签位于 `Algo/可视化工具/tags/COLIGEN_USS_UPPER/v版本号`，固定发布目录保留最新版本。旧版通过标签、SVN 历史及 Release 查询。下载后按 `SHA256SUMS.txt` 校验。

[变更说明](CHANGELOG.md) · [受保护源码的 Git 解密差异配置](docs/GIT_DECRYPT_DIFF.md)

S20 CS+ 里程计使用底软原生毫米与右/前轴向，4.4.1 修正了旧版误乘 1000 导致车体驶出画面的错误。打开可识别的旧 CS+ 录制会自动修正绘图位姿，原始字段保留；具体条件见 [世界坐标说明](docs/WORLD_MAP.md)。当前 Windows 与源码版本为 v5.2.2；Ubuntu 原生包保留已验证的 v4.5.0，归档文件名明确标注版本。Ubuntu 解压目录为 `COLIGEN_USS_UPPER`，验证环境为 Ubuntu 22.04 x86_64。

4.5.2 进一步优化“设备与显示”：展开/收起时复用原生控件，保留滚动位置和输入值，收起时跳过隐藏控件的键盘焦点。此前的弹窗与串口响应优化一并保留。改动与回归说明见 [界面响应说明](docs/UI_RESPONSIVENESS.md)。

4.5.3 将主窗口与设置弹窗左上角统一为 `assets/car.png` 图标，Windows 与 Ubuntu 源码使用同一入口。

4.6.1 在固定世界坐标下点击「适应视图」或右键，以当前车身中心取景，预留两侧各四个库位、距车身 1.5m 的参考范围；实际库位仍按输入坐标绘制，镜头在取景后保持固定。

TOSUN（同星 TC1018）支持 CAN1～CAN12 选择，使用同星原生 SDK；S20 新增 UC CAN FD 报文解析详见 [协议说明](docs/S20_UPPER_CAN_V1.md) 与 [硬件配置](docs/CAN_HARDWARE.md)。

TOSUN 和 VECTOR 可选择常见设备型号并联动可用 CAN 通道。ZLG 型号显示对应通道数量，硬件索引由后台检测实际接入设备后提供，可点击「刷新设备」更新。
