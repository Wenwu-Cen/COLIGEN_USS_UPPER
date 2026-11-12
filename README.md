# COLIGEN USS UPPER CAN

## 目录结构说明

```text
src/         Python运行代码以及CAN/GUI适配模块
tests/       Pytest测试用例以及旧版自测试程序
scripts/     PowerShell运行和构建脚本，以及CS+桥接工具
config/      运行时TOML配置文件
assets/      应用程序图标以及打包所需静态资源
docs/        集成文档、架构说明以及项目状态文档
recordings/  ASC/TXT回放文件
build/       PyInstaller构建中间文件（自动生成）
dist/        打包后的EXE输出目录（自动生成）
library/     第三方厂商运行库存放目录
```

`CAN_S20/` 是项目外部的同级目录，用于存放 DBC 文件以及（可用时）报文回放源文件。

该目录不会被复制到当前项目中。

当前软件版本为 `3.13.1`。CustomTkinter 界面使用单行工具栏和默认收起的侧栏，点击「适应视图」可将当前数据完整收入画布。 [界面使用与维护](docs/UI_CUSTOMTKINTER.md)

PDC 支持远档 2 Hz、中档 4 Hz 和近档长鸣。新增 17 探头方案以太网接口，可显示点云、PDC 和车位。原有功能基于 20 探头方案。[变更日志](CHANGELOG.md)

周立功在线收包会让出界面线程，重复报文跳过解码和画布刷新。点云、扇形、PDC 和车位批量更新，图元只在像素位置变化时移动。拖动时按像素平移，松手或停轮后重绘。ASC/BLF 从“打开日志”打开。参照网格默认细格 0.5 m、主格 1 m。S20 的冲突 ID 默认按车位解析，在「设备与显示」的「图层与测距」中关闭车位图层后，按点云和 PDC 解析。

CS+ 现在按 50 ms 起始周期采集，慢读时复用本轮批量缓存，界面每 33 ms 取最新完整帧。状态栏显示采集频率、完整读取耗时、最近 60 帧 P95 和距上次接收的时间；等待更新和数据滞后分别以黄、红色提示。原始数据表和动态图元增量更新，重复帧不再重复录制。[CS+ 优化与验证](docs/PROJECT_STATUS_CS_PLUS.md#2026-11-12软件侧优化v3110)

CS+ / E2：先在 CS+ 打开目标工程并连接调试器，在上位机选择「Renesas CS+」后点击「在线连接」。程序会自动启动官方通信服务和无损内存桥，无需每次执行 `server.Start()`。请只保留一个目标 CS+ 实例；首次使用若提示远程接口关闭，按提示启用 CS+ Python Console 的远程连接启动选项。[自动连接说明](docs/PROJECT_STATUS_CS_PLUS.md#2026-11-12自动启动服务与内存桥v3120)

E2 卡顿优化：内存桥 v6 在读取期间关闭 Console 数值输出并恢复原设置，消除大量文本刷新导致的秒级长尾；在线连接会自动更新旧桥。画布改为局部重绘，成功慢读通过状态栏显示。[实机测速与验证](docs/E2_PERFORMANCE_3.13.0.md)

CS+ 车位跳变修复：按当前调试符号确认 4/44 或 8/48 布局，避免把时间戳解析成巨型车位坐标；左右数量为 0 时不再显示数组残留值。[车位排查与验证](docs/CSPLUS_SLOT_LAYOUT_3.13.1.md)

发版时同步修改 `src/app_version.py` 的 `APP_VERSION` 与 `pyproject.toml` 的 `version`，并运行 `uv lock` 更新锁文件。窗口标题和 EXE 文件名会使用新版本号。

---

## 快速开始

### 安装或更新 uv 环境

```powershell
uv sync
```

---

### 从源码运行GUI程序

```powershell
.\scripts\run_can_upper.ps1
```

---

### Ubuntu 直接运行

新增原生 Linux 单文件程序和桌面快捷方式，已在 Ubuntu 22.04.5 x86_64 验证。无需单独安装 Python，Linux 默认 TRACE32 TCP 端口为 20000。[下载包使用、依赖与 TRACE32 配置](docs/UBUNTU_RELEASE.md)

构建：在 Ubuntu 源码目录运行 `bash scripts/build_ubuntu.sh`。产物为 `dist/COLIGEN_USS_UPPER_v3.13.1_Ubuntu_x86_64.tar.gz`。

### 车型与探头安装配置

顶部「车型配置」可编辑车辆尺寸、轴距 / 悬长、每个探头的坐标、朝向、FOV 和启用状态；支持多车型保存、切换与 JSON 导入导出。两平台使用同一格式，录制 / 回放保存配置。[使用说明](docs/VEHICLE_PROFILES.md)

TRACE32 的 Probe Scheme 可选 17 PROBE / 20 PROBE；17 探头没有线段输出，PDC 外发单位为 cm。

### Git / VS Code 解密差异

按提供文档使用 textconv，本机驱动已适配受保护文件。项目提供一键配置与验证脚本：[操作说明](docs/GIT_DECRYPT_DIFF.md)。

### 以太网接入

打开「设备与显示」，在 Hardware 下拉框选择「TCP/IP」，点击「网络设置」匹配 RTE 端的 IP、端口与数据布局后连接。默认 UDP 监听 `0.0.0.0:50000`，接收 512 字节底软数据包。[17 探头以太网说明](docs/ETHERNET_INTERFACE.md)

本机模拟可运行 `python scripts/test_ethernet_input.py`，发送 90 点、8 车位和三档 PDC。

---

### 运行测试

```powershell
uv run pytest -q
```

---

### 试听 PDC 告警

在已安装 Python 3.10 或更高版本的 Windows / Ubuntu 上，从项目根目录运行

```powershell
python .\scripts\test_pdc_alarm.py
```

脚本直接调用上位机音效，依次播放远档 2 Hz、中档 4 Hz 和近档长鸣。每档 3 秒，按 Ctrl+C 停止。

---

### 构建Windows可执行程序

```powershell
.\scripts\build_can_upper.ps1
```

生成的可执行文件路径：

```text
dist/COLIGEN_USS_UPPER_CAN_v3.13.0.exe
```

---

## 推荐优先阅读文件

1. `docs/CAN_INTEGRATION_README.md`

   用于了解：

   - CAN通信集成
   - ASC/BLF报文回放
   - 软件部署方式
2. `docs/COORDINATE_SYSTEMS.md`

   画布 / TXT（泊车3.txt）/ ASC 的点和线坐标系对照。
3. `src/VehUpperDemo_CAN.py`

   应用程序入口文件。
4. `src/CanOnlinePort.py`

   主要负责：

   - ASC文件解析
   - DBC报文解析
   - CAN Frame组装
5. `src/VehUpperDemo.py`

   GUI界面以及画布渲染相关代码。
6. `config/can_upper_config.toml`

   CAN设备以及回放参数配置文件。

---

## 注意事项

以下目录不要手动修改：

```text
build/
dist/
.venv/
__pycache__/
```

这些目录属于：

- 自动生成文件
- 编译输出文件
- Python环境缓存文件

修改可能导致构建或运行异常。
