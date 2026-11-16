# 配套 C 串口发送接口

本目录镜像已合入 `D:/Cenww_work/SF26195_Geely_KX21/replay/Replay_SourceFile/src` 的代码。接入步骤和协议见 [串口说明](../../docs/SERIAL_PROTOCOL.md)。

实车已有 `Lauterbach_Var.c/.h` 时保留原文件，编译 `UpperSerialDebug.c` 和 `UpperSerialVariables.c`，注册 `UpperSerialDebug_SetWriter()`，在完整一轮 `OutputSignalRead_*` 之后调用 `UpperSerialDebug_SendVariables()`。发送回调需在返回前复制整帧。

`UpperSerialReplay.*` 仅用于 PC 回灌，不纳入域控固件。该回灌配置没有 PDC 和车位算法，对应变量保持零；实车正常填入调试变量后，两端支持全部字段。

`sfType.h` 中开关示例：

```c
#define LAUTERBACH_UPPER_DEBUG
#define LAUTERBACH_UPPER_SERIAL_DEBUG 1
#define UPPER_SERIAL_PERIOD_US 100000u
```

UART 建议 921600 8N1，默认最多 10 Hz。X 向前、Y 向左；点线与探头为毫米，里程计为米/弧度，车速 km/h，时间戳微秒。

`Replay_Integration.patch` 为已有回灌源码的最小接入差异；在兼容基线使用 `git apply --unidiff-zero Replay_Integration.patch`。代码已在用户指定的回灌目录中合入，无需再次应用。
