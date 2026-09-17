# library/ 目录说明（zlgcan 官方 python-can 后端）

运行时传给 `zlgcan` 的 `libpath` 指向本目录。`zlgcan-driver 0.3.0` 在
Windows x64 下会固定从 `windows/x86_64/zlgcan.dll` 加载厂商库，因此目录必须是：

`zlgcan`（PyPI，周立功官方 python-can 接口）运行时需要厂商动态库。请从
**周立功官方 ZCANPRO / zlgcan 驱动包** 中取得并放入本目录：

```
library/
├── bitrate.cfg.yaml        # 位时序配置（如官方库提供）
├── zlgcan.dll              # 工程资源定位使用
└── windows/x86_64/
    ├── zlgcan.dll          # Rust 驱动实际加载的位置
    └── kerneldlls/         # ZCAN_OpenDevice/SetValue 需要的内核和设备描述
```

参考文档（zlgcan PyPI 主页）：

- 安装驱动（USBCANFD 系列需安装厂商 USB 驱动，USBCAN-I/II 一般免装）；
- 下载官方 library 文件（包含 `bitrate.cfg.yaml`）；
- `can.Bus(interface="zlgcan", libpath="library/", …)`。

> 说明：若替换或升级厂商 DLL，请从目标机器所安装的 ZCANPRO / zlgcan 驱动包
> 取得匹配版本，并重新运行准备或构建脚本。

`scripts/run_can_upper.ps1` 和 `scripts/build_can_upper.ps1` 会校验根目录 DLL，
并自动同步到 `windows/x86_64`。PyInstaller 构建也会把两份路径同时打入 EXE；
同时打包 `bitrate.cfg.yaml` 和完整 `kerneldlls`。缺少主 DLL 会报
`Could not open library` / Windows `os error 126`；缺少配套资源时通常表现为
`ZCAN_OpenDevice ret = 0` 或 `ZCAN_SetValue ret = 0`。

## 备选方案（旧后端）

若目标机器有旧版 ZCANPRO 且官方 `zlgcan` 包不适用，可改用内置 DLL 的旧后端：

```
uv sync --extra zlg-legacy
uv run can-tcp-bridge --interface zlg
```

`config.toml` 里把 `interface` 改为 `"zlg"`，用 `legacy_baud` 指定仲裁段速率(kbps)，
数据段固定 1 Mbps（旧后端限制）。
