# S20 录制、回灌与实时对比

S20 的界面操作、模式选择和输出文件统一见 [README · 录制与回灌](../README.md#录制与回灌)。本页说明 S20 的输入格式、比对固件和排查方法。

## 数据源

“录制设置”支持以下依赖输入：

- **ZLG CANFD**、**CANoe/Vector**、**TOSUN CANFD**：按 CAN FD 原始帧记录，使用 `assets/dbc/E541_PAS_20260609_FS21.dbc` 作为现场信号说明；
- **UDP**：支持 `can68`（68 字节 CAN FD）、`ussd`（USSD/IPC DBC）和 `raw`。`raw` 只保存数据报，适合尚未完成协议适配的项目；
- **无依赖**：保存主窗口实车结果。

CAN/UDP 的原始接收时间、通道、帧 ID、FD/扩展帧标志和字节数据都会落盘。UDP 原始数据可从对比窗口导出为 JSONL；CAN 或已适配的 UDP 可导出 ASC/BLF。

## S20 回灌链路

启用“实时回灌”后，程序启动 `dataReplay_main.exe --stream` 常驻进程，以 RCP1 帧协议传输完整 S20 输入周期。一个周期包含 20 个 CAN FD 输入帧；周期号、启动号、时间戳和 CRC 会写入保留元数据区，并保留车辆信息帧原有的滚动计数。回灌程序返回 USSV 输出后，按 `(boot, input_cycle, output_ordinal)` 与 CS+ 或 XCP 读取的冻结实车结果严格配对。输出序号在每个输入周期内从 1 开始，因此不依赖实车与 PC 的墙钟时间相等；真实任务时间仍保留在 USSV 快照中。工作进程握手能力版本为 2。

回灌算法文件和构建清单会复制到会话目录。默认可执行文件为 `build/s20-stream/bin/dataReplay_main.exe`，发布包中的路径为 `runtime_assets/replay/S20/dataReplay_main.exe`。构建输入 DBC 同时打包为 `runtime_assets/Database/E541_PAS_20260609_FS21.dbc` 和 `S20_Replay_Capture_v1.dbc`。

## 录制问题排查

- **实车有画面，完整周期为 0**。核对 CAN FD 通道、速率和接线，或 UDP 监听端口、来源 IP 和封装。确认 ECU 正在发送 S20 回灌输入，依赖 ID 配置为 `s20`。
- **完整周期增加，回灌为 0**。检查回灌程序路径、`--stream` 握手版本和会话中的 `replay.log`。
- **回灌增加，配对为 0**。核对固件的 `sf_Upper_Compare*` 符号及 `SCP2` 快照。CS+ 工程或 XCP 变量文件应与正在运行的固件匹配，刷写后重新连接再录制。
- **录制中途缺帧或 ECU 重启**。保存本次会话，恢复连接后开始新会话，使 PC 算法从连续输入重新运行。

## 固件配合

CS+ 工程启用 `SUPPORT_REPLAY_COMPARE` 后，`ReplayCompare_StampRaw` 在输入周期中写入严格匹配元数据；`ReplayCompare_Latch/Publish` 通过 `sf_Upper_CompareGeneration`、`sf_Upper_CompareLength` 和 `sf_Upper_CompareBuffer` 发布给 CS+ 读取。未发布该符号时，界面仍可录制实车和依赖原始数据，但不会宣称严格周期匹配。

配套固件追加 `SCP2` 校验尾，用 CRC 将周期键和 USSV 帧的校验值绑定。上位机识别新格式后每帧只读一次快照，并同时验证这两层 CRC。旧格式仍使用读取前后的代数校验。如果 CS+ 读取跨过 ECU 更新周期，旧格式会丢弃该快照，可能只看到 CANFD 输入和 PC 回灌计数增长。固件更新后需要重新连接上位机，以重新识别快照格式。

固件保留原来由传感器输入事件触发的 CAN 发送入口，禁止额外生成 20 ms 输入帧。PC 回灌保留算法状态，输入缺帧、重启或队列溢出会显示异常，原始记录继续保留。同一会话应使用连续输入；ECU 重启或输入不连续后，应停止并开始新的会话。算法启动状态未从 ECU 复制，首次录制之前的历史输入和算法版本差异仍可能导致结果不同。

## 验证范围

- 覆盖原始 CAN FD/UDP 保存、缺帧和 CRC 拒绝、严格配对、TXT/CSV/ASC/BLF 导出、对比窗口、重跑保留原记录、数据库释放等自动测试。
- S20 流式回灌与文件回灌使用同一段 ASC 比较完整输出，检查输出帧数和逐帧内容一致。
- S20 GHS Release 工程已编译、链接。`vHsm.hex` 仍缺失，合并 HEX 的出包校验沿用 S20 工程流程。
- 实车通过 CS+ 和 ZLG CANFD 验证了完整会话，2,390 个完整输入周期、5,614 帧回灌输出、666 组严格同周期配对，缺帧及解析错误均为 0。
