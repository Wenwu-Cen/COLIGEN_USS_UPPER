# XCP 变量可视化

录制流程见 [录制与回灌手册](../RECORDING.md#开始录制)。

XCP 变量可视化支持 TCP/IP、UDP/IP 和 Windows 下的 CAN、CAN FD。E211 画面支持轮询和动态 DAQ。

## 使用

1. 固件开启 XCP_UPPER_DEBUG 或 LAUTERBACH_UPPER_DEBUG，持续更新所用项目的显示变量。ECU 须启用所选传输的 XCP 服务，并允许 SET_MTA / UPLOAD 读取对应内存。
2. 展开「设备与显示」，选择相应 Hardware，将「采集协议」设为 **XCP**，再打开「XCP 设置」。
   - 使用 **TCP/IP** 时，上位机作为 TCP 客户端连接 ECU。填写 ECU 的 IP 地址或主机名和服务端口，端口预填 5555，按 ECU 实际配置修改。
   - 使用 **UDP/IP** 时，在 Hardware 选择 **UDP**。填写 ECU 的 IP 地址或主机名和 UDP 服务端口，端口预填 5555，按 ECU 实际配置修改。上位机从系统分配的本地端口主动发送命令，并接收来自所选 ECU IP 和端口的响应。
   - 使用 **CAN** 时，选择 **ZLG / TOSUN / VECTOR** 及设备型号、索引和物理通道。填写 ECU 的请求 ID、响应 ID、标准/扩展帧、CAN/CAN FD、请求帧长度、BRS、仲裁域/数据域速率及终端电阻。两个 ID 默认留空，须使用同一种标准或扩展帧类型。
3. 按 ECU 配置填写地址扩展，并按需调整命令响应超时与轮询间隔。
4. 选择与**正在运行的固件**匹配的 ELF、GHS/HighTec MAP 或地址 JSON。GHS 的无后缀 ghs/bin/debug/mca 也是 ELF，可通过“所有文件”选择。“检查变量文件”在后台执行，不连接硬件。重新编译或刷写固件后重新选择匹配文件。
5. 默认点线为 X 前/Y 左；S20 里程计默认毫米、X 右/Y 前。底软约定不同须修改对应选项；里程计约定独立于点线方向。探头安装坐标按这组原生变量的 X 右/Y 前约定转换，PDC 距离保持厘米。
6. 保存后点击“在线连接”。接收、校验所选模式的显示变量后发布一幅画面，画面按项目显示车辆、点线、RAW/PDC 和字段详情。固件发布车位时也显示车位。连接中锁定设备及协议参数，断开后可修改。
7. 打开「录制设置」，选择「仅采集」或「实时回灌比对」。实车结果使用主窗口当前的 XCP 连接。S20 实时比对可用 CAN FD、TCP/IP 或 UDP/IP 读取固件的冻结结果，回灌输入另选原始 CAN FD 或已适配的 UDP。D4M3 实时比对使用其配套 UDP。

CAN、TCP/IP 和 UDP/IP 的 XCP 设置分别保存在用户配置目录的 xcp.json、xcp_tcp.json 和 xcp_udp.json，均支持 COLIGEN_CONFIG_DIR 隔离。启动时 CAN 默认使用「CANFD」，TCP/IP 默认使用「USS 以太网」，UDP 默认使用「USSD / IPC DBC」。XCP 设置会保留上次保存的参数。

## 经典 CAN 线段显示

XCP on CAN 的经典帧模式仅采集、解析和绘制线段，并显示线段高度、类型、距离和方向等属性。保留车辆状态、ODO、车身尺寸与探头位置，车身信息每 2 秒更新。RAW 回波、PDC、点云和车位变量跳过读取，数据详情仅提供 LINE 页面，PDC 声音停用。

选择 XCP on CAN FD、TCP/IP 或 UDP/IP 时使用完整显示。切换数据源或断开经典 CAN 连接后，图层开关恢复进入线段模式前的设置。新版 E211 的 `sf_Upper_LineOutSignal.line_count` 控制有效线段读取，兼容旧版独立计数和完整数组。经典 CAN 另外每 500 ms 采样 PDC 故障并显示在顶栏，保留仅绘制线段与属性。

## S20 的 CAN FD 设置

S20 Chassis CAN 固件如果启用了 64 字节的 XCP 请求长度检查，在「XCP 设置」中选 CAN FD、标准帧、请求 ID 0x7FE、响应 ID 0x7FF 和 64 字节请求帧。按底软配置核对 BRS 和两段速率。CONNECT、内存读取和 DISCONNECT 请求均补零到所选长度。经典 CAN 使用 8 字节，已有 XCP 配置默认使用 8 字节。

## S20 采集与实时比对

- **仅采集**保存 XCP 显示变量解码出的实车结果，并同步录制所选输入。可以使用旧固件。
- **实时回灌比对**需要启用了 `SUPPORT_REPLAY_COMPARE` 的 S20 固件与配套 ELF、MAP 或变量地址 JSON。变量文件应包含 `sf_Upper_CompareGeneration`、`sf_Upper_CompareLength`、`sf_Upper_CompareBuffer`。比对以冻结结果中的周期键为准。XCP 轮询会采样部分实车周期，完整回灌输入由独立的原始 CAN FD 或 UDP 数据源提供。
- XCP on CAN FD 与原始 CAN FD 输入使用同一设备与通道时，共用该在线通道和 XCP 设置中的总线速率。

## E211 联调与录制

1. 在「设备与显示」选择 VECTOR（VN1640A）或 ZLG（USBCANFD-200U），选中接到 ECU XCP 总线的物理通道，再把「采集协议」设为 **XCP**。
2. 打开「XCP 设置」。E211 的当前编译产物使用标准 CAN 帧、请求 ID **0x580**、响应 ID **0x581**、8 字节请求。地址扩展从 0 开始，仲裁速率按实际接入的 ECU 总线配置填写。VN1640A 如果使用 CANoe 应用映射，通道须与 Vector Hardware Configuration 对应。
3. 在变量文件直接选择与当前运行固件匹配的 `autosaros_r5f.elf`。点击「检查变量文件」，应识别出 **E211** 和 7 类显示变量。已确认 E211 布局为 80 个点、24 条线，单位毫米，线段结构体第 4 字节为填充，没有车位数组。匹配的 HighTec `autosaros_r5f.map` 也可导入。
4. 保存后点击「在线连接」。握手时上位机用 0x580 发送 XCP CONNECT，ECU 用 0x581 返回首字节为 `FF` 的响应。握手成功后，上位机按选定方式采集画面。完整画面包括点线、车身、12 路回波和 PDC 测距。配套固件在 `sf_Upper_PDCOutSignal` 内提供功能字段时（兼容旧版独立 `sf_Upper_PDCFunctionOutSignal`），可在「数据详情 → PDC」查看 PDC 状态、AVM 请求、前后停车请求、前后最小距离、故障和静音。
5. 「录制设置」选项目 **E211** 和「仅采集」，回灌输入选与主窗口一致的 XCP 传输，或选「XCP（跟随在线连接）」。点「开始录制」后可在状态栏查看回灌输入计数。只录实车结果时选择 **none**。

每次录制创建独立会话，实车画面保存在 `real_vehicle.txt`，前后探头数据同时导出 CSV，PDC 功能输出保存在 `e211_pdc_result.csv`。选择任一 **XCP** 回灌输入来源时，`replay_dependency.bin` 按 1800 字节的 `USSXCPOfflineReplayData_t` 保存每份记录，包含运行时间、里程计、车速、温度、挡位、工作模式及 12 路原始传感器输入。`replay_dependency.jsonl` 记录偏移、大小、时间戳、采样编号、跳采数和上位机单调接收时间。SQLite 会话日志也保存采集数据。

使用 **XCP on CAN** 或 **XCP on CAN FD** 采集时，停止录制会生成 `E211_replay_dependency_YYYYMMDD_HHMMSS.asc`，文件名使用录制开始时的日期时间。轮询的 ASC 保存成功快照的 SET_MTA / UPLOAD 收发帧，DAQ 的 ASC 保存组装成功的 DTO 接收帧。JSONL 的 `asc_first_frame` 和 `asc_frame_count` 给出每份记录在 ASC 中的起始帧序号（从 0 开始）和帧数。DAQ 的 ASC 需要按对应 DAQ 配置解释，回灌程序可直接使用按固定 ABI 编码的 BIN。

### 选择采集方式

「XCP 设置」中的「画面采集方式」和「回灌采集方式」可以独立设置。保存后重新在线连接。上位机按所选固件变量文件的布局识别车型。E211 四种 XCP 传输的画面都可选轮询或 DAQ，默认 DAQ。经典 CAN 两种画面模式都保留线段、状态、ODO 和 PDC 故障所需数据。CAN FD、TCP/IP、UDP/IP 的回灌可选轮询或 DAQ，默认 DAQ。经典 CAN 回灌使用轮询。

- **画面轮询**按「轮询周期间隔」发起变量读取。支持使用与固件匹配的 ELF、MAP 或地址 JSON。
- **回灌轮询**需要变量文件包含 `sf_Upper_E211ReplaySequence` 与 `sf_Upper_E211ReplaySlots`。固件快照发布间隔至少 500 ms。调整上位机的轮询间隔只会改变检查频率。
- **回灌 DAQ**需要带调试类型的同版 ELF。经典 CAN 的 8 字节 DTO 无法在现有事件的单列表中容纳整份回灌测量，完整回灌 DAQ 使用 CAN FD 或以太网。
- S20 画面及冻结结果继续按现有轮询接口处理。

### E211 画面 DAQ

- **CAN、CAN FD、TCP/IP、UDP/IP** 共用 E211 显示变量布局。匹配的 ELF、MAP 或地址 JSON 提供变量地址和大小。TCP/IP 与 UDP/IP 还需填写 ECU 对应的服务地址和端口。
- 「画面 DAQ 事件编号」默认 **1**，分频 **1**。E211 当前固件的事件 1 周期为 **100 ms**。点线、PDC、状态和 `sf_Upper_OdoOutSignal` 按此事件采样。车辆尺寸和探头安装位置在连接时读取一次。完整画面的 RAW 每秒读取一次。
- 经典 CAN 的画面 DAQ 保留线段、状态、ODO 和 PDC 故障所需数据。CAN FD 和以太网同时显示点线和 PDC。按 ECU 实际结构体大小配置测量列表，并按结构体内计数或旧版独立计数显示已发布的点线。
- ECU 须支持动态 DAQ 并开放所选事件及所需的 DTO 容量。CAN 和 CAN FD 的 DTO 使用配置的响应 CAN ID。画面状态栏显示 DAQ 事件编号。

### E211 回灌 DAQ

- **CAN FD、TCP/IP、UDP/IP** 的回灌录制使用同版且含 DWARF 调试类型的 ELF。画面与回灌共用一个 XCP 会话。两路都选 DAQ 时各配置一条列表，ECU 须支持两个列表及对应事件。开始和停止回灌 DAQ 录制时，上位机会重新配置列表。若 ECU 拒绝回灌列表，上位机会恢复已选的画面采集方式，并显示回灌错误。
- 「回灌 DAQ 事件编号」默认 **2**，分频 **2**。E211 当前固件的事件 2 周期为 25 ms。支持分频的 ECU 每两次触发采一份，目标间隔 **50 ms**。按对应底软事件配置修改参数。
- 回灌 DAQ 直接采集 `Uss_OsTime_us`、`cAutoDrv_CarCenterPt`、`AsdmPrivateCan_Input_Info` 的车速/温度/挡位字段、探头模式及完整 `sensorData`。
- 上位机只保存从首个 ODT 开始且分片完整的样本。UDP 根据报文计数丢弃重复、乱序或缺片影响的半帧。`source_cycle_kind=daq_sample` 表示索引与 BIN 的 `cnt_u8` 使用上位机 DAQ 样本编号。跳采数根据丢弃分片组和 ECU 时间间隔估计。`daq_receive_ms` 表示上位机收到首末分片的间隔。
- 画面与回灌各按配置事件采样。若要对齐到同一算法周期，ECU 需在输入与输出准备完成时提供对应采样事件及同周期标识。实车刷新率和回灌 50 ms 目标需在实际 ECU 上测量。

## 显示变量接口

实车输出可视化仅依赖 `XCP_UPPER_DEBUG` 或 `LAUTERBACH_UPPER_DEBUG` 发布的 `sf_Upper_*` 变量。E211 两个宏使用同一套接口，地址和大小从匹配的 ELF、MAP 或地址 JSON 获取。上位机顶栏的 ODO 对应 `sf_Upper_OdoOutSignal.odo_x`、`odo_y` 和 `odo_ang`，保留原始 X/Y 轴，按配置将距离显示为米、角度显示为度。地图单独转换到前/左坐标用于绘制。

E211 新版接口将计数并入点线结构，容量直接使用 `USS_INTERNAL_POINT_CAPACITY` 和 `USS_INTERNAL_LINE_CAPACITY`。当前为 80 点、24 条线。上位机根据匹配 ELF/MAP 的变量大小计算容量，不再截断为 80 点或 20 条线。

- `Upper_PointOutSignal` 为 `uint16_t point_count` 和 `point_info[容量]`。条目仍为 10 字节，当前总大小 802 字节。
- `Upper_LineOutSignal` 为 `uint16_t line_count` 和 `line_info[容量]`。条目仍为 14 字节，当前总大小 338 字节。
- `Upper_PDCOutSignal` 的前 52 字节保持状态和 12 个探头距离、等级、故障字段，末尾直接增加四个 uint8（eState、pdcRequestAvm、frontStopReq、rearStopReq）、两个 uint16（frontMinDst、rearMinDst，厘米）、两个 uint8（SnsrFltOfPrkgDstCtrl、PdcMuteBtnSts），合计 62 字节。

顶栏和 PDC 详情显示前后区故障汇总、功能故障/抑制/遮挡及各探头故障。未提供的故障来源显示为“未提供”。AVM 请求当前保持零，STOP 字段为停车显示请求。

旧版 E211 的裸数组、独立 `sf_Upper_GeometryCounts`、独立 `sf_Upper_PDCFunctionOutSignal` 仍可解析。XCP 四种传输和 TRACE32 E211 入口共享原生布局解析。USSV 串口及 CAN FD 封装使用明确数量和可选 tag 10 携带 PDC 功能字段。原有 DBC CAN、IPC UDP 和 17 探头 TCP 协议保持各自线格式，界面接收实际解码的数组数量与已提供的故障字段，不能直接发送原生 C 结构体替代协议编码。

修改结构体后必须重新编译、烧写 E211 固件，并导入同次构建的 ELF。旧固件仍应使用其匹配的旧 ELF。

## 变量与原生布局

以下为 S20 的 LAUTERBACH_UPPER_DEBUG **原生内存**，含 C 结构体填充；不能使用 UART USSV 中去掉填充后的字节布局代替。

- sf_Upper_StatusOutSignal：16 字节，挡位、编码温度、速度、时间戳。
- sf_Upper_OdoOutSignal：12 字节，三个 float。
- sf_Upper_VehicleOutSignal：52 字节，车身尺寸及 12 路探头安装位置。
- sf_Upper_RawDataOutSignal：246 或 248 字节，同频状态与 12 路原始回波；248 字节布局末尾含填充。
- sf_Upper_PDCOutSignal：52 字节，状态及 12 路距离/等级/故障。
- sf_Upper_PointOutSignal：80 项，每项 10 字节，合计 800 字节。
- sf_Upper_LineOutSignal：20 项，每项 14 字节，合计 280 字节，含 cDirect。
- sf_Upper_SlotOutSignal：左右各 3 个车位；支持 4/44 或 8/48 的头部/条目步长，对应 268 或 296 字节。

ELF 从符号表读取地址、大小和字节序，兼容 _sf_Upper_* 名称。GHS MAP 从 address+hex_size _symbol 记录读取，按 RH850 小端 ABI 处理。缺变量、大小不支持、地址重叠和超出 XCP 32 位地址范围均拒绝连接。结构体字段须与本项目 firmware/upper_serial/Lauterbach_Var.h 所描述的原生接口匹配；同一大小不代表任意其他结构体布局可兼容。

地址 JSON 结构为：

    {
      "byte_order": "little",
      "variables": {
        "sf_Upper_StatusOutSignal": {"address": "0x实际地址", "size": 16},
        "sf_Upper_OdoOutSignal": {"address": "0x实际地址", "size": 12}
      }
    }

以上仅展示格式，实际文件必须包含所用项目要求的全部显示变量。完整模板为 config/xcp_variables.example.json，模板的零地址不可连接，需替换成匹配固件的真实地址。未提供 A2L 导入、自动从 ECU 下载变量描述或写入/标定操作。

## 轮询与故障行为

使用 CONNECT → SET_MTA → 分段 UPLOAD 顺序读取，正常断开时发送 DISCONNECT。支持 BYTE 地址粒度，并按 ECU 声明的 MAX_CTO 分段。经典 CAN 每帧最多返回 7 字节。ECU 声明支持从站块上传时，上位机可用一次 UPLOAD 请求连续接收多帧，8 字节 MAX_CTO 下每块最多 252 字节。其他设备仍按单帧请求读取。两种以太网传输均使用小端 LEN/CTR 帧头。TCP 按长度从字节流恢复报文边界。一个 UDP 数据报可包含多个完整 XCP 报文，格式不完整的数据报会被丢弃。ECU 拒绝读命令或 DAQ 配置时显示具体错误。

同一 ECU 上应由此实例单独执行 XCP 主站命令。CAN 采集按响应 ID 和帧类型筛选，并忽略发送回显。E211 会话按 DAQ 列表组装 DTO。S20 轮询跳过事件及 DAQ 包。UDP/IP 根据 ECU 的响应计数器丢弃重复或较旧的响应。S20 CAN 轮询超时会丢弃当前未完成的读取，并通过 SYNCH 与 ECU 重新同步后重读。同步失败或连续超时会显示错误。以太网命令超时后结束会话，已建立的 UDP 会话会尽力发送 DISCONNECT。重新点击「在线连接」可建立新会话。

采用**画面轮询**时，上位机顺序读取显示变量。读取状态时间戳后，再取其他变量，最后复读状态时间戳；两次不一致时状态栏显示“轮询（跨周期）”。即使时间戳一致，也不能代替 ECU 提供的原子发布机制。画面在所有块完整读取、长度和基础数值检查通过后才更新，错误或不完整数据不会拼入下一幅画面。

轮询间隔是目标最短周期，实际频率取决于数据量、链路负载和 ECU 响应。读取耗时超过间隔时仍按顺序完成轮询。停止操作在后台释放 TCP 连接、UDP 套接字或 CAN 通道；数据过期阈值结合命令超时、轮询间隔和上一帧读取耗时计算，低频轮询不会仅因 UI 刷新间隙提示超时。过期或断开的 PDC 告警停止发声。

## ECU 联调检查

先核对 ECU 的 IP 和 TCP/UDP 端口，或 CAN ID、接线、速率及访问权限，再验证持续采集和断开重连。对照 CS+ / TRACE32 检查原始字段，确认温度、PDC 单位、点线方向、车辆/探头和里程计坐标、左右车位及故障状态。检查完整读取耗时和跨周期提示，最后验证录制回放、PDC 静音与设备掉线。

传输层参考 [ASAM MCD-1 XCP](https://www.asam.net/standards/detail/mcd-1-xcp/) 和 [pyXCP Ethernet 实现](https://github.com/christoph2/pyxcp/blob/master/pyxcp/transport/eth.py)。协议实现参考 [pyXCP 命令与响应定义](https://github.com/christoph2/pyxcp/blob/master/pyxcp/types.py)、[pyXCP 主站命令实现](https://github.com/christoph2/pyxcp/blob/master/pyxcp/master/master.py)；同星收发 ABI 参考 [libTSCAN 官方 SDK](https://github.com/TOSUN-Shanghai/libTSCANDemos/blob/main/include/windwos/libTSCAN.h)。
