# UPPER 串口接入与实车移植

上位机的数据源「SERIES」，默认 921600、8N1。接收完整的 `LAUTERBACH_UPPER_DEBUG` 变量快照，可显示车辆、RAW、PDC、80 点、20 线及车位；位姿同时供固定世界坐标和后轴中心轨迹使用。

## 配套代码与回灌工程

本仓库的配套代码位于 `firmware/upper_serial/`；下列 `src/`、`tools/` 和 `tests/replay/` 路径属于已合入的 Replay_SourceFile 回灌工程，不是上位机 Python 目录。

- `src/UpperSerialDebug.c/.h`：独立的 USSV v1 编码器、CRC32 和发送回调，使用静态缓冲区。
- `src/UpperSerialVariables.c`：逐字段读取 `sf_Upper_*` 变量，序列化全部数组，保留下标、ObjID 和 cNum。
- `src/Lauterbach_Var.c/.h`：回灌工程所需的八类调试变量镜像，类型与 MCU 原接口一致。
- `src/UpperSerialReplay.c/.h`：回灌数据采集适配，挂在通用和 S20 的 `AppCore20msTask()` 末尾。
- `src/CommonPara/sfType.h` 和 `src/VehicleProjects/S20/CommonPara/sfType.h`：调试宏、串口自动导出开关和发送周期。
- `tools/build_s20_r77207_replay.py`：将上述共用模块纳入 S20 的隔离构建。KX21 等通用构建由 makefile 自动编译根目录 C 文件。

`LAUTERBACH_UPPER_DEBUG` 控制调试变量；`LAUTERBACH_UPPER_SERIAL_DEBUG` 为 1 时启用回灌自动采集，设为 0 时移除该调用。`UPPER_SERIAL_PERIOD_US` 默认 100000，即最多 10 Hz。不注册发送回调时不会发送数据。

## 对接域控底软

实车已有 `Lauterbach_Var.c/.h` 时保留原文件，合入 `UpperSerialDebug.c/.h` 和 `UpperSerialVariables.c` 即可。`UpperSerialReplay.*` 是 PC 回灌专用，不放入实车算法；其采集变量和坐标换算可作参考。

初始化时调用 `UpperSerialDebug_SetWriter(writer, context)`。回调签名为：

```c
int writer(const uint8_t *data, uint16_t size, void *context);
```

回调将整帧复制到域控 UART/DMA 发送队列，成功返回 0，队列满或失败返回非 0。回调返回前必须复制或接管数据，不能只保存临时指针。编码器和变量采集从同一个生产任务调用，不从 UART 中断重入。

在该周期的 `OutputSignalRead_Status/Odo/Vehicle/Rawdata/PDC/Point/Line/Slot` 都完成后调用 `UpperSerialDebug_SendVariables()`。已有固件不需改写它们的结构体内存布局。不要再重复定义 `sf_Upper_*` 全局变量。

协议约定：点、线、车位和探头为毫米，X 向前、Y 向左；里程计位置为米，航向为弧度，车速为 km/h，TimeStamp 为设备微秒计数；PDC dis 沿用原接口厘米，RAW 其余字段保持原值。移植时让变量满足此约定，或者在上位机设置中统一反转 Y 和航向符号。回灌适配已将跟踪位姿及探头从 X 右/Y 前转换到该约定；输出点线已是前/左，保持原样。

当前回灌配置不运行 PDC 和车位算法，这两类调试变量默认全 0，不伪造障碍物。实车已有的对应 `OutputSignalRead_*` 正常填入后，发送器和上位机可完整显示。

## 帧格式

所有字段均按 little-endian 编码，float 为 IEEE-754 float32，禁止直接发送带 padding 的 C 结构体。

