# COLIGEN USS UPPER

超声波上位机，当前版本 **4.5.3**。用于实时采集、日志回放、点线与车位可视化、后轴中心行车轨迹和异常快照对比。

统一启动入口为 `src/app.py`，Windows 程序为 `COLIGEN_USS_UPPER_v4.5.3.exe`。项目及 SVN 外层目录统一为 `COLIGEN_USS_UPPER`，版本记录在程序、变更说明和 Git tag 中。

## 1. 直接使用 Windows 程序

1. 从 GitHub、Gitea 对应版本 Release，或 SVN `Algo/可视化工具/COLIGEN_USS_UPPER` 下载 EXE。
2. 双击运行；展开「设备与显示」，选择数据源。英文选项统一大写，串口按界面约定命名为 **SERIES**，回灌快照命名为 **REPLAY DEBUG**。
3. 在线采集先设置设备参数，再点击「在线连接」；离线 TXT / ASC / BLF 点击「打开日志」。
4. 根据项目选择车型、探头方案和显示图层。默认车型仅作显示占位，实车使用前应确认安装参数。
5. 需要检查字段时打开「数据详情」；需要世界地图或轨迹时展开「视角与轨迹」。

支持 Windows x64。EXE 已包含 Python、界面资源、DBC、Vector XL 库和 ZLG SDK 用户态库；连接实体设备仍需安装对应厂商 USB/硬件驱动。单文件程序首次启动解压资源时可能稍慢。

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

安装 ZLG 驱动、连接硬件，选择 `ZLG-USBCANFD`，再设置型号、硬件索引和通道索引。

- 支持 USBCANFD-100U / 200U / 400U / 800U，SDK 类型分别为 42 / 41 / 76 / 59。
- 硬件索引 `0～99`，表示同型号设备的驱动枚举序号。
- 通道索引可选 `0～7`；100U 实际为 0，200U 为 0～1，400U 为 0～3，800U 为 0～7。连接时核对设备实际通道数。
- 仅初始化所选通道；默认仲裁速率 500000 bit/s、数据速率 2000000 bit/s、终端电阻开启，在 `[can]` 修改。

详细操作见 [CAN 硬件说明](docs/CAN_HARDWARE.md)。设备占用、索引错误、驱动未装、波特率或终端不匹配都会导致无法连接或无有效报文。

### CANOE/VECTOR

安装 Vector 驱动并配置 Vector Hardware Configuration 的 `CANoe` 应用通道映射。选择 `CANOE/VECTOR`，再选择 `CAN1～CAN10`；CAN1 对应 SDK 应用通道索引 0，CAN10 对应 9。

应用名、速率、FD 和监听模式在 `[canoe]` 配置。应用名必须与 Vector 通道映射一致；显示名称统一大写不会改动配置中的厂商应用名 `CANoe`。

### TCP/IP

这是独立的 **17 探头**底软以太网协议，不是任意 CAN 转 TCP 报文流。

1. 选择 `TCP/IP`，点击网络设置。
2. `UDP` 模式填写本机监听 IP 和端口；`TCP` 模式填写 RTE 服务端 IP 和端口。默认 UDP `0.0.0.0:50000`。
3. 字节序默认 `LITTLE`、C 结构体对齐默认 8、负载前缀默认 0，必须匹配发送端。
4. 发送端提供标识 1～5 的完整 512 字节包。必要时允许本机防火墙对应端口。

字段布局、对齐和验证方法见 [以太网接口](docs/ETHERNET_INTERFACE.md)。

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

顶部显示时间戳、挡位、车速和温度；在线显示电脑当前北京时间，回放显示采样时间。无数据或协议未提供的字段需结合数据详情确认。[时间说明](docs/TIME_DISPLAY.md)

S20 部分 CAN ID 在车位与点云/PDC 格式间复用，默认按车位解析；「图层与测距」关闭车位图层后切换到点云/PDC 解析。当前支持附带 DBC 和约定接口，其他项目协议需要适配。

## 4. 视图、轨迹和测距

