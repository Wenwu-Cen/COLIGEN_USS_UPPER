# S20 sf_Upper CAN-FD 协议（2026-11-17）

在实车 `OBJ_DEBUGCAN` 开启、`SUPPORT_RAWDATA_DEBUGCAN` 关闭时，用 CAN-FD 传输
`LAUTERBACH_UPPER_DEBUG` 的八类 `sf_Upper_*` 调试变量。`LAUTERBACH_UPPER_DEBUG`
需要同时开启；原始回波录制模式继续使用原有协议。随 v4.6.0 一并发布。

## 发送与刷新

复用现有 20 个 RTE 发送接口：`PAS_Rawdata0..19`，实际 CAN ID 为
`0x640`、`0x6B6..0x6C8`。每条固定 64 字节，不修改生成的 RTE/COM/CanIf 配置。
`0x6C9..0x6CD` 不再由本可视化分支发送旧内容。

现有 `AppCore20msTask` 每两次调用一次调试发送，所以一轮间隔为 40 ms。
完整快照为 1634 字节、30 个有效分片，需要两轮（约 80 ms / 12.5 Hz）；
第二轮末 10 个 PDU 发空闲标记。第一轮采集后冻结快照，第二轮不再读取变化的数组。
只有完整包且 CRC 正确才刷新画布、数据详情和报警。丢片时保留最后一帧，等待后续完整包。

## 每条 CAN-FD 载荷

- 字节 0..1：ASCII `UC`。
- 字节 2：协议版本 1。
- 字节 3：全包分片编号 0..29，空闲为 255。
- 字节 4..5：快照序号低 16 位，小端。
- 字节 6..7：完整包长度 1634，小端。
- 字节 8..63：56 字节包数据，不足补零。

分片编号取模 20 必须等于 CAN ID 的序号。完整包内还包含 32 位序号，
必须与外层低 16 位相符。乱序和相同重复片可接收，冲突重复片清理该轮缓存；
CRC 错误整包丢弃。固定最多缓存四个未完成包，回放跳转或循环时清空组包状态。

## 完整包字段

完整包复用 `serial_protocol.py` 的 USSV v1 小端 TLV 和 CRC32 编码，不传 C 结构体填充。
依次包含状态、ODO、车体/12 探头安装位置、同频计数/标志及 12 组 DE/CE 距离峰值宽度、
PDC 状态和 12 组距离/报警/故障、80 点、20 线、左右各 3 个 A..F 车位。
数组按固定容量发送，包括末次空点/空线；索引、ObjID、cNum、cObjType、属性和探头编号保留。

CAN 的数值采用 S20 原生变量口径，**与串口 v1 的坐标约定不同**：

- 点、线：毫米，X 向前、Y 向右；上位机显示时将 Y 取负，与当前 CS+ 显示一致。
- 车位 A..F：沿用当前 CS+ 的坐标原值，独立处理，不跟随障碍物进行 Y 取负。
- 探头安装位置：毫米，X 向右、Y 向前；显示转换为 `(Y, -X)`。
- ODO：毫米，X 向右、Y 向前，角度弧度；使用 `mm_right_forward`，不乘 1000。
- 速度：原生 `sf_Upper_StatusOutSignal.Speed`（ESP km/h）。
- 状态时间：采集快照时直接取硬件微秒时钟，避免继承旧原始 CAN 路径的毫秒 tick。
- 车位自身时间戳保留变量原值。

## 使用

以 TOSUN（CAN1～CAN12）、ZLG-USBCANFD 或 CANOE/VECTOR 连接原有 CAN 通道，波特率沿用原设置。
不需要切换 SLOT 来区分新协议的数据类型。旧 DBC 格式 ASC/BLF 仍可回放；
识别到 UC 后，该次连接/回放会话内不会再把残片按旧 DBC 解释。

源码运行：`uv run python src/app.py`。Windows 程序为 `dist/release460/COLIGEN_USS_UPPER_v4.6.0.exe`。
固件与上位机需成对使用。实车尚未验证，完成本地编译/协议测试不等同于总线硬件实测通过。

`firmware/upper_can/UpperCanDebug.c` 是实车内嵌编码器的测试镜像，
`UpperCanTypes.h`/`CtCdUSS_MemMap.h` 仅供主机互通测试；不要将该空 MemMap 头覆盖到实车。
实车逻辑位于 `Lauterbach_Var.c`，无需新增 GPJ 编译项。
