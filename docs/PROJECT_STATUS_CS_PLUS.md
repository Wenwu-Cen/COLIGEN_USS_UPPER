# CS+ 接入工程状态梳理

> 文档日期：2026-09-11  
> 当前结论：CS+ 的数据读取链路已经打通到“结构体字节无损读取”，但当前 `debugger.Memory.ReadRange()` + E1 RAM Monitor 路径无法稳定满足“完整帧 100 ms 内逐帧显示”。当前暂停继续调试，保留 61247 内存桥方案。  
> 说明：本文反映当前工作区和 `D:\Desktop\0911` 运行副本的实际状态，不替代旧的 `PROJECT_DOCUMENTATION.md`。旧文档主要描述早期 Lauterbach 方案，部分内容已经过期。

## 0. 一句话结论

当前工程采用：

```text
上位机 GUI
  -> OnlineReader 后台线程
  -> ReadDataPort_CSPlus.py
  -> TCP 127.0.0.1:61247
  -> CS+ Python Console 内的 csplus_memory_bridge.py
  -> debugger.Memory.ReadRange()
  -> E1 / LPD RAM Monitor
```

采用 61247 内存桥的原因不是性能，而是正确性：外部 Integration Service 的 `read_memory` 会把十六进制前导零丢掉，例如 `0x0A,0x01,0x00,0x00` 可能变成 `"A100"`，无法作为结构体字节流使用。CS+ Console 内部的 `debugger.Memory.ReadRange()` 返回数值列表，可以无损转换回字节。

当前性能状态：

- 完整结构体区域约 `1756` 字节，已经合并为一次连续读取。
- 典型读取约 `20 ms`，但存在周期性 `600~800 ms` 长尾。
- 读取 1 字节和读取 1756 字节出现相同的长尾，说明瓶颈不在数据量、TCP 或 Python 结构体解析，而在 CS+ / E1 RAM Monitor 的同步访问和内部锁。
- 因此当前方案不能保证“每次完整读取都小于 100 ms”。如果实际产品要求稳定 100 ms 逐帧显示，应改用目标端专用数据通道，而不是继续微调当前桥接代码。

## 1. 路径与运行环境

### 1.1 关键路径

| 类型 | 路径 | 说明 |
|---|---|---|
| 当前开发工作区 | `D:\Desktop\upper_demo\Reasa\new` | 当前代码和测试脚本所在目录 |
| 运行/部署副本 | `D:\Desktop\0911` | 包含 CS+ 桥接源码，且当前 61248 文件服务指向此目录 |
| 当前 CS+ 工程 | `E:\Coligen_Lpn\Project\BesTune\E541_AK2\SourceCode\20260525_SW-49\E541_SF24223_AK2_16443_3M\Toolchain\E541_SF24223_AK2_16443_3M.mtpj` | 当前 CubeSuiteW+ 已加载工程 |
| CS+ 可执行文件 | `C:\Program Files (x86)\Renesas Electronics\CS+\CC\CubeSuiteW+.exe` | 当前 CS+ IDE |
| 桥接源码（部署副本） | `D:\Desktop\0911\csplus_memory_bridge.py` | 逻辑大小 17193 字节，SHA256 前缀 `2c90a728b7a95499` |
| 桥接源码（CS+ 工程侧副本） | `E:\Coligen_Lpn\Project\BesTune\E541_AK2\SourceCode\20260525_SW-49\E541_SF24223_AK2_16443_3M\Toolchain\csplus_memory_bridge.py` | 与 `D:\Desktop\0911` 副本相同 |
| 兼容启动器 | `D:\TempBridge\bridge_launcher.py` | Base64 内嵌同一份桥接源码；用于规避本机防泄漏/透明加密对 CS+ IronPython 直接读取脚本的影响 |
| 性能/协议测试 | `csplus_bridge_bench.py` | 可直接执行 `OPTIONS`、`PROBE`、`BENCH` |
| 旧工程文档 | `PROJECT_DOCUMENTATION.md` | 早期 Lauterbach/旧目录版本，不能作为当前 CS+ 状态依据 |

### 1.2 当前进程和端口快照

本文件生成时观察到的状态：

