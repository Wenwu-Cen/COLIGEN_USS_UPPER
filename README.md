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

当前软件版本为 `3.8.2`。CustomTkinter 界面使用单行工具栏和默认收起的侧栏，点击「适应视图」可将当前数据完整收入画布。 [界面使用与维护](docs/UI_CUSTOMTKINTER.md)

PDC 支持远档 2 Hz、中档 4 Hz 和近档长鸣。新增 17 探头方案以太网接口，可显示点云、PDC 和车位。原有功能基于 20 探头方案。[变更日志](CHANGELOG.md)

周立功在线收包会让出界面线程，重复报文跳过解码和画布刷新。点云、扇形、PDC 和车位批量更新，图元只在像素位置变化时移动。拖动时按像素平移，松手或停轮后重绘。ASC/BLF 从“打开日志”打开。参照网格默认细格 0.5 m、主格 1 m。S20 的冲突 ID 默认按车位解析，在「设备与显示」的「图层与测距」中关闭车位图层后，按点云和 PDC 解析。

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

在已安装 Python 3.10 或更高版本的 Windows 上，从项目根目录运行

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
dist/COLIGEN_USS_UPPER_CAN_v3.8.2.exe
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