- **跟随车辆**：默认视角，以后轴中心为视图参考，车辆方向固定。
- **固定世界坐标**：首次有效后轴中心为地图原点，车辆随位姿移动/旋转，镜头和网格固定。TXT 回放会一次容纳整段车辆行程，播放时镜头保持不动。
- **显示行车轨迹**：将后轴中心走过的世界位置连成轨迹。关闭开关仅隐藏；「清空行车轨迹」清除历史，后续继续记录。
- 拖动画布平移，滚轮以鼠标位置为中心缩放；右键或「适应视图」重新取景。
- 可分别开关扇区、PDC、点、线、车位和标注。开启测距后选择位置，「清除测距」清除标记。

轨迹需要有效位置与航向，不通过车速积分伪造。缺后轴参数时沿用数据原点即后轴中心的约定，有车型参数时换算后轴中心。跳帧、回退、切换源或明显位姿跳变会按规则断开/重置轨迹。[世界坐标与轨迹](docs/WORLD_MAP.md)、[坐标转换](docs/COORDINATE_SYSTEMS.md)

## 5. 点线高光与点击快照

1. 打开「数据详情」，切换 `POINT` 或 `LINE`。
2. 点击数组元素或其字段：黄色高光对应实时点/线，青色虚线保存点击时的几何位置。
3. 「点击快照」并排显示点击值与实时值，变化字段着色，便于观察坐标、ObjID/cNum、收发探头等异常。
4. 实时元素暂时消失时快照仍保留；再次点击或点击「更新」重新采样，「清除」删除快照。

实时跟踪以数组下标为准，下一帧可能对应其他目标，需结合 ObjID/cNum 判断。世界视角中的冻结几何保留点击时世界位置；不会把所有历史障碍物累积成地图。

## 6. 车型、探头和本机设置

「车型配置」支持车长/车宽、轴距/悬长、数据原点、探头位置/角度/FOV/启用状态，多车型及 JSON 导入导出。「跟随在线 / 日志数据」使用源中的车型，手动选定车型用于指定安装参数。[车型说明](docs/VEHICLE_PROFILES.md)

设置按用户保存：Windows `%APPDATA%/COLIGEN_USS_UPPER/`；Ubuntu `~/.config/coligen-uss-upper/`。`COLIGEN_CONFIG_DIR` 可隔离车型、探头方案、串口和硬件设置。数据详情另存显示布局。个人设置无需放入源码或 SVN。

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

输出 `dist/COLIGEN_USS_UPPER_v4.5.3.exe`，使用 `viewer.spec` 和统一入口 `src/app.py`。旧演示入口、CAN 专用启动脚本和闲置 Python ZLG 包已移除。

Ubuntu 需要系统 Tk 库，例如安装 `python3-tk`、`python3-venv` 和可用音频播放器，再执行 `uv sync --locked`、`uv run python src/app.py`。串口可能需加入 `dialout` 组并重新登录。原生打包用 `bash scripts/build_ubuntu.sh`，见 [Ubuntu 说明](docs/UBUNTU_RELEASE.md)。Windows DLL 和 CS+ 不适用于 Linux；Linux 显示 TRACE32、TCP/IP、SERIES、REPLAY DEBUG，ASC/BLF 仍可通过打开日志回放。

源码回归与 EXE 自检：

```powershell
uv run python -m pytest -q
.\dist\COLIGEN_USS_UPPER_v4.5.3.exe --self-test .\recordings\S20test.asc .\build\self-test.json
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

S20 CS+ 里程计使用底软原生毫米与右/前轴向，4.4.1 修正了旧版误乘 1000 导致车体驶出画面的错误。打开可识别的旧 CS+ 录制会自动修正绘图位姿，原始字段保留；具体条件见 [世界坐标说明](docs/WORLD_MAP.md)。本次发布 Windows 与源码 v4.5.3；Ubuntu 原生包保留已验证的 v4.5.0，归档文件名明确标注版本。Ubuntu 解压目录为 `COLIGEN_USS_UPPER`，验证环境为 Ubuntu 22.04 x86_64。

4.5.2 进一步优化“设备与显示”：展开/收起时复用原生控件，保留滚动位置和输入值，收起时跳过隐藏控件的键盘焦点。此前的弹窗与串口响应优化一并保留。改动与回归说明见 [界面响应说明](docs/UI_RESPONSIVENESS.md)。

4.5.3 将主窗口与设置弹窗左上角统一为 `assets/car.png` 图标，Windows 与 Ubuntu 源码使用同一入口。
