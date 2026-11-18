# XCP 变量可视化（待实车验证）

本功能为 v4.9.0 新增的 Windows 预览功能。已进行模拟 ECU、SDK ABI、变量文件解析和界面检查；ZLG、TOSUN、VECTOR 的 XCP 实体收发、底软资源访问、采集频率与实车画面尚待现场验证。设备下拉、XCP 设置及采集状态均保留“待实车验证”标识。

## 使用

1. 固件开启 LAUTERBACH_UPPER_DEBUG，持续更新下文八类变量；底软须已启用 XCP-on-CAN 服务，并允许 SET_MTA / UPLOAD 读取对应内存。本次只添加上位机功能。
2. 展开“设备与显示”，Hardware 选 **CAN**，采集协议选 **XCP（待实车验证）**，设备选 **ZLG / TOSUN / VECTOR**，设置该设备的型号、硬件索引和物理 CAN 通道。型号及通道沿用现有 CAN 配置。
3. 打开“XCP 设置”，填写 ECU 配置的请求 ID、响应 ID、标准/扩展帧、CAN/CAN FD、BRS、仲裁域/数据域速率、终端电阻和地址扩展。ID 默认留空，必须按 ECU 实际配置填写；两个 ID 使用同一种标准/扩展帧类型。
4. 选择与**正在运行的固件**匹配的 ELF、GHS MAP 或地址 JSON。GHS 的无后缀 ghs/bin/debug/mca 也是 ELF，可通过“所有文件”选择。“检查变量文件”在后台执行，不连接硬件。重新编译或刷写固件后重新选择匹配文件。
5. 默认点线为 X 前/Y 左；S20 里程计默认毫米、X 右/Y 前。底软约定不同须修改对应选项；里程计约定独立于点线方向。探头安装坐标按这组原生变量的 X 右/Y 前约定转换，PDC 距离保持厘米。
6. 保存后点击“在线连接”。只有接收、校验完八类变量才发布一幅画面，复用车辆、点线方向箭头、RAW/PDC、车位、字段详情、高光快照、固定世界坐标、后轴轨迹和 PDC 静音功能。连接中锁定设备及协议参数，断开后可修改。
7. 可视化录制沿用通用录制功能。XCP 轮询结果不作为 S20 / D4M3 严格同周期比较源；原始 CAN 依赖采集和实时回灌对比仍使用各自已有的配置。

XCP 设置保存在用户配置目录的 xcp.json，支持 COLIGEN_CONFIG_DIR 隔离。启动时采集协议默认仍为“CAN 报文”，XCP 设置保留上次保存的参数。

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

第一版使用 CONNECT → SET_MTA → 分段 UPLOAD 顺序读取，正常断开时发送 DISCONNECT。支持 BYTE 地址粒度和 ECU 声明的 MAX_CTO；标准 CAN 每次最多上传 7 字节，CAN FD 根据 MAX_CTO 分段，均处理帧尾填充。WORD/DWORD 地址粒度、DAQ 配置及采样列表、Seed/Key 解锁暂不提供。被 ECU 拒绝的读取会显示具体错误。

总线须由此实例单独执行 XCP 主站命令，避免其他主站的响应与当前读操作混合。非目标响应 ID、帧类型不符、发送回显、事件及 DAQ 包不会被当作读取结果。命令超时后整条会话停止，不重试该命令，以免晚到响应被当作另一个地址的内容；重新连接可建立新会话。

八类变量是**顺序轮询**，不保证 ECU 同周期原子快照。读取状态时间戳后，再取其他变量，最后复读状态时间戳；两次不一致时状态栏显示“轮询（跨周期）”。即使时间戳一致，也不能代替 ECU 提供的原子发布机制。画面在所有块完整读取、长度和基础数值检查通过后才更新，错误或不完整数据不会拼入下一幅画面。

轮询间隔是目标最短周期，实际频率取决于数据量、CAN 负载和 ECU 响应；大于该间隔的读取耗时不会触发并发读。停止在后台结束，释放本实例所打开的物理通道；数据过期阈值结合命令超时、轮询间隔和上一帧读取耗时计算，低频轮询不会仅因 UI 刷新间隙提示超时。过期或断开的 PDC 告警停止发声。

## 后续实车验证

先核对 XCP ID、接线、速率及访问权限，再分别验证三家设备连接、持续采集和断开重连。对照 CS+ / TRACE32 检查原始字段，确认温度、PDC 单位、点线方向、车辆/探头和里程计坐标、左右车位及故障状态。检查完整读取耗时和跨周期提示，最后验证录制回放、PDC 静音与设备掉线。现场结果确认前继续保留待验证标记。

协议实现参考 [pyXCP 命令与响应定义](https://github.com/christoph2/pyxcp/blob/master/pyxcp/types.py)、[pyXCP 主站命令实现](https://github.com/christoph2/pyxcp/blob/master/pyxcp/master/master.py)；同星收发 ABI 参考 [libTSCAN 官方 SDK](https://github.com/TOSUN-Shanghai/libTSCANDemos/blob/main/include/windwos/libTSCAN.h)。
