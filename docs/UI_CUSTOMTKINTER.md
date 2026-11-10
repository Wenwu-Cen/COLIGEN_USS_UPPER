# CustomTkinter 界面（3.8.1）

当前 GUI 使用用户选择的 D 方案：CustomTkinter 6.0.0 与原有 Tkinter Canvas / ttk Treeview 结合。

## 使用

运行 `scripts/run_can_upper.ps1`，或打开 `dist/COLIGEN_USS_UPPER_CAN_v3.8.1.exe`。

- 顶部工具栏提供在线连接、打开日志、录制、数据详情和适应视图。
- 点击「设备与显示」展开左侧栏，选择硬件、切换图层与标注、使用测距并查看文件与报文计数。再次点击可收起。
- 点击「适应视图」或在画布上右键，按当前显示的数据调整车辆和周边区域。滚轮可缩放，左键可拖动。窗口或面板尺寸变化后，适应模式会重新取景，手动模式保持缩放比例。
- 点击「数据详情」展开右侧 RAW、PDC、POINT、LINE、SLOT，拖动分隔条可调整宽度。
- 底部集中回放时间轴、帧导航、倍速和帧信息。
- TCP/IP 使用“网络设置”配置 UDP 监听或 TCP 客户端、IP、端口、字节序和对齐。
- Port 输入框仅用于 Lauterbach TRACE32；ZLG-USBCANFD-200U、CANoe/Vector、Renesas CS+ 均不显示该输入框。

## 维护边界

`src/modern_ui.py` 集中维护颜色、控件适配、布局和数据详情面板。颜色统一从 `COLORS` 读取。

`src/VehUpperDemo.py` 保留共享控制器、Canvas 坐标计算、数据模型、TXT 回放及录制。
`src/VehUpperDemo_CAN.py` 组合 CustomTkinter 界面，负责硬件选择、CAN/ASC/BLF/TCP/IP 接入与 PDC 音频。

原有 CAN、TRACE32、CS+ 和日志功能基于 20 探头方案；TCP/IP 解析属于 17 探头方案，不提供线段数据。
顶栏的 17 PROBE / 20 PROBE 显示所选在线数据源对应的方案，不表示报文中每种字段的元素数量。

共享控制器通过 `_create_main_pane()`、`_create_canvas()` 和 `_create_more_panel()` 创建视图。`WorkspaceCanvas` 复用画布渲染，在取景时包含可见图层的几何范围。
CustomTkinter 控件提供 `.config()` 兼容入口；下拉框把原生选择回调桥接到已有的
`<<ComboboxSelected>>` 事件，使硬件切换与 CAN 回放倍速继续使用统一控制器。
界面缩放由 CustomTkinter 处理，不再在每个子控件的 Configure 事件中重置字体。

## 依赖与打包

`pyproject.toml` 和 `uv.lock` 固定 CustomTkinter 版本。更新依赖后执行 `uv sync`。

`VehUpperDemo.spec` 使用 `collect_data_files("customtkinter")` 收集主题和字体，
保证单文件 EXE 在未安装 Python 的电脑上也具备界面资源。
应用自己的图标继续由 `assets/car.ico` 提供。

打包自检除了 CAN 解码、厂商 DLL 和 17 探头解析，还会创建隐藏的 CustomTkinter 按钮和硬件下拉框，
验证 EXE 中的主题及字体资源可以加载。

CustomTkinter 项目采用 MIT 许可证：
https://github.com/TomSchimansky/CustomTkinter
