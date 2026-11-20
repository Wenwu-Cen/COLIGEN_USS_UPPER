# 项目维护说明

唯一入口 `src/app.py` 组合数据源、车型控制、界面和共用控制器。已删除旧演示程序和第二套经典 Tk 界面，维护功能时直接修改所属模块。

## 模块职责

- `viewer_models.py`：独立的车辆、点、线、探头、车位和帧模型，不导入 GUI 或设备读取器。
- `log_parser.py`：TXT 文件头和帧解析，兼容旧日志并保留绘图位姿、采样时间与车型。
- `viewer_canvas.py`：局部/世界坐标绘图、后轴轨迹、平移缩放、测距、高光与冻结几何。
- `data_details.py`：RAW/PDC/POINT/LINE/SLOT 结构树，数组选择、点击快照与实时字段变化。
- `viewer_controller.py`：帧导航、在线生命周期、完整帧消费、状态、录制与 TXT/CSV 输出。
- `modern_ui.py`：CustomTkinter 界面、顶部状态和侧栏。通过覆盖控件创建方法组合，不再保留旧 UI。
- `app.py`：源工厂、ASC/BLF 回放扩展、PDC 提示音、启动参数和 EXE 自检。
- `can_source.py` / `zlg_can_bus.py`：DBC、ASC/BLF、ZLG/Vector；ZLG 直接调用 x64 SDK，仅打开所选通道。
- `debugger_source.py`：TRACE32/CS+ 完整帧聚合；`trace32_transport.py` / `csplus_transport.py` 读取设备内存。
- `ethernet_source.py` / `ethernet_protocol.py`：17 探头固定包与结构体对齐。
- `serial_source.py` / `serial_protocol.py`：串口设置、流式重同步、USSV v1/TLV/CRC32 与模型转换。
- `replay_source.py`：从 PC 回灌快照读取完整帧，断点期间保留画面。
- `debug_state.py`：底软调试变量镜像，供详情与录制使用。
- `map_view.py` / `selection_snapshot.py` / `display_clock.py`：纯计算与状态规则。

## 修改约定

新增源先适配统一帧和元数据，再交给控制器、画布。模型不得反向导入界面，新增源不得复制一套画布。后台线程只发布完整数据，Tk 控件在主线程更新。

显示坐标为 X 前/Y 左、毫米，各协议轴向、单位和对象 ID 在适配层处理。修改前阅读 [坐标说明](COORDINATE_SYSTEMS.md)。位姿和时间元数据必须与同帧几何一起发布。

POINT/LINE 高光跟随选定下标；点击快照存点击时字段与几何，不得每帧覆盖。世界视角冻结位置和轨迹使用世界坐标，不能直接累积局部坐标。

数据源英文显示选项统一大写，内部键保持 `lauterbach/csplus/zlgcan/canoe/tosun/ethernet/serial/replay_debug`，界面串口名称为 `SERIES`。厂商应用名、用户车型名、串口路径和协议变量保留原有大小写。

## 构建与发布

Windows 运行 `scripts/build_windows.ps1`，Ubuntu 运行 `scripts/build_ubuntu.sh`。两套 PyInstaller 配置都在 `scripts/pyinstaller/`，使用同一入口和项目内的 DBC。Windows 通过 `scripts/check_runtime.ps1` 检查厂商 DLL。构建脚本从当前仓库定位资源，可在独立解压的源码包中运行。

Windows 配置可选内置两个回灌 worker。S20 使用 `build/s20-stream/bin/dataReplay_main.exe` 和 `replay_s20_build_manifest.json`，D4M3 使用 `build/d4m3-stream/bin/dataReplay_main.exe` 和 `build_manifest.json`。每个清单与对应 EXE 放在同一目录。单机联调可在「录制设置」指定独立 EXE。

发布步骤

1. 同步 `src/app_version.py`、`pyproject.toml`、`uv.lock` 与 [变更日志](CHANGELOG.md)。用 `uv lock --check` 核对依赖锁文件。
2. 运行源码回归和 Windows EXE 自检。历史日志测试可通过 `COLIGEN_TEST_RECORDINGS` 指向解压出的 `recordings/` 目录。实体硬件及实车效果在相应设备上验证。
3. 从当前提交归档源码 ZIP。发布附件包括当前 Windows EXE、源码 ZIP、README、变更日志和 SHA-256 清单，以及明确标注自身版本的 Ubuntu 包和 S20 worker。
4. GitHub 和 Gitea 发布同一提交、版本标签与 Release。SVN 固定目录保持一套发布物，将该目录的已提交版本复制到 `Algo/可视化工具/tags/COLIGEN_USS_UPPER/v版本号`。回读附件名、大小和校验值。

历史采集日志保留在 v5.2.6 及更早标签的 `recordings/`。当前仓库的 `tests/fixtures/` 用于小型、可随源码复现的协议夹具。构建输出、虚拟环境、录制和个人设置均由忽略规则排除。

受保护文件的差异查看使用 [textconv](GIT_DECRYPT_DIFF.md)。SVN 提交说明记录软件变更、发布物与验证结果。
