# 开发维护与发布

下载安装和日常操作见 [README](../../README.md)。本页用于源码维护和发布。

唯一入口 `src/app.py` 组合数据源、车型控制、界面和共用控制器。已删除旧演示程序和第二套经典 Tk 界面，维护功能时直接修改所属模块。

## 从源码运行

需要 Python 3.10～3.12（推荐 3.12 x64）和 `uv`。源码包含 DBC、静态资源和 Windows 用户态运行库，不依赖同级外部项目。

在项目根目录打开 PowerShell：

```powershell
uv sync --locked
.\scripts\run_viewer.ps1
# 或直接运行，可选传入 TXT / ASC / BLF 路径
uv run python src/app.py "D:\logs\sample.asc"
```

Ubuntu 依赖和原生构建见 [Ubuntu 使用与构建](UBUNTU_RELEASE.md)。

## 模块职责

- `viewer_models.py`：独立的车辆、点、线、探头、车位和帧模型，不导入 GUI 或设备读取器。
- `log_parser.py`：TXT 文件头和帧解析，兼容旧日志并保留绘图位姿、采样时间与车型。
- `viewer_canvas.py`：局部/世界坐标绘图、后轴轨迹、平移缩放、测距、高光与冻结几何。
- `data_details.py`：RAW/PDC/POINT/LINE/SLOT 结构树，数组选择、点击快照与实时字段变化。
- `viewer_controller.py`：帧导航、在线生命周期、完整帧消费、状态、录制与 TXT/CSV 输出。
- `modern_ui.py`：CustomTkinter 界面、顶部状态和侧栏。通过覆盖控件创建方法组合，不再保留旧 UI。
- `recording_ui.py / recording_controller.py / replay_runtime.py`：录制设置、会话、导出与实时回灌。
- `xcp_source.py / xcp_protocol.py / xcp_symbols.py`：在线 XCP、传输与 ECU 变量布局。
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

显示坐标为 X 前/Y 左、毫米，各协议轴向、单位和对象 ID 在适配层处理。修改前阅读 [坐标说明](../reference/COORDINATE_SYSTEMS.md)。位姿和时间元数据必须与同帧几何一起发布。

POINT/LINE 高光跟随选定下标；点击快照存点击时字段与几何，不得每帧覆盖。世界视角冻结位置和轨迹使用世界坐标，不能直接累积局部坐标。

数据源英文显示选项统一大写，内部键保持 `lauterbach/csplus/zlgcan/canoe/tosun/ethernet/serial/replay_debug`，界面串口名称为 `SERIES`。厂商应用名、用户车型名、串口路径和协议变量保留原有大小写。

## 构建与发布

Windows 和 Ubuntu 的 PyInstaller 配置位于 `scripts/pyinstaller/`，使用同一入口和项目内的 DBC。Windows 通过 `scripts/check_runtime.ps1` 检查厂商 DLL。构建脚本从当前仓库定位资源，可在独立解压的源码包中运行。

Windows 便携包把回灌程序和构建清单放在 `profile/<项目>/`，优先使用源码同名目录中已有的程序。若该目录缺少程序，脚本从 `build/s20-stream/bin` 或 `build/d4m3-stream/bin` 复制已有的 `dataReplay_main.exe` 及同目录构建清单。S20 清单名为 `replay_s20_build_manifest.json`，D4M3 清单名为 `build_manifest.json`。也可在「录制设置」指定独立 EXE。

### Windows 构建与自检

```powershell
.\scripts\build_windows.ps1
```

输出 `dist/COLIGEN_USS_UPPER_v5.4.0-Windows-Portable.zip`。解压后在同一目录保留 EXE、`_internal`、`config` 和 `profile`。下载版可用 `Get-FileHash -Algorithm SHA256` 核对发布清单。

源码回归与 EXE 自检：

```powershell
uv run --locked python -m pytest -q
$sample = "D:\logs\S20test.asc"
$test = Start-Process -FilePath .\build\windows\dist\COLIGEN_USS_UPPER_v5.4.0\COLIGEN_USS_UPPER_v5.4.0.exe `
    -ArgumentList "--self-test `"$sample`" `"$PWD\build\self-test.json`"" -WindowStyle Hidden -Wait -PassThru
