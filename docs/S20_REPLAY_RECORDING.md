# S20 录制、回灌与实时对比

点击主界面的“开始录制”后，程序会同时保存可视化快照和依赖输入数据。采集线程直接写入会话目录的 SQLite WAL 数据库，界面刷新不会阻塞采集。

## 数据源

“录制设置”支持以下依赖输入：

- **ZLG CANFD**、**CANoe/Vector**、**TOSUN CANFD**：按 CAN FD 原始帧记录，使用 `assets/dbc/E541_PAS_20260609_FS21.dbc` 作为现场信号说明；
- **UDP**：支持 `can68`（68 字节 CAN FD）、`ussd`（USSD/IPC DBC）和 `raw`。`raw` 只保存数据报，适合尚未完成协议适配的项目；
- **无依赖**：只记录 CS+ 实车可视化，不能启动实时回灌。

CAN/UDP 的原始接收时间、通道、帧 ID、FD/扩展帧标志和字节数据都会落盘。UDP 原始数据可从对比窗口导出为 JSONL；CAN 或已适配的 UDP 可导出 ASC/BLF。

## S20 回灌链路

启用“实时回灌”后，程序启动 `dataReplay_main.exe --stream` 常驻进程，以 RCP1 帧协议传输完整 S20 输入周期。一个周期包含 20 个 CAN FD 输入帧；周期号、启动号、时间戳和 CRC 会写入保留元数据区，并保留车辆信息帧原有的滚动计数。回灌程序返回 USSV 输出后，按 `(boot, input_cycle, output_ordinal)` 与 CS+ 输出严格配对。输出序号在每个输入周期内从 1 开始，因此不依赖实车与 PC 的墙钟时间相等；真实任务时间仍保留在 USSV 快照中。工作进程握手能力版本为 2。

回灌算法文件和构建清单会复制到会话目录。默认可执行文件为 `build/s20-stream/bin/dataReplay_main.exe`，发布包中的路径为 `runtime_assets/replay/S20/dataReplay_main.exe`。构建输入 DBC 同时打包为 `runtime_assets/Database/E541_PAS_20260609_FS21.dbc` 和 `S20_Replay_Capture_v1.dbc`。

## 交互流程

1. 打开“录制设置”，选择依赖类型、设备参数、UDP 端口、S20 ID 配置、依赖 DBC 和回灌程序。DBC 默认指向需求中指定的 `E541_PAS_20260609_FS21.dbc`。
2. 点击“检查连接”验证硬件/端口；检查使用临时会话，3 秒后自动关闭。
3. 点击“开始录制”。录制窗口左右显示 **实车 / CS+** 与 **回灌 / S20 PC**，状态栏显示完整周期、缺帧、解析错误、回灌输出和严格匹配数。
4. 可冻结实时画面、逐周期播放、叠加回灌结果、标记问题，并打开“字段对照”比较点/线的属性和差值。
5. 停止录制后，会话目录保留 `manifest.json`、`session.db`、`real_vehicle.txt`、`replay.txt`、CSV 和 `differences.csv`。选择“新版本回灌”会从原始输入重新生成独立子会话，不修改原始记录。

## 固件配合

CS+ 工程启用 `SUPPORT_REPLAY_COMPARE` 后，`ReplayCompare_StampRaw` 在输入周期中写入严格匹配元数据；`ReplayCompare_Latch/Publish` 通过 `sf_Upper_CompareGeneration`、`sf_Upper_CompareLength` 和 `sf_Upper_CompareBuffer` 发布给 CS+ 读取。未发布该符号时，界面仍可录制实车和依赖原始数据，但不会宣称严格周期匹配。

固件保留原来由传感器输入事件触发的 CAN 发送入口，禁止额外生成 20 ms 输入帧。PC 回灌保留算法状态，输入缺帧、重启或队列溢出会显示异常，原始记录继续保留。同一会话应使用连续输入；ECU 重启或输入不连续后，应停止并开始新的会话。算法启动状态未从 ECU 复制，首次录制之前的历史输入和算法版本差异仍可能导致结果不同。

## 验证范围

- 覆盖原始 CAN FD/UDP 保存、缺帧和 CRC 拒绝、严格配对、TXT/CSV/ASC/BLF 导出、对比窗口、重跑保留原记录、数据库释放等自动测试。
- S20 流式回灌与文件回灌使用同一段 ASC 比较完整输出，检查输出帧数和逐帧内容一致。
- GHS Release 工程已编译、链接；本地尚未执行 CAN 硬件、CS+ 在线读取和实车整条链路联调。构建后处理仍报告工程原有的 `vHsm.hex` 缺失，产出的合并 HEX 需按项目流程核验。