| 端口 | 监听进程 | 当前状态 |
|---|---|---|
| `61246` | 无 | CS+ Integration Service 当前未监听，未采用 |
| `61247` | CS+ PID `38904`，`CubeSuiteW+.exe` | TCP 监听存在，`PING` 可返回 `B + len=1 + "P"` |
| `61248` | Python PID `42860` | `python3 -m http.server`，目录为 `D:\Desktop\0911` |

补充：最后一次主动检查时，61247 的 `PING` 正常，但 `OPTIONS` / `PROBE` 返回了：

```text
global name 'debugger' is not defined
```

随后 `ADDR` 查询超时。这说明当前监听线程还在，但加载它的 CS+ Console 上下文已经不再持有有效的 `debugger` 对象，当前状态下不能直接进行数据结构读取。恢复使用时，需要在有效的 CS+ 调试会话/Console 上下文中重新加载桥接。

### 1.3 工作区与 0911 副本同步情况

核心 CS+ 文件已经一致：

| 文件 | `new` 工作区 | `D:\Desktop\0911` | 结果 |
|---|---|---|---|
| `DataSheet.py` | 6149 字节，`0ee189d5beaed965` | 6149 字节，`0ee189d5beaed965` | 相同 |
| `OnlinePort.py` | 23741 字节，`e0f2788fb3a6d9f6` | 23741 字节，`e0f2788fb3a6d9f6` | 相同 |
| `ReadDataPort_CSPlus.py` | 60541 字节，`8736e0803c5aa118` | 60541 字节，`8736e0803c5aa118` | 相同 |
| `ReadDataPort_T32.py` | 25596 字节，`37e0e006b84ec90f` | 25596 字节，`37e0e006b84ec90f` | 相同 |
| `csplus_bridge_bench.py` | 2091 字节，`e0c35550c84514ab` | 2091 字节，`e0c35550c84514ab` | 相同 |
| `VehUpperDemo.py` | 159800 字节，`01bf0fd724c28e40` | 158662 字节，`1497126c22e52c7b` | 不同 |

`VehUpperDemo.py` 的差异主要是 `new` 工作区包含更新后的界面样式、面板布局和显示文字；CS+ 数据读取/解析核心不受影响。如果以 `D:\Desktop\0911` 作为唯一运行目录，后续需要单独同步 GUI 文件，不能把“CS+ 核心文件一致”误认为整个工程一致。

### 1.4 文件访问异常说明

本机存在防泄漏/透明加密特征。普通原生工具读取某些 `.py` 时可能看到：

```text
%TSD-Header-###%
```

并使用填充后的文件大小（例如显示为 65536 字节）；Python 3.10 读取同一文件时看到的是正常源码和实际大小。该现象会影响 CS+ IronPython 直接 `execfile` 源文件的成功率，因此当前可靠启动方式是使用 `D:\TempBridge\bridge_launcher.py`。不要把 `%TSD-Header-###%` 误判为源码损坏，也不要使用未经确认的方法覆盖原文件。

## 2. 工程模块职责

| 文件 | 职责 | 当前注意事项 |
|---|---|---|
| `VehUpperDemo.py` | Tkinter 主程序、画布、日志解析、在线 tick、录制/回放、More Data 面板 | 需要 Python 3；默认连接方式下拉框初始为 Lauterbach，使用 CS+ 时必须手动选择 CS+ |
| `OnlinePort.py` | 在线 Reader 线程、帧数据模型、`build_frame()`、后端动态选择、错误桥接 | 每轮读取 8 类数据，全部成功才发布新帧 |
| `ReadDataPort_CSPlus.py` | CS+ 后端、61247 客户端、符号地址读取、批量预取、结构体解析、超时统计 | 当前重点模块 |
| `DataSheet.py` | GUI、Reader、解析模块之间共享的数据层 | 在线读取结果先写入此处，再由 `OnlinePort` 组装成显示帧 |
| `ReadDataPort_T32.py` | Lauterbach Trace32 RCL 旧后端 | 保留备用；不是当前 CS+ 数据链的一部分 |
| `csplus_bridge_bench.py` | 61247 桥接协议和性能测试客户端 | 用于 `PING`、`OPTIONS`、`PROBE`、`BENCH` |
| `csplus_memory_bridge.py` | 在 CS+ Python Console 内运行的服务端桥接 | 当前在 `D:\Desktop\0911` 和 E 盘 Toolchain 各有一份 |
| `bridge_launcher.py` | Base64 包装启动器 | 当前建议的 CS+ Console 启动入口 |
| `PROJECT_DOCUMENTATION.md` | 早期工程文档 | 保留历史信息，不作为当前 CS+ 实况文档 |
| `*_backup*`、`.bak_*` 文件 | 调试前备份 | 不应被 GUI 或 CS+ 自动加载 |
| `_csplus_docs` | CS+ 官方帮助文档提取资料 | 用于确认 RAM Monitor、Python Console 和 API 行为 |
| `*.png`、临时探测脚本 | 调试过程证据 | 不属于运行时依赖，可后续归档 |

