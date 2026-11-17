# CAN 硬件与通道选择

点击「设备与显示」，在「设备连接」中先选择 `CAN`，再选择 `ZLG`、`TOSUN` 或 `VECTOR`，下方显示对应设备与通道。参数按当前 Windows 用户保存，重新启动后恢复；连接期间禁止修改，断开后可重新选择。

`ZLG-USBCANFD` 支持 USBCANFD-100U、200U、400U、800U。选择设备型号、检测到的硬件索引及该设备可用通道；硬件索引表示同型号设备的驱动枚举序号。程序检查所选型号和设备实际通道数：100U 可用通道 0，200U 为 0～1，400U 为 0～3，800U 为 0～7。选择较少通道的型号时，之前超出范围的通道会回到 0。硬件索引由后台检测获取，单台设备通常只有索引 0，多台设备显示检测到的索引；刷新设备可重新检测。未检测到可用设备时禁止连接，不提供固定 0～99 选项。扫描仅使用公开 OpenDevice/GetDeviceInf/CloseDevice 读取信息，不初始化或启动 CAN。

接收端直接调用工程附带的 ZLG `zlgcan.dll`，仅初始化所选的一个物理通道。Windows 64 位 SDK 的句柄按指针传递；经典 CAN 和 CAN FD 都保留原始报文 ID、数据、微秒时间戳和实际通道号。程序使用现有 `library/windows/x86_64/kerneldlls/USBCANFD800U.dll` 支持 800U。

`VECTOR` 增加设备型号：VN1610（2 路 CAN）、VN1611（1 路 CAN）、VN1630/VN1630A/VN1630 LOG（最多 4 路）、VN1640/VN1640A/VN1641（最多 4 路）、VN1670（最多 10 路 CAN）与 CANcaseXL（2 路经典 CAN）。实际通道还取决于收发器、扩展板及驱动报告，连接时只选 CAN 接口，排除 LIN/FlexRay，CAN1 表示所选设备的第一个可用 CAN 接口。VN1630(A)、VN1640(A) 各自共用 XL 硬件类型编号。具体型号直接连接首个匹配设备；多设备可在 `[canoe].serial` 指定序列号。CANcaseXL 自动关闭 FD。

旧配置默认 `CANoe 应用映射`，保留 CAN1～CAN10 与 `[canoe].app_name` 的 Vector Hardware Configuration 应用映射。具体型号模式绕过应用映射，避免选择的型号与实际连接设备不一致。

用户选择保存在 `%APPDATA%/COLIGEN_USS_UPPER/can_hardware.json`；设置了 `COLIGEN_CONFIG_DIR` 时使用该目录。首次启动没有用户配置时沿用 TOML 默认值：200U、硬件 0、通道 0，以及 Vector CAN1。

验证涵盖硬件/通道边界、型号通道数、配置恢复、选择到驱动参数的传递、只初始化指定通道、CAN/CAN FD 接收、初始化失败释放和断开中止。800U 及 Vector CAN10 的实体设备收包仍需现场验证。

接口依据：[ZLG 产品通道说明](https://www.zlg.com/can/can/product/id/223.html)、[python-can Vector 配置](https://python-can.readthedocs.io/en/stable/interfaces/vector.html)、现有 zlgcan 包上游所带的 [Windows SDK 头文件](https://github.com/jesses2025smith/zlgcan-driver/blob/dev/zlgcan/windows/x86_64/zlgcan/zlgcan.h)。

## TOSUN（同星 TC1018）

数据源选择 `CAN`，设备选择 `TOSUN`，选择物理 CAN1～CAN12，直接传给同星 SDK 的通道索引 0～11；与 Vector CANoe 应用通道映射独立。通道选择按用户保存，连接期间禁止修改，断开后恢复。

`config/viewer.toml` 的 `[tosun]` 独立配置仲裁/数据波特率（默认 500K/2M）、CAN FD、120Ω 终端电阻、监听模式与设备序列号。序列号为空时打开首个可用设备，多设备时填写指定序列号。选择设备不支持的通道时 SDK 返回错误，不会改为其他通道。

Windows x64 包自带 `library/windows/x86_64/tosun/libTSCAN.dll` 和匹配的 `libTSH.dll`。源码运行也可通过 `TOSUN_LIBRARY_DIR` 指定含 DLL 的目录，或使用本机 TSMaster 的 bin64。当前 Ubuntu 菜单不提供 TOSUN 在线接口。

接收端仅配置所选通道，使用 RX FIFO 接收经典 CAN/CAN FD，保留 ID、FD/BRS/ESI 标志、物理通道与微秒硬件时间戳；连接失败释放资源，断开可中止等待。所有接收报文进入已有 DBC / [S20 UC 完整快照解析](S20_UPPER_CAN_V1.md)。

依据：[同星官方 SDK 头文件](https://github.com/TOSUN-Shanghai/libTSCANDemos/blob/main/include/windwos/libTSCAN.h)、[TC1018 12 通道说明](https://www.tosunai.com/wp-content/uploads/2024/01/TC1018_Datasheet_EN.pdf)。已验证模拟 SDK 和打包 ABI，实体设备及实车效果需现场验证。

## 型号联动（v4.6.1）

TOSUN 型号：TC1011、TC1012/TC1012P（1 路）；TC1013/TC1013 Pro（2 路）；TC1014/TC1014 Pro、TC1016/TC1016P（4 路）；TC1017/TC1017 Pro（8 路）；TC1018/TC1018 Pro（12 路）。`自动识别` 保留旧配置行为，提供最多 12 路选项，连接时以实际通道数校验；具体型号按 SDK 产品名称精确匹配，避免把基础型号与 Pro 混用。多台同型号设备可通过 `[tosun].serial` 指定序列号。

所有型号改变会更新通道列表，超出新范围时归 CAN1（ZLG 归索引 0），保存选择并在连接期间禁用型号、索引与通道修改。设备未接入或选定通道未安装 CAN 收发器时给出错误，不会换到另一型号或跨设备拼接通道。

型号数据依据：[同星硬件目录](https://www.tosunai.com/product-category/hardware/)、[Vector VN1600 官方规格](https://www.vector.com/en/product/vn1600/)、[python-can 4.6.1 Vector 接口](https://python-can.readthedocs.io/en/v4.6.1/interfaces/vector.html)。VN1670 的 15 路总线包含 LIN，当前 CAN 上限为 10 路。
