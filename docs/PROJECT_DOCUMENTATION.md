# 项目维护说明（4.4.0）

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

数据源英文显示选项统一大写，内部键保持 `lauterbach/csplus/zlgcan/canoe/ethernet/serial/replay_debug`，界面串口名称为 `SERIES`。厂商应用名、用户车型名、串口路径和协议变量保留原有大小写。

## 构建与发布

Windows：`viewer.spec` / `scripts/build_windows.ps1`；Ubuntu：`viewer_linux.spec` / `scripts/build_ubuntu.sh`。DBC 来自项目内 `assets/dbc/`，运行库来自 `library/`，不依赖外部项目路径。

版本在 `app_version.py`，依赖在 `pyproject.toml`、`uv.lock`。发布需版本一致、适当回归、EXE 自检、源码包可独立构建和 SHA256 校验。实体硬件及实车效果须另行验证。

Git 保留源码和示例日志，精简源码 ZIP 省略历史日志。SVN 当前树仅放当前 EXE、源码 ZIP、README、CHANGELOG 和校验文件，历史版通过版本控制查询。

受保护文件沿用现有存储策略，差异查看使用 [textconv](GIT_DECRYPT_DIFF.md)。`build/`、`dist/`、`.venv/` 和个人设置不提交。
