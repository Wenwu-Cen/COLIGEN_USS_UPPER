# CAN 硬件与通道选择

点击「设备与显示」，在「设备连接」中选择数据源。参数按当前 Windows 用户保存，重新启动后恢复；连接期间禁止修改，断开后可重新选择。

`ZLG-USBCANFD` 支持 USBCANFD-100U、200U、400U、800U。选择设备型号、硬件索引 0～99、通道索引 0～7；硬件索引表示同型号设备的驱动枚举序号。程序检查所选型号和设备实际通道数：100U 可用通道 0，200U 为 0～1，400U 为 0～3，800U 为 0～7。选择较少通道的型号时，之前超出范围的通道会回到 0。

接收端直接调用工程附带的 ZLG `zlgcan.dll`，仅初始化所选的一个物理通道。Windows 64 位 SDK 的句柄按指针传递；经典 CAN 和 CAN FD 都保留原始报文 ID、数据、微秒时间戳和实际通道号。程序使用现有 `library/windows/x86_64/kerneldlls/USBCANFD800U.dll` 支持 800U。

`CANoe/Vector` 显示 CAN1～CAN10，分别传入 Vector XL 应用通道索引 0～9。它们对应 Vector Hardware Configuration 中 `CANoe` 应用的通道分配；例如选择 CAN10 时打开应用通道索引 9。波特率、CAN FD 数据波特率及应用名称继续沿用 `config/can_upper_config.toml`。

用户选择保存在 `%APPDATA%/COLIGEN_USS_UPPER/can_hardware.json`；设置了 `COLIGEN_CONFIG_DIR` 时使用该目录。首次启动没有用户配置时沿用 TOML 默认值：200U、硬件 0、通道 0，以及 Vector CAN1。

验证涵盖硬件/通道边界、型号通道数、配置恢复、选择到驱动参数的传递、只初始化指定通道、CAN/CAN FD 接收、初始化失败释放和断开中止。800U 及 Vector CAN10 的实体设备收包仍需现场验证。

接口依据：[ZLG 产品通道说明](https://www.zlg.com/can/can/product/id/223.html)、[python-can Vector 配置](https://python-can.readthedocs.io/en/stable/interfaces/vector.html)、现有 zlgcan 包上游所带的 [Windows SDK 头文件](https://github.com/jesses2025smith/zlgcan-driver/blob/dev/zlgcan/windows/x86_64/zlgcan/zlgcan.h)。