## 3. 当前数据流和运行周期

### 3.1 在线数据流

```text
VehUpperDemo.App._toggle_online()
  -> 选择 backend='csplus'
  -> OnlineReader.start()
  -> ReadDataPort_CSPlus.read_port_connect()
  -> bridge_available() / PING
  -> 后台循环读取并解析
  -> DataSheet
  -> OnlinePort.build_frame()
  -> GUI 显示最新帧
```

CS+ 读取按以下顺序执行：

```text
Status
Vehicle
Point
Line
Echo
PDC
Slot
```

其中 `Status` 还会同时读取 Odo。所有读取成功后才更新 `latest_frame`；只要有一项失败，GUI 保留上一帧，以避免半帧/混帧数据显示。

### 3.2 循环周期

| 层级 | 代码周期 | 实际含义 |
|---|---:|---|
| GUI 轮询 | `self.after(50, self._online_tick)` | 每 50 ms 检查 Reader 的最新帧 |
| Reader 循环 | `time.sleep(0.05)` | 每轮读取结束后额外等待约 50 ms |
| 桥接单次同步读取 | 无固定节拍 | 由 CS+ / E1 RAM Monitor 决定，存在长尾 |

因此软件设计的理论轮询间隔约为 50 ms，但完整帧的真实周期为：

```text
完整帧周期 = CS+ 读取耗时 + 约 50 ms 等待
```

在有 `600~800 ms` 长尾时，实际完整帧周期会远大于 100 ms。

## 4. 61247 内存桥

### 4.1 为什么不用 61246

CS+ External Integration Service 的 `csplus.read_memory` 返回的是会丢失前导零的十六进制字符串。对于标量显示可能够用，对于结构体字节流不成立。前导零丢失会改变字节边界，后续 `struct.unpack` 会把错误数据解释成坐标、距离、状态等。

因此当前未采用：

```text
61246 Integration Service -> csplus.read_memory
```

而是采用：

```text
61247 TCP Memory Bridge
  -> CS+ Python Console
  -> debugger.Memory.ReadRange(addr, count, MemoryOption.Byte)
  -> 数值列表转 bytearray
  -> TCP 返回原始字节
```

### 4.2 协议

请求为一行 ASCII 文本，服务端返回二进制帧：

```text
成功：'B' + uint32(length, big-endian) + raw bytes
失败：'E' + uint32(length, big-endian) + UTF-8 error text
```

支持命令：

| 命令 | 说明 |
|---|---|
| `READ <hex-address> <hex-length>` | 按字节读取内存并返回原始数据 |
| `READU <hex-address> <hex-length> <B/H/W>` | 按 Byte/HalfWord/Word 单位读取 |
| `ADDR <symbol>` | 使用 `debugger.Address` 查询符号地址 |
| `OPTIONS` | 返回 `AccessDuringExecution` 等状态 |
| `SETOPT on/off` | 设置运行中访问开关 |
| `PROBE` | 枚举与内存、Watch、实时读取相关的 API |
| `BENCH <addr> <len> <count> [B/H/W]` | 在 CS+ 内执行读取基准测试 |
| `PING` | 健康检查 |
| `HELP` | 返回命令摘要 |
| `STOP` | 只结束当前 TCP 客户端连接，不停止监听线程 |

### 4.3 当前启动方式

当前推荐在 CS+ Python Console 执行：

```python
execfile("D:/TempBridge/bridge_launcher.py")
```

