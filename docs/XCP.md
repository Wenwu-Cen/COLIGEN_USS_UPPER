# XCP 变量可视化

XCP 变量可视化支持 TCP/IP、UDP/IP 和 Windows 下的 CAN。已使用模拟 ECU 验证轮询与画面数据。

## 使用

1. 固件开启 LAUTERBACH_UPPER_DEBUG，持续更新下文八类变量。ECU 须启用所选传输的 XCP 服务，并允许 SET_MTA / UPLOAD 读取对应内存。
2. 展开「设备与显示」，选择相应 Hardware，将「采集协议」设为 **XCP**，再打开「XCP 设置」。
   - 使用 **TCP/IP** 时，上位机作为 TCP 客户端连接 ECU。填写 ECU 的 IP 地址或主机名和服务端口，端口预填 5555，按 ECU 实际配置修改。
   - 使用 **UDP/IP** 时，在 Hardware 选择 **UDP**。填写 ECU 的 IP 地址或主机名和 UDP 服务端口，端口预填 5555，按 ECU 实际配置修改。上位机从系统分配的本地端口主动发送命令，并接收来自所选 ECU IP 和端口的响应。
   - 使用 **CAN** 时，选择 **ZLG / TOSUN / VECTOR** 及设备型号、索引和物理通道。填写 ECU 的请求 ID、响应 ID、标准/扩展帧、CAN/CAN FD、BRS、仲裁域/数据域速率及终端电阻。两个 ID 默认留空，须使用同一种标准或扩展帧类型。
3. 按 ECU 配置填写地址扩展，并按需调整命令响应超时与轮询间隔。
4. 选择与**正在运行的固件**匹配的 ELF、GHS MAP 或地址 JSON。GHS 的无后缀 ghs/bin/debug/mca 也是 ELF，可通过“所有文件”选择。“检查变量文件”在后台执行，不连接硬件。重新编译或刷写固件后重新选择匹配文件。
5. 默认点线为 X 前/Y 左；S20 里程计默认毫米、X 右/Y 前。底软约定不同须修改对应选项；里程计约定独立于点线方向。探头安装坐标按这组原生变量的 X 右/Y 前约定转换，PDC 距离保持厘米。
6. 保存后点击“在线连接”。只有接收、校验完八类变量才发布一幅画面，复用车辆、点线方向箭头、RAW/PDC、车位、字段详情、高光快照、固定世界坐标、后轴轨迹和 PDC 静音功能。连接中锁定设备及协议参数，断开后可修改。
7. 可视化录制沿用通用录制功能。XCP 轮询结果不作为 S20 / D4M3 严格同周期比较源；原始 CAN 依赖采集和实时回灌对比仍使用各自已有的配置。

CAN、TCP/IP 和 UDP/IP 的 XCP 设置分别保存在用户配置目录的 xcp.json、xcp_tcp.json 和 xcp_udp.json，均支持 COLIGEN_CONFIG_DIR 隔离。启动时 CAN 默认使用「CANFD」，TCP/IP 默认使用「USS 以太网」，UDP 默认使用「USSD / IPC DBC」。XCP 设置会保留上次保存的参数。

## 变量与原生布局

以下均为 LAUTERBACH_UPPER_DEBUG 导出的**原生内存**，含 C 结构体填充；不能使用 UART USSV 中去掉填充后的字节布局代替。

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

以上仅展示格式，实际文件必须包含八类变量。完整模板为 config/xcp_variables.example.json，模板的零地址不可连接，需替换成匹配固件的真实地址。未提供 A2L 导入、自动从 ECU 下载变量描述或写入/标定操作。

## 轮询与故障行为

使用 CONNECT → SET_MTA → 分段 UPLOAD 顺序读取，正常断开时发送 DISCONNECT。支持 BYTE 地址粒度，并按 ECU 声明的 MAX_CTO 分段。标准 CAN 每次最多上传 7 字节，CAN FD 最多 63 字节，TCP/IP 和 UDP/IP 最多 254 字节。两种以太网传输均使用小端 LEN/CTR 帧头。TCP 按长度从字节流恢复报文边界。一个 UDP 数据报可包含多个完整 XCP 报文，格式不完整的数据报会被丢弃。当前实现支持只读轮询，ECU 拒绝读取时会显示具体错误。

同一 ECU 上应由此实例单独执行 XCP 主站命令。CAN 采集按响应 ID 和帧类型筛选，并忽略发送回显。各传输均跳过事件及 DAQ 包。UDP/IP 根据 ECU 的响应计数器丢弃重复或较旧的响应。命令超时后结束会话，已建立的 UDP 会话会尽力发送 DISCONNECT。重新点击「在线连接」可建立新会话。

八类变量是**顺序轮询**，不保证 ECU 同周期原子快照。读取状态时间戳后，再取其他变量，最后复读状态时间戳；两次不一致时状态栏显示“轮询（跨周期）”。即使时间戳一致，也不能代替 ECU 提供的原子发布机制。画面在所有块完整读取、长度和基础数值检查通过后才更新，错误或不完整数据不会拼入下一幅画面。

轮询间隔是目标最短周期，实际频率取决于数据量、链路负载和 ECU 响应。读取耗时超过间隔时仍按顺序完成轮询。停止操作在后台释放 TCP 连接、UDP 套接字或 CAN 通道；数据过期阈值结合命令超时、轮询间隔和上一帧读取耗时计算，低频轮询不会仅因 UI 刷新间隙提示超时。过期或断开的 PDC 告警停止发声。

## ECU 联调检查

先核对 ECU 的 IP 和 TCP/UDP 端口，或 CAN ID、接线、速率及访问权限，再验证持续采集和断开重连。对照 CS+ / TRACE32 检查原始字段，确认温度、PDC 单位、点线方向、车辆/探头和里程计坐标、左右车位及故障状态。检查完整读取耗时和跨周期提示，最后验证录制回放、PDC 静音与设备掉线。

传输层参考 [ASAM MCD-1 XCP](https://www.asam.net/standards/detail/mcd-1-xcp/) 和 [pyXCP Ethernet 实现](https://github.com/christoph2/pyxcp/blob/master/pyxcp/transport/eth.py)。协议实现参考 [pyXCP 命令与响应定义](https://github.com/christoph2/pyxcp/blob/master/pyxcp/types.py)、[pyXCP 主站命令实现](https://github.com/christoph2/pyxcp/blob/master/pyxcp/master/master.py)；同星收发 ABI 参考 [libTSCAN 官方 SDK](https://github.com/TOSUN-Shanghai/libTSCANDemos/blob/main/include/windwos/libTSCAN.h)。
