# 文档索引

日常操作先查两份手册。协议细节、固件联调和构建集中在下方。

## 日常使用

- **[使用手册](USER_GUIDE.md)**。设备连接、日志回放、时钟、地图和点线快照。
- **[录制与回灌手册](RECORDING.md)**。仅采集与实时比对、S20 / D4M3 / E211 的输入来源、导出和单步调试。

## 设备与协议联调

- **CAN FD**。厂商驱动、设备型号和通道设置见 [CAN 硬件](interfaces/CAN_HARDWARE.md)。S20 可视化报文见 [S20 UC CAN v1](interfaces/S20_UPPER_CAN_V1.md)。
- **XCP**。CAN FD、TCP/IP、UDP/IP 的参数、符号和原生结构体见 [XCP](interfaces/XCP.md)。
- **网络**。17 探头的 512 字节协议见 [USS 以太网](interfaces/ETHERNET_INTERFACE.md)。USSD / IPC DBC 见 [UDP 接口](interfaces/UDP_INTERFACE.md)。
- **UART**。USSV 帧、校验及底软移植见 [串口协议](interfaces/SERIAL_PROTOCOL.md)。

## 坐标与车型

- [坐标与单位](reference/COORDINATE_SYSTEMS.md)汇总各数据源轴向、单位和旧日志兼容规则。
- [世界地图与轨迹](reference/WORLD_MAP.md)说明位姿、重构和地图导出。
- [车型与探头](reference/VEHICLE_PROFILES.md)说明后轴、探头安装参数和 JSON 交换。

## 开发维护

- [开发维护与发布](maintenance/DEVELOPMENT.md)包含启动、构建、自检、界面实现及三仓发布流程。
- [Ubuntu 使用与构建](maintenance/UBUNTU_RELEASE.md)说明依赖、目录和本地打包。
- [Git 解密差异](maintenance/GIT_DECRYPT_DIFF.md)说明授权环境中的历史源码查看方式。
- [变更日志](CHANGELOG.md)按版本记录历史变更。