$test.ExitCode
Get-Content .\build\self-test.json
```

部分 Windows Tk 环境不支持同一进程反复创建根窗口；若批量 GUI 测试出现 Tcl 图标/主题错误，将相应用例分别在新进程运行。实体收包和实车坐标/轨迹效果需用对应设备及数据验证。

历史 ASC 样本可从 v5.2.6 取出，用于上面的 EXE 自检。

```powershell
$sampleDir = Join-Path (Get-Item ..).FullName 'upper-test-data'
$sampleZip = Join-Path $sampleDir 's20test.zip'
New-Item -ItemType Directory -Force $sampleDir | Out-Null
git archive --format=zip --output=$sampleZip v5.2.6 recordings/
Expand-Archive -LiteralPath $sampleZip -DestinationPath $sampleDir -Force
$env:COLIGEN_TEST_RECORDINGS = Join-Path $sampleDir 'recordings'
```

### 发布步骤

1. 同步 `src/app_version.py`、`pyproject.toml`、`uv.lock` 与 [变更日志](../CHANGELOG.md)。用 `uv lock --check` 核对依赖锁文件。
2. 运行源码回归和 Windows EXE 自检。历史日志测试可通过 `COLIGEN_TEST_RECORDINGS` 指向解压出的 `recordings/` 目录。实体硬件及实车效果在相应设备上验证。
3. 从当前提交归档源码 ZIP。发布附件包括当前 Windows 便携 ZIP、源码 ZIP、README、变更日志和 SHA-256 清单，以及明确标注自身版本的 Ubuntu 包和 S20 worker。
4. GitHub 和 Gitea 发布同一提交、版本标签与 Release。SVN 固定目录保持一套发布物，将该目录的已提交版本复制到 `Algo/可视化工具/tags/COLIGEN_USS_UPPER/v版本号`。回读附件名、大小和校验值。

历史采集日志保留在 v5.2.6 及更早标签的 `recordings/`。当前仓库的 `tests/fixtures/` 用于小型、可随源码复现的协议夹具。构建输出、虚拟环境、录制和个人设置均由忽略规则排除。

受保护文件的差异查看使用 [textconv](GIT_DECRYPT_DIFF.md)。SVN 提交说明记录软件变更、发布物与验证结果。


## 界面实现

### 维护边界

`src/modern_ui.py` 集中维护颜色、控件适配、布局和数据详情面板。颜色统一从 `COLORS` 读取。

`viewer_controller.py` 负责回放与录制；`viewer_canvas.py` 负责 Canvas；`viewer_models.py` 和 `log_parser.py` 为独立模型和 TXT 解析。
`src/app.py` 组合 CustomTkinter 界面，负责硬件选择、CAN/ASC/BLF/TCP/IP/串口接入与 PDC 音频。

原有 CAN、TRACE32、CS+ 和日志功能基于 20 探头方案；TCP/IP 解析属于 17 探头方案，不提供线段数据。
顶栏的 17 PROBE / 20 PROBE 显示所选在线数据源对应的方案，不表示报文中每种字段的元素数量。

共享控制器通过 `_create_main_pane()`、`_create_canvas()` 和 `_create_more_panel()` 创建视图。`WorkspaceCanvas` 复用画布渲染，在取景时包含可见图层的几何范围。
`MoreDataPanel` 通过 `<<TreeviewSelect>>` 把数组或字段所属的协议下标传给画布。树节点 iid 保持稳定，点/线在当前帧按下标查找；高亮作为增量图层绘制，保留原图元、颜色和固定地图镜头。
`SelectionSnapshot` 保存不可变的点击字段和世界坐标，使用与画布相同的完整帧取样。实时对比直接由新画布帧更新，独立于主数据树的刷新节流；源对象后续变化不会改写快照。
CustomTkinter 控件提供 `.config()` 兼容入口；下拉框把原生选择回调桥接到已有的
`<<ComboboxSelected>>` 事件，使硬件切换与 CAN 回放倍速继续使用统一控制器。
界面缩放由 CustomTkinter 处理。Tkinter 主窗口实现 DPI 开始和结束回调，供 CustomTkinter 缩放检查调用，避免中断透明度恢复。

### 依赖与打包

`pyproject.toml` 和 `uv.lock` 固定 CustomTkinter 版本。更新依赖后执行 `uv sync`。

`scripts/pyinstaller/windows.spec` 使用 `collect_data_files("customtkinter")` 收集主题和字体，
保证单文件 EXE 在未安装 Python 的电脑上也具备界面资源。
应用自己的图标继续由 `assets/car.ico` 提供。

打包自检除了 CAN 解码、厂商 DLL 和 17 探头解析，还会创建隐藏的 CustomTkinter 按钮和硬件下拉框，
验证 EXE 中的主题及字体资源可以加载。

CustomTkinter 采用 MIT 许可证。[CustomTkinter 项目](https://github.com/TomSchimansky/CustomTkinter)

## 界面响应

设备与显示、数据详情和配置窗口共用 Tk 主线程。滚动条每次绘制都强制执行全局 `update_idletasks()`，会在一次布局内反复触发其他控件布局和绘制。主窗口原先是普通 Tk，首次 CTk 弹窗才启用进程 DPI 感知，会引发主窗口整体缩放和重绘。串口枚举也曾直接占用主线程。

程序在创建主窗口前初始化 DPI，保留后续 DPI 监测；控件使用 CTk 原生多边形边框。`ui_runtime.py` 的滚动条适配沿用锁定的 CustomTkinter 6.0.0 几何和配色，让主循环统一安排重绘。配置窗口先构建再显示，标题栏直接通过 DWM 设置，避免在构造期间调用 `update()`。这些适配仅在应用内使用，不修改已安装依赖。

详情面板在添加前预留目标宽度，交由 Tk 分栏布局分配空间；不调用全局事件刷新来强行得到宽度。高 DPI 的最小窗口按系统缩放设置，窄窗口的信息栏自动换行。空间不足时收起快照颜色图例及点击时间标题，扩大窗口恢复；原始快照字段和保存位置继续保留。

串口扫描由后台线程枚举，只将结果放入队列；主线程轮询并显示结果。扫描期间可以填写其他参数，关闭窗口会取消轮询。后台扫描线程不调用 Tk，不会在窗口关闭后更新已销毁控件。

回归入口为 `tests/test_ui_responsiveness.py`，覆盖绘制/按钮不执行嵌套 idle 任务、首次配置弹窗不改变主窗口 DPI、慢串口枚举时主循环仍可运行，以及初次布局前打开详情仍保留车辆画布。现有界面测试继续覆盖展开/收起、点线高光、快照保留、窄窗口、车型配置和保存/取消/关闭路径。


### 4.5.1：窗口显示和主窗口衔接

普通文字标签使用 `TextLabel`，保留 CTk 的配置、字体、外观与缩放接口，直接显示原生文本，省去每个标签的背景 Canvas。圆角或边框标签继续使用 CTk 绘制；运行时新增圆角/边框会补建画布。车型编辑器先建立字段变量和数据树，探头输入控件在首次点击探头页时创建，已有字段内容和编辑状态保持不变。

`SettingsDialog` 在隐藏状态下等待 idle 布局，再按最终内容或显式尺寸相对主窗口居中。实际收到 Map 事件后取得输入焦点及本地 grab，关闭时释放并归还先前焦点。所有设置窗口采用同一生命周期；串口和车型不再分别等待 50/100ms。网络和串口设置的连续点击复用尚未关闭的窗口。CustomTkinter 的延迟默认图标更新改为沿用 Tk 应用图标。

CTk 6.0 的每次 Toplevel 构建都会添加全局 Button-1 焦点处理器，销毁窗口后仍保留。本适配只拦截构造期间的这一处理器，每个 Tk 解释器安装一次；业务代码自己的全局绑定仍按 Tk 原义执行。

详情面板在加入分栏前预留目标宽度，由 Tk 完成空间分配，避免用旧主窗口宽度设置 sash 后再修正。画布的尺寸重绘合并到下一次 idle，同一批请求只安排一次，关闭时取消待执行任务。

验证应同时观察点击回调耗时、定时心跳最大间隔、首次 Map 的实际尺寸和最终布局；单次 `update()` 会排空多个事件，其总耗时不能等同于一次主线程冻结。Windows 原生映射受机器负载影响，性能比较需要相同缩放、相同数据及重复样本。此工作站的 Tk 在同一进程反复创建根窗口时偶有库初始化错误，相关失败需在独立进程复核。


本机 Windows 对比（v4.5.0 与 v4.5.1，同一 Python/CTk 环境，空闲主窗口、模拟空串口列表、每种弹窗 3 次）：网络/串口/车型初始子控件数从 68/65/150 降至 57/55/83；构造回调中位耗时从 41.3/44.1/77.4ms 降至 29.8/34.6/62.1ms。每 8ms 调度一次的心跳，在打开阶段的最大间隔取三次中位数，分别从 130.4/133.6/92.0ms 降至 75.5/64.8/69.8ms。首次车型打开还包含模块加载，单次样本会明显偏大；以上数据不等同于所有机器的点击到完全显示时间，也不包括实际硬件连接。


### 4.5.2：“设备与显示”侧栏

此前每次 `pack/pack_forget` 都重新映射整棵原生控件树。现在侧栏使用稳定的 place 布局，收起时停放在主窗口 body 的裁剪区域外，展开时移回左侧，工作区按侧栏实际宽度预留空间。这样切换不重建或重新映射子窗口，也不会清空滚动位置、输入或数据源选择。收起时暂存并关闭原生子控件的 takefocus，展开时还原；当前焦点在侧栏时先移回车辆画布。

工作区留白按控件实际像素宽度换回 CTk 逻辑单位，侧栏尺寸变化后同步；place 的位置与锚点由 CTk 记录，DPI 更新不会把已展开侧栏重新移到屏幕外。

本机 Windows 三次展开对比：此前心跳最大间隔为 96.0/42.4/60.4ms；新实现为 22.7/17.3/19.8ms（每 8ms 调度心跳，空闲主窗口、无在线采集）。中位数从 60.4ms 降至 19.8ms，约下降 67%。单次 update 排空耗时仍包括多条原生事件，不能作为单个冻结时长。回归验证侧栏没有新增 Map、完整展开与收起后的画布宽度、滚动/输入保留、隐藏控件的 Tab 焦点以及原有硬件和快照流程。


### 4.9.1：默认展开与静音位置

设备与显示启动时默认展开，首次布局预留侧栏空间，后续继续通过停放原生控件展开和收起。PDC 静音按钮位于侧栏下方的标注区域，随侧栏滚动，音频状态沿用现有逻辑。收起/展开、焦点恢复、滚动与输入保留及缩放行为继续使用原有路径。
