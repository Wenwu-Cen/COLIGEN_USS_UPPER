# E2 读取与显示性能验证：v3.13.0

日期：2026-11-12。Windows 本机 CS+ / RH850 E2，当前打开的调试工程为 S73。结果为本次现场样本，不作为所有目标板和调试配置的实时性保证。

## 主要原因与修复

开启 `common.ViewOutput` 时，CS+ 的 `debugger.Memory.ReadRange` 会向 Python Console 输出读取结果。本项目每轮批量读取 1756 字节，输出大量数值导致 IDE 文本刷新形成秒级长尾。内存桥 v6 在已串行化的内存访问中临时关闭结果输出，并在正常返回或抛出异常时恢复原设置；未永久关闭操作员的 Console 输出。

[Renesas 的 common.ViewOutput 说明](https://tool-support.renesas.com/autoupdate/support/onlinehelp/csp/V5.00.00/CS%2B.chm/PythonConsole.chm/Output/py_Python_property10.html)确认该属性控制 CS+ Python 函数结果和错误的 Console 显示。根因判断基于下述现场开关对照，而非仅凭文档推断。

上位机在线连接会检查 `VERSION` 并自动更新旧桥。热更新保留原有监听 socket、线程和内存锁，避免在同一端口重新绑定的窗口；仍使用原来 61247 端口和 Byte 无损读取。Word / HalfWord 在不同轮次中没有稳定收益，本版未据此修改默认读取单位。

界面取消每轮 `WM_SETREDRAW` 加全窗口 `InvalidateRect`，让 Tk 合并局部脏区。点位增删只安排新增图元位置，原有图元不再逐个提升层级；如果源数据顺序改变，仍纠正完整层级，测距和时钟继续位于上方。车型数据未改变时复用校验结果，状态栏颜色未改变时只改文字。

成功慢读保留 Hz / 读取耗时 / P95 / 距接收时间，不再每两秒新建一个红色错误窗口；真正的硬超时、连接失败和数据校验失败仍正常报告。

## E2 实测

先暂停上位机采集，确保只有一个测速客户端。通过 debugger.Address 解析当前符号，连续区域为 `0xFE402E18` 起 1756 字节；该地址仅描述当前编译产物，上位机仍动态解析，不能跨编译复用。

1. Console 输出对照：True → False → False → True，每组 12 次，共每种状态 24 次。同为 Byte 读取。开启时平均 567.29 ms、P95 2226.62 ms、最大 2274.80 ms；关闭时平均 36.49 ms、P95 94.58 ms、最大 120.38 ms。结束后恢复原设置。原始记录：`build/e2-performance/console-output-benchmark.json`。
2. 正式 v6 的临时抑制与恢复：40 次 Byte 整块读取，平均 59.24 ms、中位 46.29 ms、P95 127.78 ms、最大 135.28 ms。作用域设置和恢复包含在该时延内。记录：`build/e2-performance/bridge-v6-benchmark.json`。
3. 修复后 Byte/HalfWord/Word 各 24 次，状态结构体全部通过校验；车身参数静态区域三种单位字节一致。Byte 平均 50.69 ms、HalfWord 47.80 ms、Word 45.75 ms，此差异不足以保证所有轮次获益。记录：`build/e2-performance/quiet-unit-benchmark.json`。
4. 源码 GUI 完整在线测试约 12 秒，数据详情 RAW 页打开：观察约 14.67 帧/秒，末尾窗口统计 14.99 Hz、最近 60 帧 P95 94 ms；179 个完整快照已由 Reader 发布，无读取异常或错误窗口。GUI tick 平均 2.09 ms、P95 4.18 ms；画布更新函数平均 1.91 ms、P95 2.93 ms。事件循环仍可能受启动、系统调度和窗口绘制影响，本次心跳最大延迟 594 ms，不能声称界面从此没有任何停顿。记录：`build/e2-performance/live-e2-source.json`。

输出完全关闭的 36 ms 是根因对照数据，正式桥接采用临时关闭并恢复，不应把该数值当成正式上位机的稳定周期。前后数据在同机现场不同时段测量，有调度波动；主要改善是消除 Console 刷屏造成的秒级阻塞。

## 画布对照

同一进程、同一窗口，模拟最多 80 点、20 线、12 探头回波与 6 车位，点数交替变化。按旧 → 新 → 新 → 旧顺序测试，每种渲染路径 120 个计时样本，包含 `app.update()` 绘制事件处理。

旧实现平均 23.46 ms、P95 34.28 ms；新实现平均 11.99 ms、P95 17.29 ms。该数据是可重复模拟场景，不能替代实车刷新率。记录：`build/e2-performance/canvas-optimized.json`。

## 实车变量来源

用户指定工程：`D:/Cenww_work/SF26088_S20/SF26088_S20_Project`。

- 宏：`Source/USS_APP/UssProcess/Headfile/sfType.h` 中启用 `LAUTERBACH_UPPER_DEBUG`。
- 定义与布局：`Source/USS_APP/UssProcess/Libfile/Uss_Drv/uss_sensor/LauterbachUpper/Lauterbach_Var.h` 与 `.c`。
- 变量：`sf_Upper_PointOutSignal[80]`、`sf_Upper_LineOutSignal[20]`、`sf_Upper_StatusOutSignal`、`sf_Upper_OdoOutSignal`、`sf_Upper_VehicleOutSignal`、`sf_Upper_RawDataOutSignal`、`sf_Upper_PDCOutSignal`、`sf_Upper_SlotOutSignal`。
- 车况/车身/车位输出调用已在 `PDC/source/VehSigInterface.c` 核对；宏名不限制 CS+ 使用，这些是编入固件的可读全局变量。

本版未修改、重编译或烧写实车固件。当前 S73 调试工程的实际符号由 CS+ 解析，与所核对的结构体数量及读取长度吻合。

## 运行

关闭旧版上位机，保持 CS+ 目标工程和调试连接就绪，启动 `dist/COLIGEN_USS_UPPER_CAN_v3.13.0.exe`，选择「Renesas CS+」后点击「在线连接」。软件会确认或更新内存桥 v6，已有 Console 结果显示设置会在每次内存访问后恢复。

## 回归与发行验证

共 97 项相关测试通过：CS+ / 车型数据模型 82 项、版本 2 项、时钟 4 项、平移/滚轮 3 项、硬件选择 1 项，以及定向 GUI 5 项。覆盖输出恢复、异常、并发、旧桥升级、采集流水线、车型复用与图元层级。部分 Windows GUI 用例在同一进程多次初始化 Tk 时遇到既有 Tcl 资源加载问题，改用独立进程执行通过；未将该环境错误当作应用功能失败隐藏。

实际加载旧 v5 桥后，调用正式 `read_port_connect()` 路径自动更新到 v6，返回连接成功，随后连续读到 1756 字节；5 次样本约 17～98 ms。记录：`build/e2-performance/actual-v5-upgrade.json`。

Windows 单文件自检包含内存桥 v6 载荷、Console 单命令长度、CAN 回放、TRACE32 模块、CAN 厂商库、17 探头以太网、车型配置和滚轮。最终检查结果保存在 `build/e2-performance/validation-3.13.0.json`。
