# V3.5 UDP 接入

在「设备与显示」的 Hardware 下拉框选择「UDP」，点击「UDP 设置」编辑本机监听 IP、监听端口和接收来源设备 IP，保存后点击「在线连接」。当前工程的统一入口仍为 `src/app.py`，可运行 `scripts/run_viewer.ps1` 启动。

## 网络配置

`config/viewer.toml` 和 `config/ubuntu_config.toml` 提供：

```toml
[udp]
bind_address = "192.168.98.123"
port = 39001
sender_address = "192.168.98.233"
```

`bind_address` 是本机网卡地址，也可填 `0.0.0.0` 监听所有本机网卡；设备向本机实际 IP 和监听端口发送数据。`sender_address` 是接收来源设备的 IPv4 地址，设备源端口可以变化。上位机只监听，无启动指令或心跳。本机需具备指定的监听地址；地址不存在或端口占用会显示连接错误。端口范围为 `1..65535`，保存和连接前会校验地址格式与端口范围。

界面的「保存设置」将三个参数保存到当前用户的配置目录，优先于 TOML 默认值，重启软件后仍有效。Windows 路径为 `%APPDATA%/COLIGEN_USS_UPPER/udp_settings.json`；Ubuntu 路径为 `$XDG_CONFIG_HOME/coligen-uss-upper/udp_settings.json`，未设置 XDG 路径时使用 `~/.config/coligen-uss-upper/udp_settings.json`。测试或便携部署可用 `COLIGEN_CONFIG_DIR` 指定配置目录。

连接期间不能编辑设置，先断开再修改。取消或保存失败不会修改正在使用的参数。侧栏直接填写端口可临时覆盖本次连接，切换数据源时分别保留 UDP 与 TRACE32 的端口；需要重启后保留时请在「UDP 设置」中保存。

未保存过界面设置时使用 `[udp]` 默认值。发布程序也支持在 EXE 同级放置 `viewer.toml` 覆盖内置 TOML 默认值。

「TCP/IP」仍使用 `[ethernet]` 的独立 512 字节接口，相关设置不作用于这里的 USSD 协议。

## 报文和周期

每个 UDP 数据报包含一个 80 字节报文：

| 偏移 | 长度 | 内容 |
| --- | --- | --- |
| 0 | 4 | ASCII `USSD` |
| 4 | 1 | 版本 `1` |
| 5 | 1 | CAN 类型 `0xFF` |
| 6 | 2 | 负载长度 `64`，小端 |
| 8 | 4 | 29 位 CAN ID，小端 |
| 12 | 4 | 包头毫秒时间戳，小端 |
| 16 | 64 | CAN FD 数据，按 IPC DBC 解码 |

DBC 为 `assets/dbc/IPC_matrix_UssDebugDataMCUtoSOC_V1.0_20261019_D4M6.dbc`。Windows 和 Ubuntu 打包配置均包含该文件；运行时支持从程序同级 `assets/dbc/` 加载。

接收 ID 为 `0x10000768..0x10000782`，共 27 种。以首 ID `0x10000768` 开始、末 ID `0x10000782` 结束，仅发布包含全部消息的完整周期。包头时间戳允许跨毫秒边界，支持 32 位回绕；缺包、重复 ID 或中途接入时等下一完整周期，晚到的旧周期不回退画面。

## 显示与录制

- 80 点、20 线的坐标由 DBC 的 cm 转为画布 mm，沿用 V3.5 的坐标方向；点 ID、线段编号分别保留。
- 12 路回波和 PDC 距离保持 cm，里程计保持 DBC 的 mm。完整周期同步发布 PDC 声音样本，故障探头不参与告警。
- 沿用当前工程的 20 PROBE 显示方案、车型与探头配置。IPC 没有车位数据，周期更新会清除其他来源遗留的车位。
- 显示和录制采用状态消息内的设备微秒时间戳，TXT 使用 `TimeStamp_us` 明确单位，回放和再次录制保留原值。原有 `TimeStamp_1ms` 日志继续按原方式读取。
- 状态栏显示收包、DBC 解码、完整更新、异常和不完整周期计数。2 秒没有完整周期时显示「等待数据」；PDC 声音遵循现有告警超时。

## 验证

```powershell
uv run pytest -q tests/test_udp_settings.py tests/test_udp_online_port.py tests/test_hardware_selection.py
```

测试使用 V3.5 的完整周期抓包样本，覆盖协议校验、坐标和字段解码、跨毫秒组帧、丢包恢复、时间戳回绕、IP 过滤、按保存参数进行本机 UDP 收包、端口释放、超时、界面路由、PDC 样本和录制回放。设置测试覆盖地址校验、保存与重读、保存失败保护、取消和连接参数传递。设备网络和实车数据仍需现场联调。
