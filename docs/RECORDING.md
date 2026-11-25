# 录制与回灌手册

返回 [项目首页](../README.md) · [文档索引](README.md)

- [开始录制](#开始录制) · [保存文件](#保存文件) · [回看与导出](#回看与导出)
- [S20](#s20) · [D4M3](#d4m3) · [E211](#e211) · [PC 回灌单步调试](#pc-回灌单步调试)

## 开始录制

1. 在主窗口连接实车结果源，确认画面持续更新。
2. 打开「录制设置」，选择项目和回灌输入来源。选 ZLG、TOSUN 或 Vector 时填写对应设备与通道。选 UDP 时填写本机监听地址、来源 IP 和封装。选 XCP 时复用主窗口连接。
3. 选「仅采集」同步保存实车结果与所选输入。回灌输入选「无（仅实车结果）」可单独保存实车结果。选「实时回灌比对」时，指定该项目支持 `--stream` 的 RCP1 v2 worker，再点「检查连接」核对链路。
4. 保存设置后点「开始录制」，结束时点「停止录制」。会话默认在程序目录的 `recordings/sessions`，也可指定保存根目录。

## 保存文件

- 每次录制创建独立会话。`session.db` 保存采集数据，`manifest.json` 记录设置、状态和计数。
- 实车结果保存在 `real_vehicle.txt` 和前后探头 CSV。仅采集时，原始 CAN 输入自动导出 ASC，UDP 数据报自动导出 JSONL。
- 实时比对同时保存 `replay.txt`、回灌探头 CSV 和 `differences.csv`。配对键为启动号、输入周期和输出序号。
- E211 的 XCP 回灌输入保存为 `replay_dependency.bin` 和周期索引 JSONL，实车 PDC 另存 CSV。XCP on CAN 同时保存轮询收发帧 ASC，XCP on CAN FD 同时保存完整样本的 DAQ DTO ASC。

## 回看与导出

停止后可从「对比」重新打开会话，叠加结果、逐周期播放、查看字段或标记问题。「导出依赖」可另存 CAN ASC/BLF 或 UDP 原始 JSONL。「导出对比」可生成 `comparison_timeline.csv`，保留完整配对和单侧结果。S20 和 D4M3 有完整输入周期时可用「新版本重跑」，结果保存在子会话。

## S20

实车结果选 CS+ 或 XCP on CAN FD / TCP/IP / UDP/IP。原始输入选 CAN FD 或已适配的 UDP，依赖 ID 选 `s20`。用 XCP 做实时比对时，变量文件需包含 `sf_Upper_CompareGeneration`、`sf_Upper_CompareLength` 和 `sf_Upper_CompareBuffer`。[XCP 设置](interfaces/XCP.md#s20-采集与实时比对)

### 数据源

“录制设置”支持以下依赖输入：

- **ZLG CANFD**、**CANoe/Vector**、**TOSUN CANFD**：按 CAN FD 原始帧记录，使用 `assets/dbc/E541_PAS_20260609_FS21.dbc` 作为现场信号说明；
- **UDP**：支持 `can68`（68 字节 CAN FD）、`ussd`（USSD/IPC DBC）和 `raw`。`raw` 只保存数据报，适合尚未完成协议适配的项目；
- **无依赖**：保存主窗口实车结果。

CAN/UDP 的原始接收时间、通道、帧 ID、FD/扩展帧标志和字节数据都会落盘。UDP 原始数据可从对比窗口导出为 JSONL；CAN 或已适配的 UDP 可导出 ASC/BLF。

### S20 回灌链路

启用“实时回灌”后，程序启动 `dataReplay_main.exe --stream` 常驻进程，以 RCP1 帧协议传输完整 S20 输入周期。一个周期包含 20 个 CAN FD 输入帧；周期号、启动号、时间戳和 CRC 会写入保留元数据区，并保留车辆信息帧原有的滚动计数。回灌程序返回 USSV 输出后，按 `(boot, input_cycle, output_ordinal)` 与 CS+ 或 XCP 读取的冻结实车结果严格配对。输出序号在每个输入周期内从 1 开始，因此不依赖实车与 PC 的墙钟时间相等；真实任务时间仍保留在 USSV 快照中。工作进程握手能力版本为 2。

回灌算法文件和构建清单会复制到会话目录。默认可执行文件为 `build/s20-stream/bin/dataReplay_main.exe`，发布包中的路径为 `runtime_assets/replay/S20/dataReplay_main.exe`。构建输入 DBC 同时打包为 `runtime_assets/Database/E541_PAS_20260609_FS21.dbc` 和 `S20_Replay_Capture_v1.dbc`。

### S20 录制排查

- **实车有画面，完整周期为 0**。核对 CAN FD 通道、速率和接线，或 UDP 监听端口、来源 IP 和封装。确认 ECU 正在发送 S20 回灌输入，依赖 ID 配置为 `s20`。
- **完整周期增加，回灌为 0**。检查回灌程序路径、`--stream` 握手版本和会话中的 `replay.log`。
- **回灌增加，配对为 0**。核对固件的 `sf_Upper_Compare*` 符号及 `SCP2` 快照。CS+ 工程或 XCP 变量文件应与正在运行的固件匹配，刷写后重新连接再录制。
- **录制中途缺帧或 ECU 重启**。保存本次会话，恢复连接后开始新会话，使 PC 算法从连续输入重新运行。

### 固件配合

CS+ 工程启用 `SUPPORT_REPLAY_COMPARE` 后，`ReplayCompare_StampRaw` 在输入周期中写入严格匹配元数据；`ReplayCompare_Latch/Publish` 通过 `sf_Upper_CompareGeneration`、`sf_Upper_CompareLength` 和 `sf_Upper_CompareBuffer` 发布给 CS+ 读取。未发布该符号时，界面仍可录制实车和依赖原始数据，但不会宣称严格周期匹配。

配套固件追加 `SCP2` 校验尾，用 CRC 将周期键和 USSV 帧的校验值绑定。上位机识别新格式后每帧只读一次快照，并同时验证这两层 CRC。旧格式仍使用读取前后的代数校验。如果 CS+ 读取跨过 ECU 更新周期，旧格式会丢弃该快照，可能只看到 CANFD 输入和 PC 回灌计数增长。固件更新后需要重新连接上位机，以重新识别快照格式。

固件保留原来由传感器输入事件触发的 CAN 发送入口，禁止额外生成 20 ms 输入帧。PC 回灌保留算法状态，输入缺帧、重启或队列溢出会显示异常，原始记录继续保留。同一会话应使用连续输入；ECU 重启或输入不连续后，应停止并开始新的会话。算法启动状态未从 ECU 复制，首次录制之前的历史输入和算法版本差异仍可能导致结果不同。

### 验证范围

- 覆盖原始 CAN FD/UDP 保存、缺帧和 CRC 拒绝、严格配对、TXT/CSV/ASC/BLF 导出、对比窗口、重跑保留原记录、数据库释放等自动测试。
- S20 流式回灌与文件回灌使用同一段 ASC 比较完整输出，检查输出帧数和逐帧内容一致。
- S20 GHS Release 工程已编译、链接。`vHsm.hex` 仍缺失，合并 HEX 的出包校验沿用 S20 工程流程。
- 实车通过 CS+ 和 ZLG CANFD 验证了完整会话，2,390 个完整输入周期、5,614 帧回灌输出、666 组严格同周期配对，缺帧及解析错误均为 0。

## D4M3

### 接收和录制

D4M3 的实时比对使用 UDP CAN68。仅采集也可保存原始 CAN FD 和其他 UDP 封装。

1. 在 Windows 上给接收网卡配置 `192.168.98.123`。上位机选择 **UDP**，在「UDP 设置」填本机 `192.168.98.123:39001` 和来源 `192.168.98.233`，连接后确认实车画面持续更新。
2. 在「录制设置」选择 **D4M3**。回灌依赖使用 **UDP / can68 / legacy**，使用相同地址和端口，依赖 DBC 选择 `E541_PAS_20260609_FS21.dbc`。
3. 选择支持 `D4M3 / RCP1 v2 / --stream` 的 D4M3 native 回灌程序，将「录制模式」设为「实时回灌比对」，保存并开始录制。上位机从同一个 UDP 接收器读取实车可视化与回灌依赖。
4. 在「字段对照」选择 PDC、POINT 或 LINE。PDC 可看系统状态以及同一探头的距离、范围等级、故障；点线可看坐标和高低属性。停止录制后从「对比」重新打开会话。

### 数据合同

实车图沿用 `LAUTERBACH_UPPER_DEBUG` 的 UDP USSD 画面。回灌输入是同一条 UDP 链路发出的 CAN68 组，每个数据报有 E541 的 20 条原始报文，4 字节大端 ID 加 64 字节 DBC 负载。原有功能字段、DBC 文件和报文长度保留。

`RawData_SendToCAN` 在完整测量生成后写入真实输入序号。20 ms 输出完成后锁存最近一次可视化的输入周期、输出序号与 USSD 状态消息中的微秒时间戳。该信息在下一次原始测量中随 UDP 带出，上位机据此精确匹配已收齐的 USSD 结果。

| 帧 | DBC 字节偏移（从 0 开始） | 内容 |
| --- | --- | --- |
| 0x103 | 48–51 | D4 标记与 24 位启动号 |
| 0x103 | 52–55 | 当前完整输入周期 |
| 0x103 | 56–59 | 最近可视化结果的输入周期 |
| 0x103 | 60 | 当前测量的 PDC 开关请求 |
| 0x103 | 61–62 | 最近可视化结果的输出序号 |
| 0x102 | 44–49、58–59 | 最近可视化结果的微秒时间戳，小端 |
| 0x102 | 50–57 | 原有输入毫秒时间戳 |
| 0x102 | 60–61 | CRC-16/CCITT-FALSE，覆盖上述周期、时间戳和 PDC 请求字段 |

UDP 转发需要按既有 E541 规则保留 `0x102`、`0x103` 的这些字节，同时保留 USSD 中的 `Upper_StatusOutSignal.TimeStamp`。启动后首个输入和录制尾部可能只有原始记录。未得到双方同周期身份或完整数据时，原始记录仍保存。PC 回灌从自身初始状态运行，算法及初始历史的差异仍会反映到结果。

D4M3 在此处对比 PDC、点、线和属性。

停止录制后，点「导出依赖」选 ASC，将 CAN68 还原为 CAN FD 原始帧。ASC 保留 ID 和负载，使用上位机收包的相对时间；同一数据报中的帧时间相同，实车 USSD 可视化不写入 ASC。如需原始 UDP 数据报，选 JSONL。点「导出对比」可另存 `comparison_timeline.csv`，包含输入周期键、两侧输出时间戳、点线坐标及属性，以及按探头名称保存的 PDC 状态、距离、范围和故障。

## E211

主窗口连接 E211 XCP，录制项目选 E211，模式选「仅采集」。回灌输入选与在线连接一致的 XCP 传输，或选「XCP（跟随在线连接）」。

E211 实车画面在四种 XCP 传输上均使用 DAQ。CAN FD、TCP/IP 和 UDP/IP 的回灌输入也使用独立 DAQ 列表，需使用带调试类型信息的同版 ELF。经典 CAN 的回灌输入读取固件发布的 `sf_Upper_E211ReplaySequence` 和 `sf_Upper_E211ReplaySlots`。两路均导出 1800 字节一条的 `USSXCPOfflineReplayData_t` 记录，包含时间戳、里程计、车速、温度、挡位、工作模式及 12 路原始传感器输入。[E211 连接参数、变量与导出字段](interfaces/XCP.md#e211-联调与录制)

## PC 回灌单步调试

此数据源供 Replay_SourceFile 的 GDB / VS Code 单步调试使用。它读取 REPLAY_UPPER_SNAPSHOT 指定的 UPPER v1 / CRC32 二进制最新快照，与 C 进程分开运行。

推荐从回灌工程按 F5 启动 Replay: COLIGEN upper single-step。启动器会设置快照路径并自动连接本上位机的“REPLAY DEBUG”。

也可以在“设备与显示”的 HARDWARE 选项中手动选择“REPLAY DEBUG”，连接时选择回灌生成的快照文件。上一次选择在当前进程中保留。

断点停住时保留最后完整帧，状态显示“暂停 / 等待下一步”，可继续检查数组和操作视图。继续执行到下一个完整输出后刷新；读到截断、CRC 错误或暂时不存在的文件时重试，保持已有完整画面。此模式不输出实时 PDC 提示音，不把当前电脑时间标成原始采样日期。

回灌工程对应路径：
D:/Cenww_work/SF26195_Geely_KX21/replay/Replay_SourceFile/docs/REPLAY_UPPER_DEBUG.md

测试可设置 REPLAY_DEBUG_TEST_PACKET 指向真实 C 回灌输出的快照文件，然后执行：
python -m pytest -q tests/test_replay_debug.py