该启动器内部已经加载同一份桥接源码并调用 `csplus_bridge_start()`。

如果 CS+ Console 能正常直接读取源文件，也可以使用：

```python
execfile("D:/Desktop/0911/csplus_memory_bridge.py")
csplus_bridge_start()
```

启动成功时，控制台应出现类似：

```text
csplus_bridge: AccessDuringExecution ... -> True
csplus_bridge: listening on 127.0.0.1:61247
```

健康检查：

```python
csplus_bridge_test()
```

### 4.4 当前停止方式

在 CS+ Python Console 执行：

```python
csplus_bridge_stop()
```

注意：网络协议中的 `STOP` 命令不会停止监听线程，只让当前客户端断开。要真正释放 61247，必须调用 `csplus_bridge_stop()` 或结束对应 CS+ 进程。

### 4.5 运行依赖

桥接正常工作至少依赖：

1. CS+ 已启动并加载当前 `.mtpj` 工程。
2. E1 调试会话已建立且目标处于可访问状态。
3. CS+ Python Console 中 `debugger` 对象存在且对应当前调试会话。
4. `debugger.Memory.ReadRange` 可用。
5. E1/LPD RAM Monitor 可访问目标 RAM 区域。
6. `127.0.0.1:61247` 未被其他进程占用，桥接监听线程正常。
7. 上位机使用 Python 3.10 运行 GUI。
8. GUI 中连接方式选择 `CS+`，不要选择 Lauterbach。

## 5. 结构体地址与解析布局

以下地址是此前在线调试时解析到的地址，必须视为“当前目标镜像的有效地址”，重新下载、重编译、修改链接配置后要重新通过 `ADDR` 查询确认。

| 符号 | 地址 | 长度 | 解析用途 |
|---|---:|---:|---|
| `sf_Upper_PointOutSignal` | `0xFEBD2C9C` | 800 | 80 个点云障碍物，每项 10 字节 |
| `sf_Upper_LineOutSignal` | `0xFEBD2FBC` | 280 | 20 条线段障碍物，每项 14 字节 |
| `sf_Upper_StatusOutSignal` | `0xFEBD30D4` | 16 | 档位、温度、速度、时间戳 |
| `sf_Upper_OdoOutSignal` | `0xFEBD30E4` | 12 | `odo_x`、`odo_y`、`odo_ang`，三个 float |
| `sf_Upper_VehicleOutSignal` | `0xFEBD30F0` | 52 | 车长、车宽、12 个探头位置 |
| `sf_Upper_RawDataOutSignal` | `0xFEBD3124` | 246 | 12 个探头原始回波和同频标志 |
| `sf_Upper_PDCOutSignal` | `0xFEBD321A` | 52 | 12 探头 PDC 距离、区间、故障 |
| `sf_Upper_SlotOutSignal` | `0xFEBD3250` | 296 | 6 个车位 A..F 点数据 |

### 5.1 解包格式摘要

```text
Status : <BxHfQ                         # 16 字节
Odo    : <fff                           # 12 字节
Vehicle: <HH + hh*12                    # 52 字节
PDC    : <BBBx + HBB*12                 # 52 字节
Point  : <HhhBBBB * 80                  # 每项 10 字节，共 800
Line   : <BBBBhhhhH * 20                # 每项 14 字节，共 280
Raw    : <HHBB + BxHHHHHHHHH * 12       # 246 字节
Slot   : 基址偏移 8，stride 48
         <QBBHHhhBx + hhhhhhhhhh + Bx
```

`Slot` 结构按 8 字节对齐解释：头部 8 字节，随后 6 条槽位数据，每条 48 字节，总计 296 字节。代码还保留了通过调试器表达式校验布局的可选逻辑，但当前默认布局是固定 `(offset=8, stride=48)`，不依赖每次运行时做表达式解析。

## 6. 批量预取机制

`ReadDataPort_CSPlus.py` 中 `CSPLUS_BRIDGE_BATCH_ENABLED=True`，每帧开始时清空缓存，然后按符号地址排序并合并相邻区域。当前 8 个结构体实际合并成一个区域：

```text
起点：0xFEBD2C9C
长度：0x6DC = 1756 字节
终点：0xFEBD3378
```

