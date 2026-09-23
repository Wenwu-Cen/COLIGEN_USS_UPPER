# COLIGEN USS UPPER 工程代码文档

> 本文档保留早期 Trace32/CS+ 数据链路的技术说明。当前目录布局、CAN/ASC 入口和构建命令以根目录 `README.md` 与 `docs/CAN_INTEGRATION_README.md` 为准。

---

## 目录

1. [工程概述](#1-工程概述)
2. [目录结构](#2-目录结构)
3. [系统架构与数据流](#3-系统架构与数据流)
4. [C 端结构体定义（Lauterbach_Var.h / .c）](#4-c-端结构体定义)
5. [DataSheet.py —— 数据存储层](#5-datasheetpy--数据存储层)
6. [ReadDataPort.py —— 在线读取层](#6-readdataportpy--在线读取层)
7. [OnlinePort.py —— 帧构建与后台线程](#7-onlineportpy--帧构建与后台线程)
8. [vehicle_upper_demo.py —— 主界面](#8-vehicle_upper_demopy--主界面)
9. [坐标系与关键约定](#9-坐标系与关键约定)
10. [自测脚本 _selftest.py](#10-自测脚本-selftestpy)
11. [打包配置 vehicle_upper_demo.spec](#11-打包配置)
12. [运行方式](#12-运行方式)
13. [功能模块要点与注意事项](#13-功能模块要点与注意事项)

---

## 1. 工程概述

**COLIGEN USS UPPER V1.0** 是超声波雷达（USS）系统的**上位机演示/调试工具**，主要能力：

| 功能 | 说明 |
|---|---|
| **日志回放** | 解析 `.txt` 日志（含新旧两种格式），逐帧显示车辆、探头、障碍物、车位 |
| **在线读取** | 通过 Lauterbach Trace32 RCL 实时读取目标板内存中的 C 结构体数据 |
| **车辆可视化** | 车身轮廓、12 个探头、探头探测扇形、PDC 色块、车位 A~F 连线 |
| **实时数据面板** | Show More Data 面板：Raw / PDC / Obj / Line / Slot 五页，数据常显实时更新 |
| **录制与导出** | 录制期间的所有帧保存为可回放 TXT 日志，并同时导出前/后传感器原始数据 CSV |
| **状态记忆** | 关闭时记住 Show More Data 面板的展开/收起状态与显示状态，下次启动恢复 |

**技术栈**：Python 3 + Tkinter（ttk 主题 `clam`）+ NumPy + Lauterbach Trace32 RCL（`lauterbach.trace32.rcl`）；C 端结构体定义用于嵌入式侧调试镜像（`LAUTERBACH_UPPER_DEBUG` 宏开关）。

**运行要求**：必须使用 **Python 3**（本机默认 `python` 可能为 2.7，需用 `python3` 启动）。

---

## 2. 目录结构

```
COLIGEN_USS_UPPER/
├── src/                        # 运行时代码与 CAN/GUI 适配器
├── tests/                      # pytest 与自测脚本
├── scripts/                    # 启动、构建和 CS+ 桥接工具
├── config/                     # 运行配置
├── assets/                     # 图标与静态资源
├── docs/                       # 工程说明
├── recordings/                 # ASC/TXT 回放文件
├── build/ dist/                # PyInstaller 生成产物
├── library/                    # 厂商运行库放置目录
├── pyproject.toml              # uv/pytest/ruff 配置
└── VehUpperDemo.spec           # PyInstaller 打包配置
```

---

## 3. 系统架构与数据流

### 3.1 总体分层

```
┌───────────────────────── C 端（嵌入式调试镜像）─────────────────────────┐
│  Lauterbach_Var.h / Lauterbach_Var.c                                   │
│  sf_Upper_*OutSignal 全局结构体（Vehicle/RawData/PDC/Slot/Status/Odo/  │
│  Point/Line），由 OutputSignalRead_* 函数从 USS 算法侧填充              │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Lauterbach Trace32 RCL 远程读取
┌──────────────────────────────────▼─────────────────────────────────────┐
│  ReadDataPort.py（在线读取层）                                          │
│  符号地址解析 → memory.read → struct.unpack → 写入 DataSheet            │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│  DataSheet.py（Python 共享数据层）—— 所有在线变量集中存放               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
          ┌────────────────────────┴────────────────────────┐
          ▼                                                 ▼
┌──────────────────────┐                    ┌──────────────────────────┐
│  OnlinePort.py       │                    │  vehicle_upper_demo.py   │
│  build_frame() 组装帧 │◄──OnlineReader───►│  App（Tkinter 主窗口）     │
│  （后台线程实时读取） │   后台线程          │  VehicleCanvas 画布       │
└──────────────────────┘                    │  MoreDataPanel 数据面板   │
                                            │  LogParser 回放解析       │
                                            └──────────────────────────┘
```

### 3.2 在线模式数据流

```
C 结构体（sf_Upper_*OutSignal）
  → ReadDataPort.read_*() 逐个结构体读取（_retry 重试）
  → DataSheet.py 变量
  → OnlinePort.build_frame() → 9 元组
    (segments, points, gear, speed, raw_probes, pdc_ranges, slots,
     samefreq_front_flag, samefreq_rear_flag)
  → App._online_tick → canvas.set_obstacles(...) → 绘制
  → 同频标志 → 车前/车后小灯
```

### 3.3 回放模式数据流

```
*.txt 日志
  → LogParser.parse()（按 "== Frame Index: n ==" 分帧）
  → FrameData 对象列表
  → App._jump_to_frame() → canvas.set_obstacles(...) → 绘制
```

### 3.4 录制数据流

```
在线/回放每帧
  → _record_frame(...) 生成日志文本块 + 快照 snap
  → 停止录制 → _save_record()：
      · 保存 TXT 日志（可回放，含新旧格式结构体分节）
      · 同时导出 _Front.csv / _Rear.csv（前/后 6 传感器原始数据）
```

---

## 4. C 端结构体定义

### 4.1 文件说明

| 文件 | 内容 |
|---|---|
| `Lauterbach_Var.h` | `Upper_*OutSignal` 全部结构体定义 + 函数声明（仅 `LAUTERBACH_UPPER_DEBUG` 编译） |
| `Lauterbach_Var.c` | 全局变量定义 + `OutputSignalInit_*` / `OutputSignalRead_*` 实现 |

### 4.2 结构体清单

```c
// 车身参数（52 字节）
typedef struct {
    uint16_t CarLength, CarWidth;
    int16_t SnsPosRRS_X/Y ... SnsPosFLS_X/Y;   // 12 组探头位置（RRS→FLS 顺序）
} Upper_VehicleOutSignal;

// 回波原始数据信息（20 字节/探头）
typedef struct {
    uint8_t mode;  uint16_t de, de_peak, de_width;
    uint16_t ce_left, ce_left_peak, ce_left_width;
    uint16_t ce_right, ce_right_peak, ce_right_width;
} Upper_RawDataOutSignalInfo;

// 回波原始数据总结构体（246 字节）
typedef struct {
    uint16_t samefreq_front_Cnt;   // 前向同频计数器
    uint16_t samefreq_rear_Cnt;    // 后向同频计数器
    uint8_t  samefreq_front_Flag;  // 前向同频标志（=1 前小灯亮）
    uint8_t  samefreq_rear_Flag;   // 后向同频标志（=1 后小灯亮）
    Upper_RawDataOutSignalInfo rawdata_info[12];  // offset 6..245
} Upper_RawDataOutSignal;

// PDC 报警信息（4 字节/探头）
typedef struct { uint16_t dis; uint8_t range; uint8_t fault; } Upper_PDCOutSignalInfo;

// PDC 报警信号（52 字节，snspdc_info[0..11] = RRS..FLS SNS_STR_LIST 顺序）
typedef struct {
    uint8_t pdc_sts, front_sts, rear_sts;
    Upper_PDCOutSignalInfo snspdc_info[12];
} Upper_PDCOutSignal;

// 车位槽位信息（slot_width/slot_Depth 为 uint16_t；2/4/8 字节对齐下大小 42/44/48 字节）
typedef struct {
    uint64_t timestamp;
    uint8_t slot_id, slot_type;
    uint16_t slot_width, slot_Depth;
    int16_t slot_A_x, slot_A_y;  uint8_t slot_A_type;
    int16_t slot_B_x/y, slot_C_x/y, slot_D_x/y, slot_E_x/y;
    int16_t slot_F_x, slot_F_y;  uint8_t slot_F_type;
} Upper_SlotOutSignalInfo;

// 车位信号（左 3 + 右 3 槽位）
typedef struct {
    uint8_t slot_sts, left_slot_num, right_slot_num;
    Upper_SlotOutSignalInfo left_slot_info[3], right_slot_info[3];
} Upper_SlotOutSignal;

// 车辆状态 / 里程计
typedef struct {
    uint8_t GearLever; uint16_t Temp; float Speed; uint64_t TimeStamp;
} Upper_StatusOutSignal;
typedef struct { float odo_x, odo_y, odo_ang; } Upper_OdoOutSignal;

// 点云 / 线段障碍物
typedef struct {
    uint16_t ObjID; int16_t x, y; uint8_t cHight, SNS_Txindex, SNS_Rxindex;
} Upper_PointOutSignal;
typedef struct {
    uint8_t cNum, cHight, cObjType;
    int16_t wStartx, wStarty, wEndx, wEndy; uint16_t wDist;
} Upper_LineOutSignal;
```

### 4.3 关键实现函数（Lauterbach_Var.c）

| 函数 | 作用 |
|---|---|
| `OutputSignalRead_Vehicle()` | 从 `kLengthOfCar/kWidthOfCar/kSnsPos*` 填充车身参数 |
| `OutputSignalRead_Rawdata(SnsCh_Index)` | 从 `USS_OriginalInfo*` 填充 `rawdata_info[SnsCh_Index]`；同频标志由 `d_SameFreq_Front/Rear_Cnt > 50` 判定 |
| `OutputSignalRead_PDC(...)` | 从 `PdcmPrivateCan_PDC_Info` 填充 12 探头 `snspdc_info`；末尾 HX11 色块适配把 range 归一为 0/1/2/3 |
| `OutputSignalRead_Slot()` | 从 `WroldUltrasonicSlot[1]/[0]` 填充左右各 3 槽位 A~F 六点 |
| `OutputSignalRead_Status/Odo/Point/Line` | 状态、里程计、点云、线段填充 |

---

## 5. DataSheet.py —— 数据存储层

`DataSheet.py` 是**纯数据模块**，集中存放所有共享变量，供 `ReadDataPort` 写入、`OnlinePort` 读取、`vehicle_upper_demo` 使用。无任何业务逻辑。

### 5.1 协议常量

```python
POINT_CLOUD_NUM = 80    # 点云数量上限
POINT_LINE_NUM  = 20    # 线段数量上限
POINT_SLOT_NUM  = 8     # 旧 Slot 数组数量
GEAR_STR_LIST   = ['P', 'R', 'N', 'D']
SLOT_TYPE_STR_LIST = ("无", "水平", "垂直", "斜线")
SNS_STR_LIST = ('RRS','RRC','RRM','RLM','RLC','RLS',
                'FRS','FRC','FRM','FLM','FLC','FLS')   # 12 探头 SNS 顺序
DATA_TYPE_* = 1..31     # 旧 CSV/协议数据类型枚举
```

### 5.2 变量分组

| 分组 | 变量 | 说明 |
|---|---|---|
| 车辆状态 | `VehicleGear / VehicleSpeed / VehicleTemp / VehicleTimeStamp` | `VehicleSpeed` 为 **float（km/h）** |
| 里程计 | `OdoX / OdoY / OdoAng / VehicleCenterPt` | `OdoAng` 弧度 |
| 车身参数 | `VehicleLength / VehicleWidth / VehicleProbePos[12]` | 顺序 = SNS_STR_LIST |
| 点云 | `PtTime/PtTxMask/PtRxMask/Ptx/Pty/Pth/Ptype[80] / PtNum` | |
| 线段 | `PtLinex1/2, PtLiney1/2, PtLineh, PtLinetype, PtLineObjType, PtLineDist[20] / PtLineNum` | |
| 旧 Slot | `Slotx1..y4, SlotLength, SlotDepth, SlotType[8] / SlotNum` | |
| 新车位 | `SlotOutNum/LeftNum/RightNum/Sts`，`SlotOutId/Type/Width/Depth/Valid[6]`，A..F 六点 `SlotOutAx..Fy[6]` | 左 3 + 右 3 |
| 回波 | `RawSameFreqFrontCnt/RearCnt/FrontFlag/RearFlag`，`raw_data[12]`（每项 10 元组 `(mode, de, de_peak, de_width, ce_left, ce_left_peak, ce_left_width, ce_right, ce_right_peak, ce_right_width)`） | |
| PDC | `PDC_Sts / PDC_FrontSts / PDC_RearSts`，`PDCDis / PDCRange / PDCFault[12]` | 顺序 = SNS_STR_LIST |

---

## 6. 在线读取层 —— ReadDataPort.py（劳特巴赫）与 ReadDataPort_CSPlus.py（瑞萨 CS+）

上位机提供**两种调试器连接方式**，工具栏「方式」下拉框选择，读取的**内容变量完全一致**：
- **劳特巴赫**：`ReadDataPort.py`，通过 Lauterbach Trace32 RCL 读取（`t32.connect(port)` + `SYStem.Attach`）。
- **CS+**：`ReadDataPort_CSPlus.py`，通过瑞萨 CS+ Integration Service 读取（`csplus` / `integration_service`，懒加载），连接层从 `COLIGEN_USS_V1_9_1_S73/ReadDataPort.py` 移植。

两者对外 API 完全一致：`read_port_connect / read_port_disconnect / set_error_callback / reconnect / read_StsData / read_vehicleInfo / read_PtData / read_PtLineData / read_echoData / read_PDCData / read_SlotOutData`，读取的符号（`sf_Upper_*`、`cAutoDrv_CarCenterPt` 等）与写入的 `DataSheet` 字段也完全一致——仅底层“调试器连接”不同。`OnlinePort.OnlineReader(backend='lauterbach'|'csplus')` 按所选后端分发。

### 6.1 连接管理

| 函数 | 作用 |
|---|---|
| `read_port_connect(info)` | 劳特巴赫：`t32.connect(port)` + `SYStem.Attach`（含中文错误提示）；CS+：`_connect_backend()`（懒加载并连接 CS+ Integration Service，忽略 info） |
| `read_port_disconnect()` | 劳特巴赫：`dbg.disconnect()`；CS+：`_disconnect_backend()` |
| `reconnect()` | 连接可能断开时尝试重连（劳特巴赫=`SYStem.Attach`，CS+=`_connect_backend()`） |

### 6.2 通用读取辅助

```python
_ADDR_CACHE = {}          # 符号地址缓存（连接后按需解析一次）

# 劳特巴赫版：
_resolve_symbol(symbol)   # dbg.fnc → dbg.address.from_string → 缓存
_retry(desc, callback)    # 重试封装：
                          #   永久错误(symbol not found) → 立即上报返回 None
                          #   其它错误 → 每次重试前重新 SYStem.Attach，
                          #   上报并计数，>10 次后放弃
_read_symbol(desc, symbol, length, fmt)  # 解析地址 + memory.read + struct.unpack

# CS+ 版（与上等价）：
get_addr(symbol)                  # Symbol.GetAddress → 缓存
read_memory_range_struct(symbol, length)  # Memory.ReadRange/Read 批量读字节
_evaluate_expression(expr, float) # 表达式求值（档位/温度/车速等单变量）
_retry / _read_symbol             # 重试 + 读符号，与劳特巴赫版同语义
```

### 6.3 各结构体读取函数

| 函数 | 读取对象 | 长度/格式 | 写入 DataSheet |
|---|---|---|---|
| `read_vehicleInfo()` | `sf_Upper_VehicleOutSignal` | 52B `'HH'+'hh'*12` | `VehicleLength/Width/ProbePos` |
| `read_StsData()` | `sf_Upper_StatusOutSignal` + `sf_Upper_OdoOutSignal` | 变量读 + 12B `'fff'` | `VehicleGear/Temp/TimeStamp/Speed(float)`、`OdoX/Y/Ang` |
| `read_PtData()` | `sf_Upper_PointOutSignal[80]` | `'HhhBBBB'*80` | `Ptx/Pty/Pth/Ptype/PtTxMask/PtRxMask/PtNum` |
| `read_PtLineData()` | `sf_Upper_LineOutSignal[20]` | `'BBBBhhhhH'*20` | `PtLinex1/2, PtLiney1/2, PtLineh, PtLinetype, PtLineObjType, PtLineDist, PtLineNum` |
| `read_echoData()` | `sf_Upper_RawDataOutSignal` | **246B `'HHBB'+'BxHHHHHHHHH'*12`** | `RawSameFreqFrontCnt/RearCnt/FrontFlag/RearFlag`、`raw_data[12]` |
| `read_PDCData()` | `sf_Upper_PDCOutSignal` | **52B `'BBBx'+'HBB'*12`** | `PDC_Sts/FrontSts/RearSts`、`PDCDis/PDCRange/PDCFault[12]`（snspdc_info 顺序 = SNS_STR_LIST，直写无需反转） |
| `read_SlotOutData()` | `sf_Upper_SlotOutSignal` | 296B（`'<QBBHHhhBx'+'hhhhhhhhhh'+'Bx'`；单个 info 42/44/48B 随 2/4/8 对齐） | `SlotOut*` 全字段 + `SlotOutValid` |

**要点**：
- `read_PDCData()` 末尾有**数据有效性校验**：`PDCRange>3 / PDCFault>1 / PDCDis>511` 任一越界即清空并返回 0，配合 `OnlinePort` 的"所有模块 and"门控，避免显示垃圾值。
- `read_echoData()` 的 246 字节布局：`samefreq_front_Cnt(2) + samefreq_rear_Cnt(2) + samefreq_front_Flag(1) + samefreq_rear_Flag(1) + rawdata_info[12]×20`；12 探头偏移 `4 + i*10`。

---

## 7. OnlinePort.py —— 帧构建与后台线程

### 7.1 数据模型

```python
RawProbeData    # 单个探头的原始数据（md/de/de_peak/ce_left/ce_left_peak/ce_right/ce_right_peak）
ObstacleSegment # 线段障碍物（sx,sy,ex,ey,height,obj_type,dist）
ObstaclePoint   # 点云障碍物（x,y,height,tx_idx,rx_idx）
SlotInfo        # 车位（pts = [A..F 六点]，已转 demo 坐标系；is_valid 属性）
VehicleInfo     # 车身参数（front_probes/rear_probes 字典，all_probes()）
```

### 7.2 数据转换

| 函数 | 作用 |
|---|---|
| `_echo_to_raw_probes()` | `DataSheet.raw_data[12]`（SNS 顺序）→ `RawProbeData` 列表（`ECHO_PROBE_NAME` 映射探头名） |
| `_pdc_ranges()` | `DataSheet.PDCRange/PDCDis` → `[(name, pd_range, dis_cm), ...]`（仅 `PDCRange != 0`；`=1 红/2 黄/3 绿`） |
| `pdc_info()` | 构建 `sf_Upper_PDCOutSignal` 全量字典（供 Show More Data PDC 页） |
| `_slots_from_datasheet()` | `DataSheet.SlotOut*` → `SlotInfo` 列表（`wx=X, wy=-Y` 坐标转换） |
| `read_vehicle_info_dict()` | 最近一次缓存的车身参数 dict（供 UI 线程应用） |

### 7.3 build_frame() —— 在线帧构建

从 `DataSheet` 当前数据组装一帧，返回 **9 元组**：

```python
(segments, points, gear, speed, raw_probes, pdc_ranges, slots,
 samefreq_front_flag, samefreq_rear_flag)
```

- `segments`：`PtLinetype[i]` 为真的线段
- `points`：`Ptype[i]` 为真的点云
- `pdc_ranges`：`_pdc_ranges()`
- `slots`：`_slots_from_datasheet()`
- `samefreq_*_flag`：`DataSheet.RawSameFreqFront/RearFlag`（驱动车前/后小灯）

### 7.4 OnlineReader 后台线程

```python
class OnlineReader(threading.Thread):
    # __init__(port='20001', backend='lauterbach')
    #   backend='lauterbach' → ReadDataPort.py（Trace32 RCL，port=RCL 端口）
    #   backend='csplus'     → ReadDataPort_CSPlus.py（CS+ Integration Service，port 忽略）
    #   display_name：状态栏显示的后端名称
    # run(): 连接 → 循环读取（50ms 周期）：
    #   read_StsData / read_vehicleInfo / read_PtData / read_PtLineData /
    #   read_echoData / read_PDCData / read_SlotOutData
    #   "所有模块 and"门控：全部成功才 build_frame() 更新 latest_frame
    #   （任一失败即冻结画面，不更新，避免显示乱值）
    # 错误处理：连接级错误（10053/10054 等）只打印控制台；
    #           其它错误经 _error_bridge → 队列 → UI 线程 drain_error() 弹窗
```

### 7.5 错误桥接

| 函数 | 作用 |
|---|---|
| `_error_bridge(msg)` | 后台线程回调；连接级错误抑制 5 秒内的尾随消息，避免刷屏 |
| `drain_error()` | UI 线程轮询：取出一条待显示错误（无则 None） |

---

## 8. vehicle_upper_demo.py —— 主界面

### 8.1 数据模型（文件顶部）

```python
class VehicleInfo       # 车身参数：length/width/front_probes/rear_probes/all_probes()
class ObstacleSegment   # 线段：index/sx/sy/ex/ey/height/prob/obj_type/dist
class ObstaclePoint     # 点云：index/x/y/tx_idx/rx_idx/height/prob
class RawProbeData      # 探头原始：name/md/de/de_peak/ce_left/ce_left_peak/ce_right/ce_right_peak
class _LogSlot          # 回放车位：index/slot_id/slot_type/width/depth/timestamp/a_type/f_type/pts[6]
class FrameData         # 一帧全部数据（__slots__）：segments/points/raw_probes/slots/
                        #   freq_front_flag/val, freq_rear_flag/val, temp/odo/pdc/car_* 等
class LogParser         # 日志解析器：parse() 分帧 → _parse_frame() 逐行解析
```

**日志解析（LogParser）**：
- 按 `={2,} Frame Index: (\d+) ={2,}` 分帧
- 头部解析车身参数（`VehicleInfo:`/`Length:`/`FLS_X:` 等）
- 每帧支持两类格式：
  1. **旧格式**：`stOneOutSi_Upper[i]`（线段）、`stPointOut_Upper[i]`（点云）、`RawInfo`（`探头名_MD:.. DE:.. PK:..`）
  2. **新格式**：`[sf_Upper_VehicleOutSignal] / [sf_Upper_StatusOutSignal] / [sf_Upper_OdoOutSignal] / [sf_Upper_RawDataOutSignal] / [sf_Upper_PDCOutSignal] / [sf_Upper_PointOutSignal] / [sf_Upper_LineOutSignal] / [sf_Upper_SlotOutSignal]` 分节 + 头两行 `TimeStamp/GearLever/VehicleSpeed/RawFrameIndex` 与 `SameFreq_Front/Rear_Flag`

### 8.2 画布 VehicleCanvas（tk.Canvas）

**核心坐标转换**：`world_to_canvas(wx, wy)` → `cx = offset_x - wy*scale, cy = offset_y - wx*scale`（wx=+前/上，wy=+左）。

**绘制方法（_draw() 调用顺序）**：

| 方法 | 内容 |
|---|---|
| `_draw_grid/_draw_axes` | 网格随缩放加密（默认视距细格 500mm、主格 1000mm）、坐标轴 |
| `_draw_vehicle_body` | 车身多边形、中心十字、**前/后同频小灯**（FLS/FRS 中点与 RLS/RRS 中点，`=1` 橙色亮/`=0` 灰暗）、车长/车宽文字 |
| `_draw_probes` | 12 个探头点（`PDCFault=1` 变红） |
| `_draw_probe_sectors` | 每个探头 120° 探测扇形（受 Show Sensor Info 开关控制） |
| `_draw_pdc_blocks` | **PDC 色块：60° 环形薄带**（外弧半径 = PDCDis，内弧半径 = dis-5cm；`PDCRange` 1红/2黄/3绿/0无；实色不透明；距离标签 `xxcm`） |
| `_draw_outline` | 车身外轮廓虚线 |
| `_draw_obstacles` | 线段/点云障碍物（按高度着色 + 信息标签，受 LINE/OBJ 开关控制） |
| `_draw_slots` | **车位 A~F 六点开放折线**（不过滤中间缺失点，B-C-D-E 也可连线；A/F 缺失不闭合）；`Show Slot Info` 时标注 A..F 顶点与车位类型 |
| `_draw_info` | 画布信息面板 + 图例 + **画布上开关按钮**（Explore/PDC/OBJ/LINE/SLOT，点击切换，悬停高亮） |
| `_draw_compass` | 指南针 |
| `_draw_measurement` | 点击测量两点距离 |

**交互**：右键复位。滚轮缩放和左键拖拽在实时报文刷新时不再逐事件整帧重绘：

- **左键拖拽**：没有连接、正在回放或正在在线时都一样。拖动时按像素平移当前画面，网格和车身跟着鼠标走，不再逐条重画。松手后按新视口整幅重绘，补上拖出屏幕的网格。拖动期间暂停实时/回放刷新。
- **滚轮缩放**：以鼠标位置为中心，连续滚动时按比例缩放 `world` 图元。停轮约 40ms 后整帧重绘，使线宽、文字和网格间距回到当前比例。界面按钮不跟着放大缩小。

**参照网格**：细格取 100/200/500/1000/2000/5000/10000 mm 中、使相邻线不少于约 48 px 的最密一档。默认比例 0.15 px/mm 时细格为 500 mm（虚线），主格为 1000 mm（更深实线）。放大到能放下 200 mm 或 100 mm 时自动加密，缩小时加粗间距，避免缩成一片。

### 8.3 Show More Data 面板 MoreDataPanel（ttk.Frame）

**科技感 UI**：深空蓝底 + 上下 2px 青色霓虹细条 + `MORE DATA // SYSTEM MONITOR` 标题栏 + `● DATA LINK` 指示 + **分段式标签页**（RAW/PDC/OBJ/LINE/SLOT，激活青色、悬停亮蓝）+ 表格行条纹 + 摘要 `▶` 前缀。全部使用 **ttk 控件**（避免 Windows 上 tk/ttk 混排导致 Treeview 滚动残影）。

**数据展示**：
- **Raw 页**：12 探头 8 列表格（整树重建，成本低）
- **结构体页（PDC/Obj/Line/Slot）**：**常显 + 增量更新**：
  - 所有结构体块按协议数量固定常显（PDC 39 字段、Obj 80、Line 20、Slot 6），缺失填 0
  - 节点用稳定 iid，已存在行只更新值、仅增删变化行（`_sync_rows`）
  - **默认收起**（open=False），用户展开/收起状态在刷新间保留
- **状态持久化**：`more_panel_state.json` 记忆各页展开状态 + 面板可见性（`save_state`/`_load_tree_state`/`saved_visible`）；首次启动默认收起

### 8.4 App 主窗口（tk.Tk）

**窗口**：1300×850，深色主题（`#0B1026`），标题来自 `src/app_version.py`（当前为 "COLIGEN USS UPPER v3.4.4"），ttk 主题 `clam`。

**布局**：顶部工具栏 → 控制面板（帧滑块+播放控制）→ 主 PanedWindow（画布 | Show More Data 面板）→ 底部状态栏。

**工具栏（_create_toolbar）**：

| 控件 | 功能 |
|---|---|
| Open Log... | 打开日志。TXT 走 `LogParser`；CAN 版同一个按钮还可打开 ASC/BLF，并按录制时间回放 |
| 在线连接 + Port | 在线模式开关（`_toggle_online`，端口可编辑） |
| 开始/停止录制 | `_toggle_record` / `_save_record` |
| Show More Data | 开关右侧数据面板（`_on_toggle_more_panel`） |
| Show Sensor/Line/Point/Slot Info | 画布各类信息标签开关 |
| Total Frames / 文件路径 | 信息显示 |

**控制面板（_create_control_panel）**：帧滑块 + `|<< / < / Play / > / >>|` + 播放速度（0.25~16 倍）+ 信息栏（`SF | TS | Gear | Speed | Temp`）。

**关键方法**：

| 方法 | 功能 |
|---|---|
| `_open_log()` | 文件对话框选日志 → `LogParser.parse()`（带进度）→ 更新帧数/车辆/画布 |
| `_jump_to_frame(idx)` | 跳帧：更新画布（含 PDC/车位/同频小灯）、信息栏、MoreData 面板；录制中自动记录本帧 |
| `_start_play/_stop_play/_play_tick` | 播放/暂停（`delay = 100/play_speed` ms） |
| `_toggle_online/_online_tick/_disconnect_online` | 在线模式生命周期：启动 `OnlineReader` 后台线程 → 50ms 轮询 `read_latest()` → 应用到画布/信息栏/MoreData；断开时恢复回放控件（`_set_playback_enabled`） |
| `_record_frame(...)` | 把一帧格式化为日志文本块（按 `sf_Upper_VehicleOutSignal→Status→Odo→RawData→PDC→Point→Line→Slot` 顺序） |
| `_save_record()` | 保存 TXT 日志 + `_write_raw_csv()` 导出前/后传感器 CSV（含标题、MODE/DE/PEAK/CE 交叉回波列） |
| `_build_online_snap/_build_offline_snap` | 在线/回放录制快照（含 pdc/raw_data/samefreq/slot_meta 等） |
| `_on_window_resize` | 窗口缩放时按参考尺寸缩放字体 |
| `_bind_keys` | 快捷键：`Ctrl+0`/`r` 复位、`←/→` 步进、`Space` 播放、`Home/End` 首末帧、`Ctrl+o` 打开 |
| `_fit_to_window` | 自动缩放画布至适合窗口 |
| `on_closing` | 关闭：停播放 → 断在线 → **保存 Show More Data 状态** → destroy |

**main() 入口**：
- 自动探测脚本目录下的 `.txt` 日志并解析；无则用内置默认车身参数（`FLS..FRS`/`RLS..RRS` 坐标）创建空车辆
- 创建 `App` 进入 `mainloop()`

---

## 9. 坐标系与关键约定

点和线、TXT 与 ASC 的转换规则以 [`docs/COORDINATE_SYSTEMS.md`](COORDINATE_SYSTEMS.md) 为准。摘要：

| 约定 | 说明 |
|---|---|
| **demo 坐标系** | `wx=+前`（向上）、`wy=+左`（向左），单位 mm；所有源最终都转成它再画 |
| **TXT 新格式（泊车3.txt）** | `[sf_Upper_Point/LineOutSignal]` 已是 demo，**原样显示**（周立功接入前规则，保持不变） |
| **TXT 旧格式 / 旧文件头** | `X=+右, Y=+前` → `wx=Y, wy=-X` |
| **main/C（劳特巴赫/CS+）** | `X=+前, Y=+右` → `wx=X, wy=-Y` |
| **ASC/CAN 点** | DBC cm→mm 后 `wx=X, wy=Y`（不互换、不取反） |
| **ASC/CAN 线** | `wx=Ay, wy=Ax`（只互换轴，不再 Y 取反） |
| **SNS_STR_LIST 顺序** | `RRS, RRC, RRM, RLM, RLC, RLS, FRS, FRC, FRM, FLM, FLC, FLS` |
| **探头角向** | FLS/RLS→180°(左)、FRS/RRS→0°(右)、FLC/FRC→135°/45°、RLC/RRC→225°/315°、FLM/FRM/RLM/RRM→90°/270° |
| **PDC range** | `0=无 1=红 2=黄 3=绿`；`PDCDis` 0/511 为默认/无效，有效 1..510 |
| **车速** | `VehicleSpeed` 为浮点 km/h（不再取整） |

---

## 10. 自测脚本 _selftest.py

用**桩 dbg（FakeDBG）** 在无 Trace32 环境下验证 `ReadDataPort` 的读取与重试逻辑。

### 10.1 桩实现

```python
class FakeVar/FakeMem/FakeDBG
    # 按符号名生成固定地址（0x400000+i*0x100），
    # memory.read 返回预打包的字节缓冲；fail 参数模拟瞬时失败次数；
    # status 提供 dbg.variable.read 的变量值（如 Speed=12.7）
```

### 10.2 测试缓冲（build_buffers）

| 符号 | 打包格式 | 关键测试值 |
|---|---|---|
| `sf_Upper_VehicleOutSignal` | `'HH'+'hh'*12` | 4922×1876 |
| `sf_Upper_PDCOutSignal` | `'BBBx'+'HBB'*12` | dis=100..111, range=1, fault=0 |
| `sf_Upper_PointOutSignal` | `'HhhBBBB'*80` | x=100+i, y=200+i |
| `sf_Upper_LineOutSignal` | `'BBBBhhhhH'*20` | 坐标 100+i..400+i |
| `sf_Upper_RawDataOutSignal` | `'HHBB'+'BxHHHHHHHHH'*12` | 同频 Cnt=100/200, Flag=1/1 |
| `sf_Upper_OdoOutSignal` | `'fff'` | 1.5/-2.5/0.3 |

### 10.3 测试项（30 项全部通过）

- 正常路径：7 个 `read_*()` 返回 1，DataSheet 关键值断言（含 PDC/同频/浮点车速）
- 永久性错误：符号缺失 → 返回 0 且上报一次
- 瞬时失败 3 次 → 重试成功 + 触发 `SYStem.Attach`
- 持续瞬时失败 → 10 次后放弃返回 0

**运行**：`uv run python tests/selftest.py` → `passed=30 failed=0`

---

## 11. 打包配置

`VehUpperDemo.spec`（PyInstaller）：

```python
Analysis(['vehicle_upper_demo.py'], datas=[('car.ico', '.')], ...)
EXE(name='vehicle_upper_demo', icon=['car.ico'], console=False, upx=True, ...)
```

- 打包为无控制台的 Windows 窗口程序
- 打包命令示例：`uv run pyinstaller VehUpperDemo.spec`
- 注意：`more_panel_state.json` 由程序运行时在**可执行文件同目录**生成

---

## 12. 运行方式

```bash
# 必须使用 Python 3（本机默认 python 可能是 2.7）
python3 vehicle_upper_demo.py     # 启动主程序（自动探测目录下 .txt 日志）
python3 _selftest.py              # 运行自测（30 项）
```

在线模式需：
1. 目标板程序编译时启用 `LAUTERBACH_UPPER_DEBUG`
2. Trace32 已启动并允许远程控制（`RESet/PORT`）
3. 点击"在线连接"，默认端口 20001（可在输入框修改）

---

## 13. 功能模块要点与注意事项

### 13.1 PDC 色块（60° 环形薄带，实色）
- 以探头为中心画 **60° 环形薄带**（`center_angle ± 30°`）：**外弧半径 = `PDCDis`、内弧半径 = dis-5cm**，不填充中心区域
- **实色不透明**（无 stipple）
- 颜色以 `PDCRange` 为准：`1=红 #FF3B5C、2=黄 #FFC93C、3=绿 #00E58C、0=无`
- `dis` 有效（≠0 且 ≠511）时在色块外缘显示 `xxcm`
- 12 探头数据 `[(name, range, dis_cm)]` 来自 `OnlinePort._pdc_ranges()`（在线）/ `_frame_pdc_ranges()`（回放），顺序均为 SNS_STR_LIST

### 13.2 车位 A~F
- 画布上按 `A→B→C→D→E→F` 顺序画**开放折线（不闭合）**
- 仅两种场景：完整 6 点或中间 4 点（B-C-D-E），缺失点（0,0）自动过滤；标签保留原始字母
- Show More Data Slot 页固定常显 6 个槽位

### 13.3 同频小灯
- C 端 `samefreq_front/rear_Flag`（=1）→ `DataSheet.RawSameFreq*Flag` → `build_frame` 9 元组末尾 → `set_obstacles(front_flag, rear_flag)` → 车前/车后橙色小灯点亮
- 回放模式由日志头两行 `SameFreq_Front/Rear_Flag` 携带

### 13.4 Show More Data 面板
- 各分页（含结构体页）**保持数据实时更新**（无降频）
- 结构体页**常显 + 增量更新 + 默认收起**，刷新不干扰展开/选中/滚动
- 关闭软件时记忆状态到 `more_panel_state.json`（首次启动默认收起、面板隐藏）

### 13.5 顶部按钮高亮
- 按钮样式仅保留 `pressed/active` 瞬态，**不设 `focus` 焦点态**，点击释放后自动恢复原色

### 13.6 常见注意事项
- **必须用 `python3`**（`_selftest.py` 用了 `nonlocal`，Python 2 会 SyntaxError）
- 在线读取"所有模块 and"门控：任一模块读取失败即冻结画面，避免显示乱值
- 修改 C 端结构体后，`ReadDataPort.read_*()` 的**长度/解包格式**与 `DataSheet` 需同步更新（本工程曾经历 PDC/RawData 结构体重构）
- 录制导出的 CSV 与参考 `1_SnsSorRawData_Front/Rear.csv` 格式一致（无回波哨兵值 32767）

---

*文档生成时间：2026-08-13，基于当前源码快照。*