- 帧头 12 字节：`USSV`、version u8=1、flags u8=0、payload_size u16、sequence u32。
- payload 内 8 个 TLV：tag u8、size u16、body。tag 1～8 对应 Status、Odo、Vehicle、RawData、PDC、Point、Line、Slot。
- 尾部 CRC32 u32：覆盖整个帧头和 payload，CRC-32/ISO-HDLC，与 `zlib.crc32` 一致。
- Status：GearLever u8、Temp u16、Speed f32、TimeStamp u64；Odo：三个 f32；Vehicle：长宽两个 u16，再按 RRS/RRC/RRM/RLM/RLC/RLS/FRS/FRC/FRM/FLM/FLC/FLS 顺序发 12 组 i16 X/Y。
- RAW：两个 u16 同频计数、两个 u8 标志、count u8=12，再发 12 个 `mode:u8 + 9*u16`。
- PDC：三个 u8 状态、count u8=12，再发 12 个 `dis:u16/range:u8/fault:u8`。
- Point：count u16，再发每个元素的 `ObjID:u16, x:i16, y:i16, cHight:u8, Tx:u8, Rx:u8`，每元素 9 字节。
- Line：count u16，再发 `cNum:u8, cHight:u8, cObjType:u8, StartX:i16, StartY:i16, EndX:i16, EndY:i16, wDist:u16`，每元素 13 字节。
- Slot：`slot_sts/left_num/right_num/side_capacity` 四个 u8，随后左侧全部槽位、右侧全部槽位。每槽位 40 字节：timestamp u64、id/type 两个 u8、宽深两个 u16、A 点两个 i16、A_type u8、B～F 点十个 i16、F_type u8。常规镜像每侧 3 个；通用帧 API 也支持每侧 4 个。

常规 80 点、20 线、6 车位完整帧为 1634 字节。10 Hz、8N1 需要约 163400 bit/s，因此推荐 921600；使用 115200 时将周期调至至少 200000 us，并保证底软队列不堵塞。

## 验证与复现

已验证通用 KX21 和 S20 隔离构建；原有生产 EXE 未覆盖。新构建在 `build/serial_upper_20261116/`。

`tests/replay/upper_serial_fixture.c` 检查 CRC 标准向量、队列失败、重入保护、参数边界及完整变量输出；生成的 1634 字节帧在上位机测试中校验全部字段、录制回放和 ObjID/cNum。

`tests/replay/upper_serial_replay_fixture.c` 使用受控变量验证回灌采集、坐标换算、左右串扰映射、RAW 宽度和 100 ms 限频。UART 宏关闭分支也已编译通过。

PC 可设置 `UPPER_SERIAL_OUTPUT` 为文件路径，将发送回调接到二进制文件；未设置时不会创建文件。该方式只用于协议验证，不能替代实车 UART/域控验证。

全套 `main.py test` 的 82 项检查中，79 项通过；其余 3 项要求旧 `S20_R77207_TEST_STAGE`/历史未合并源文件，而当前工程默认使用已合并的日常 S20 源码阶段。串口新增检查不依赖这些旧阶段。


### 可选线段方向扩展（2026-11-17）

USSV v1 保留 tag 7 的 13 字节线段记录，新增可选 tag 9：每个字节是对应
线段的 `cDirect`，长度必须等于 tag 7 的线段数量。无扩展时默认 0。
`UpperSerialVariables.c` 从 `Upper_LineOutSignal.cDirect` 复制到 `UpperSerialLine.direction`；
串口编码器在至少一个方向非零时发送此块，全零时省略，接收端每帧重新赋值，避免残留。
S20 CAN 编码器始终发送完整 20 字节方向块。方向来自 `IlPutTx_ObjPt_Direct` 的原始枚举，
0 为车辆在线段左侧，1 为右侧；画布箭头始终为起点 → 终点。

## E211 counted output adapter (v5.2.13)

`E211UpperSerialVariables.c` is the E211 adapter. Build it and `UpperSerialDebug.c` with `UPPER_SERIAL_E211`, use the E211 `Lauterbach_Var.h`, and register the UART writer. Do not build the legacy S20 adapter for E211. Capacities follow `Rte_Type_SF.h`. Geometry TLVs retain uint16 counts and explicit wire fields. Optional tag 10 is 10 bytes (`<BBBBHHBB`) in the order eState, pdcRequestAvm, frontStopReq, rearStopReq, frontMinDst, rearMinDst, SnsrFltOfPrkgDstCtrl, PdcMuteBtnSts. Old v1 frames without tag 10 remain supported. Serial and USSV-over-CAN-FD share this payload. Frames remain bounded by the protocol's 8192-byte payload limit, and oversized frames fail validation instead of being truncated.