当前合并参数：

```text
CSPLUS_BRIDGE_BATCH_GAP = 256 字节
CSPLUS_BRIDGE_BATCH_TTL = 0.25 秒
```

因为相邻结构体之间的最大空隙不超过 256 字节，所以当前布局下：

```text
第一帧每轮读取 = 1 次 READ 1756 字节
```

之后各读取函数只是从缓存切片解析，不再分别发起 TCP 请求。缓存会在每帧开始时清空，避免把上一帧数据当成当前帧。批量预取失败时会临时禁用批量模式 5 秒，回退为单结构体读取；这能保功能，但会增加请求次数和长尾概率。

## 7. 超时提示和统计

当前配置：

```text
CSPLUS_BRIDGE_ENABLED       = True
CSPLUS_BRIDGE_STANDALONE    = True
CSPLUS_BRIDGE_BATCH_ENABLED = True
CSPLUS_BRIDGE_ONLY          = True
CSPLUS_BRIDGE_HOST          = 127.0.0.1
CSPLUS_BRIDGE_PORT          = 61247
CSPLUS_BRIDGE_TIMEOUT       = 5.0 秒
CSPLUS_BRIDGE_SLOW_WARN_MS  = 200
CSPLUS_BRIDGE_SLOW_WARN_COOLDOWN = 2.0 秒
CSPLUS_BRIDGE_STATS_WINDOW  = 20
```

超过 200 ms 的读请求会触发提示，格式已经固定为：

```text
CS+ 桥接读取超时提示，本次完整读取耗时 <本次耗时> ms，最近20次平均完整读取 <平均值> ms
```

统计规则：

- 只统计 `READ` / `READU` 请求。
- 当前批量模式下，一次批量 `READ` 基本等同于一次完整结构体读取，因此“完整读取”文案符合当前主路径。
- 如果批量预取被禁用，后续单结构体读取会产生多个请求，统计窗口记录的是每个请求，不应把其中一条直接当作完整帧总耗时。
- 同类慢提示有 2 秒冷却，避免 UI 被重复日志刷屏。
- 超过 `5.0` 秒没有收到响应会触发硬超时，并关闭当前连接。

## 8. 实测性能与根因

### 8.1 当前已知的历史测试数据

最近一次 50 次读取测试：

| 读取长度 | 平均值 | 中位数 | P95 | 最大值 |
|---:|---:|---:|---:|---:|
| 1 字节 | 137.0 ms | 20.6 ms | 716.9 ms | 785.3 ms |
| 1756 字节 | 124.2 ms | 20.4 ms | 672.1 ms | 757.7 ms |

关键观察：1 字节和完整 1756 字节的长尾几乎相同，说明请求大小不是根因。

短暂停核访问实验：

- 设置 `AccessDuringExecution=False`、`AccessStopExecution=True` 后，多数读取约 `2~4 ms`。
- 但仍出现 `330~735 ms` 的长尾。
- 连续多轮平均约为 `43.3、38.0、55.1、72.1、84.9 ms`，不稳定满足每次 `<100 ms`。
- 这种模式会暂停/干扰目标执行，不适合作为常规实时显示方案。

### 8.2 已排除的路径

以下检查没有发现可以直接消除长尾的开关：

- `debugger.Option.ThreadLock` 读取时报 `AttributeError`，不能作为可调锁参数。
- `OPTIONS` 的 `AccessDuringExecution` 可以切换，但不是缓存、快照或读取队列。
- `PROBE` 没有发现隐藏的 RAM Monitor 周期、缓存或快照 API。
- `debugger.Watch.GetValue()` 对完整结构体返回 `"-"`，不能替代结构体内存读取；标量 Watch 读取也会出现 400 ms 级长尾。
- TCP loopback、批量预取、`struct.unpack` 都不是长尾来源。

### 8.3 官方文档给出的边界

CS+ RH850 调试帮助确认：

- E1 支持运行中访问内部 RAM。
- 实时显示更新的最小设置单位为 `100 ms`，默认值为 `500 ms`。
- RAM Monitor 读取遇到 CPU 进入 HALT/STOP/IDLE 等情况会发生 monitor timeout。
- 未发现公开的“可复用快照缓存”或“一次性导出完整实时结构体”API，可绕过当前同步读取锁。

