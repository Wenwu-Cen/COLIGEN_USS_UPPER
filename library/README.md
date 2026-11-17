# Windows x64 厂商运行库

本目录提供连接设备的用户态库，USB/硬件驱动仍需安装厂商驱动。

```text
library/
├── vxlapi64.dll
└── windows/x86_64/
    ├── zlgcan.dll
    └── kerneldlls/
```

ZLG 通过 `src/zlg_can_bus.py` 直接调用 ZCAN SDK，仅初始化所选物理通道，支持 USBCANFD-100U/200U/400U/800U。不依赖旧 PyPI zlgcan/zlgcan-driver 和 bitrate.cfg.yaml。主 DLL 只保留 `windows/x86_64/zlgcan.dll`；`kerneldlls` 是厂商匹配的设备插件和属性资源，包含 800U 支持，需保持完整。

Vector 通过 python-can 加载 `vxlapi64.dll`，使用 Vector Hardware Configuration 的应用通道映射。当前交付支持 x64，不携带闲置的 32 位 XL 库。

运行 `scripts/check_runtime.ps1` 检查必要文件；Windows spec 将其打包到 EXE 的 `runtime_assets/library`。升级 SDK 时同步匹配的内核与属性资源，并重新构建验证。缺 DLL 或系统依赖可能报 error 126，缺设备插件/资源可能导致 OpenDevice/SetValue 失败。

TOSUN 通过 `src/tosun_can_bus.py` 调用 `windows/x86_64/tosun/libTSCAN.dll`，配套 `libTSH.dll` 来自本机 TSMaster bin64，支持 TC1018 所选物理 CAN1～CAN12。主 DLL 与依赖放在同一目录并随 Windows EXE 打包，不调用 Vector XL。