### 8.4 结论

当前问题的根因是 CS+ / E1 RAM Monitor 的同步访问机制和内部锁，不是：

```text
数据量太大
TCP 太慢
Python 解析太慢
批量预取没有合并
```

因此不能通过继续缩短 `time.sleep(0.05)`、增加线程或把 1756 字节拆成更多小请求来稳定达到 100 ms。拆分请求反而可能触发更多长尾。

## 9. 100 ms 目标评估

用户的实际目标是“完整 1756 字节帧稳定逐帧显示，单帧不超过 100 ms”。

当前方案的评估：

| 指标 | 当前结果 | 是否满足 |
|---|---|---|
| 典型读取 | 约 20 ms | 满足 |
| 软件轮询间隔 | 约 50 ms | 设计上满足 |
| P95 | 约 670~717 ms | 不满足 |
| 最大读取 | 约 757~785 ms | 不满足 |
| 连续稳定 100 ms | 未达到 | 不满足 |

结论必须明确：

> 在当前 CS+ Python Console 同步 `debugger.Memory.ReadRange()` + E1 RAM Monitor 路径上，无法可靠承诺完整帧 100 ms 内返回。若产品验收要求是“每次完整逐帧显示都不超过 100 ms”，当前桥接方案不应作为最终方案。

## 10. 可行的后续方向

按推荐优先级排列：

### 方案 A：目标端专用数据通道

由目标程序把最新显示帧写入环形缓冲或固定共享区，并通过 UART、CAN、Ethernet、USB 或专用测试接口传输到上位机。该方案不依赖调试器 RAM Monitor，最有机会稳定满足 100 ms。

关键要求：

- 帧数据带序号/时间戳/完整性标志。
- 上位机只接收完整帧，不直接读取运行中的多个结构体。
- 目标端维持最新快照，PC 端丢掉旧帧而不是排队。

### 方案 B：目标端环形缓冲 + CS+ 读取最新完整帧

由目标端维护一个连续的“最新帧缓冲区”，每个周期写入数据并最后更新序号。PC 仍通过 61247 读取，但每次只读取一个固定区域，并用序号和校验判断是否获得完整帧。

优点：解决多结构体非原子读取和混帧问题。  
限制：仍然可能受 CS+ RAM Monitor 长尾影响，不能保证 100 ms。

### 方案 C：CS+ 后台采样器 + GUI 最新帧

让 CS+ 侧独立线程持续采样，GUI 只读取最新缓存帧，不把 CS+ 同步读取直接挂在 GUI 更新路径上。

优点：GUI 不会被一次 700 ms 读取卡住。  
限制：只会改善“界面卡顿”和显示新鲜度，不会消除底层采样长尾。

### 方案 D：更换调试器/采集方案

如果必须依赖调试接口，评估 Lauterbach 等具有更快内存采样、Trace/实时采集能力的工具。该方向需要重新验证目标端访问和稳定性。

### 方案 E：仅用于低频诊断

如果把 CS+ 实时逐帧显示降级为“低频诊断/标定”，可继续使用当前桥接，但应把验收指标改为容忍秒级阻塞，并在 UI 中明确显示数据陈旧时间。

## 11. 已知风险和注意事项

1. **不要边读边下载/重启调试会话。** 当前桥接与 CS+ 下载/调试操作会互相干扰，曾出现 `E1203074 CPU did timeout` 和 `Download failed`。
2. **不要把 HALT/STOP/IDLE 当成读取前提。** 这会导致 RAM Monitor timeout，且短暂停核模式本身也不能消除长尾。
3. **不要在 CS+ Console 丢失 `debugger` 后继续使用旧监听。** 当前快照已出现 61247 监听存在但 `debugger` 未定义的情况，必须重新加载桥接。
4. **不要在重新下载后复用旧地址。** `sf_Upper_*` 地址有可能变化，必须重新执行 `ADDR` 查询。
5. **不要同时运行多个桥接实例。** 61247 只能有一个监听者；旧进程会造成端口占用或旧上下文继续服务。
6. **不要让普通 PowerShell/编辑器以加密视图覆盖源码。** 本机存在透明加密文件访问差异，优先使用已验证的 Python 3.10 和备份文件。
7. **GUI 与其他处理模块的线程安全要维持现状。** 在线数据由 Reader 线程写入 `DataSheet`，GUI 通过最新帧快照显示；不要直接在 GUI 线程增加同步内存读取。
8. **`D:\Desktop\0911` 的 GUI 比 `new` 工作区旧。** 同步工程时要明确同步的是运行目录中的完整文件集合，而不是只同步 CS+ 读取模块。

## 12. 恢复运行前的检查清单

1. 启动 CS+，加载当前 `.mtpj` 工程。
2. 连接 E1，确认目标进入预期的运行状态。
3. 打开 CS+ Python Console，确认当前上下文存在 `debugger`。
4. 执行：

   ```python
   execfile("D:/TempBridge/bridge_launcher.py")
   ```

5. 在 CS+ Console 执行健康检查：

   ```python
   csplus_bridge_test()
   ```

6. 在上位机执行 PING 或查看 61247 是否监听。
7. 在上位机选择 `CS+` 后端后启动在线连接。
8. 观察 GUI 状态栏和超时提示，不要在执行下载/刷新目标时启动实时读取。
9. 调试结束后执行：

   ```python
   csplus_bridge_stop()
   ```

10. 如果目标工程重新编译或重新下载，重新确认所有 `sf_Upper_*` 地址。

## 13. 后续 TODO

- [ ] 明确产品验收口径：是否真的要求“每次完整帧 `<100 ms`”，还是允许多数帧 100 ms、偶发长尾。
- [ ] 如果要求严格 100 ms，确认是否有可用 UART/CAN/Ethernet 或目标端测试数据通道。
- [ ] 如果只能保留 CS+ 路径，优先设计“目标端环形缓冲 + 序号/时间戳”的完整性方案。
- [ ] 把 GUI 从“同步等待一帧”改造成“后台采样 + 最新帧显示”，避免 CS+ 长尾阻塞交互。
- [ ] 将 `new\VehUpperDemo.py` 与 `D:\Desktop\0911\VehUpperDemo.py` 做一次明确同步，避免运行副本使用旧界面。
- [ ] 归档 `_csplus_docs`、临时 PNG、`p.py`/`q.py`/`probe_watch.py` 等实验文件，保留可复现实验记录。
- [ ] 如果继续研究 CS+ API，只把 `BENCH`/`PROBE` 当作验证工具，不再用它们假设存在未公开的实时缓存开关。

## 附录 A：当前代码指纹

以下是 2026-09-11 梳理时的逻辑源码 SHA256 前缀，可用于确认后续修改是否影响当前基线：

```text
D:\Desktop\upper_demo\Reasa\new\DataSheet.py
  0ee189d5beaed965

D:\Desktop\upper_demo\Reasa\new\OnlinePort.py
  e0f2788fb3a6d9f6

D:\Desktop\upper_demo\Reasa\new\ReadDataPort_CSPlus.py
  8736e0803c5aa118

D:\Desktop\upper_demo\Reasa\new\VehUpperDemo.py
  01bf0fd724c28e40

D:\Desktop\0911\csplus_memory_bridge.py
  2c90a728b7a95499

D:\TempBridge\bridge_launcher.py
  cd9b22ef1a93af40
```

## 附录 B：常用命令

运行 GUI：

```powershell
C:\Python310\python3.exe D:\Desktop\upper_demo\Reasa\new\VehUpperDemo.py
```

运行 1756 字节桥接基准：

```powershell
C:\Python310\python3.exe D:\Desktop\upper_demo\Reasa\new\csplus_bridge_bench.py --addr 0xFEBD2C9C --length 1756 --count 20 --units B,H,W
```

在 CS+ Python Console 启动/停止桥接：

```python
execfile("D:/TempBridge/bridge_launcher.py")
csplus_bridge_test()
csplus_bridge_stop()
```

## 附录 C：结论保留

当前工程已经解决了“结构体读取必须字节无损”的正确性问题，但没有解决“CS+ 调试接口稳定 100 ms 实时读取”的性能问题。后续决策应围绕数据通道和验收口径展开，而不是继续优化 61247 的 Python 解析或 TCP 代码。
