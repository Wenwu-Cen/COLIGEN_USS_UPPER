# 可视化坐标系说明

画布只认一种坐标：**demo 坐标系**。所有数据源必须先转成 demo，再调用 `world_to_canvas()`。

TXT 日志（`recordings/泊车3.txt`，引入周立功之前）和 ASC/CAN 的**源坐标系不同**，转换规则分开维护，互不套用。

---

## 1. 画布（demo）坐标系

单位 **mm**。原点在车辆参考中心。

```text
              wx +前  → 屏幕向上
                    ↑
                    |
    wy +左 ←--------+--------→ 右（wy 为负）
     屏幕向左       |
                    ↓
                  后（wx 为负）
```

屏幕映射（`VehicleCanvas.world_to_canvas`）：

```text
cx = offset_x - wy * scale
cy = offset_y - wx * scale
```

界面标签：`X+ (forward) → up`，`Y+ (left) → left`。  
More Data / 线段标签里的 `(sx,sy)`、点标签里的 `(x,y)` 都是 **demo 值**，不是 DBC 原始值。

---

## 2. 数据源对照（点和线）

| 数据源 | 入口 | 源单位 | 点 → demo | 线 → demo |
|---|---|---|---|---|
| **TXT 新格式**（泊车3.txt 的 `[sf_Upper_PointOutSignal]` / `[sf_Upper_LineOutSignal]`） | `VehUpperDemo.LogParser` | mm | **原样** `wx=x, wy=y` | **原样** `wx=wStartx, wy=wStarty` |
| **TXT 旧格式**（`stPointOut_Upper` / `stOneOutSi_Upper`） | 同上 | mm | `wx=Y, wy=-X` | `wx=Y, wy=-X` |
| **劳特巴赫 / CS+** | `OnlinePort.build_frame` | mm | `wx=X, wy=-Y` | `wx=X, wy=-Y` |
| **ASC / 周立功 / CANoe** | `CanOnlinePort.VisualizationModel` | DBC 原始 cm（offset −3276）→ mm | `wx=X_mm, wy=Y_mm`（不互换、不取反） | `wx=Ay_mm, wy=Ax_mm`（只互换，不再取反） |

引入周立功之后：**只新增了 ASC/CAN 这一列**。泊车3.txt 仍走 TXT 列，坐标规则没有改。

---

## 3. TXT 日志（周立功之前，以泊车3.txt 为例）

文件同时带两种写法。解析器两套都认，规则不同。

### 3.1 文件头探头（旧横向/纵向）

```text
FLC_X:-795 FLC_Y:3336
```

约定：**X=+右，Y=+前**。转 demo：

```text
wx = Y = 3336   （前）
wy = -X = 795   （左）
```

FLC 是前左探头，转换后出现在画布左前方，与车身轮廓一致。

### 3.2 新格式点和线（泊车3.txt 主体）

```text
Point[0] ObjID = 0 x = 5315 y = 1290 cHight = 0 SNS_Txindex = 10 SNS_Rxindex = 9
Line[0]  wStartx = 5281 wStarty = 1221 wEndx = 5281 wEndy = 1221
```

这两行在录制时已经是 **demo 坐标**（在线路径 `OnlinePort` 转完再写入 TXT）。回放时：

```text
点:  wx = x = 5315,  wy = y = 1290
线:  起点 (5281, 1221)，终点同样，不再 XY 互换、不再 Y 取反
```

`SNS_Txindex = 10` 是 FLC（前左角）。`y = 1290` 为正，落在车左，和探头侧别一致。

**不要把 ASC 的线互换/取反套到这种 TXT 上**，否则左右会翻掉。

### 3.3 旧格式点和线（更早的 st* 行）

若日志里仍是 `stPointOut_Upper[i]` / `stOneOutSi_Upper[i]`，则与文件头相同：

```text
源 X=+右, Y=+前
demo wx = Y, wy = -X
```

---

## 4. ASC / 周立功 CAN（当前规则）

DBC 解码使用 `scaling=False`，坐标再按：

```text
mm = (raw + (−3276)) × 10
```

即 1 cm → 10 mm。无效/默认常见为 raw=0 或距离 `0x0FFF`。

### 4.1 点云 `Point_NN_X / Point_NN_Y`

与 TXT 新格式进画布的方式相同：**不互换、不取反**。

```text
wx = X_mm
wy = Y_mm
```

### 4.2 线段 `Ax/Ay` 或 `P1X/P1Y`

ObstacleTrack 的轴和旧 TXT 头一样：**Ax/P1X 为横向，Ay/P1Y 为前向**。转 demo 只做轴互换：

```text
wx = Ay_mm     （前）
wy = Ax_mm     （左）
```

**不再做 `wy = -Ax`。** 多一次取反会把右后目标画到左后（S20test.asc / 实车 PDC 对过）。

### 4.3 车位槽

CAN 车位画 **B、C、D、E**（A/F 常为原点，仍不画）。四点齐全时闭合。

固件按 DBC 以 **厘米** 下发 B/C/D/E（原点 3276）。画布是毫米：

```text
mm = (raw − 3276) × 10
```

垂直（B–E 主要沿 DBC X）：`wx = X_mm`（前），`wy = Y_mm`（左）。  
水平（B–E 主要沿 DBC Y）：`wx = Y_mm`（前），`wy = -X_mm`（右为负）。

B、E 是靠近车侧的入口，C、D 是库位里侧。往前开时 B/C 在后、E/D 在前。左侧入口 `wy>0`，右侧入口 `wy<0`；若整框落在对侧则先翻 Y。若 C/D 落到 B/E 的车体内侧，则把它们镜到该侧库内。车位是自车系，不减 `0x640` DR。点云和线段仍走原来的 cm→mm，也不做这次 DR。

CS+/TXT 车位仍走原来的 `wx = X, wy = -Y`。

---

## 5. 劳特巴赫 / CS+（main / C 结构体）

`sf_Upper_PointOutSignal` / `sf_Upper_LineOutSignal` 在板端是：

```text
X = +前, Y = +右
demo: wx = X, wy = -Y
```

实现：`OnlinePort.build_frame`。录成 TXT 之后，新格式点和线已经是 demo，回放不再转一次。

---

## 6. 用一个数看差异

假设障碍在车**前方 2 m、左侧 0.5 m**，demo 应为 `(wx, wy) = (2000, 500)`。

| 源里怎么写 | 解析后 demo |
|---|---|
| TXT 新格式 `x=2000 y=500` | `(2000, 500)` 原样 |
| TXT 旧格式 / 旧头 `X=−500 Y=2000`（X=+右） | `wx=2000, wy=-(-500)=500` |
| 调试器 main `X=2000 Y=−500`（Y=+右） | `wx=2000, wy=-(-500)=500` |
| ASC 点 `X_raw, Y_raw` → mm 已是 `(2000, 500)` | `(2000, 500)` 原样 |
| ASC 线 `Ax`→0.5 m 左、`Ay`→2 m 前 | `wx=Ay=2000, wy=Ax=500` |

若把 ASC 线再执行 `wy = -wy`，会变成 `(2000, -500)`，画到**右侧**，这就是「左右对称、搞反了」。

---

## 7. 可视化不做几何补偿

画布**没有**再对点、线做安装位置、轴距、后轴/车中心之类的补偿。  
`world_to_canvas()` 只做 demo→屏幕；ASC 仅有 DBC 单位换算 `(raw − 3276) × 10`（cm→mm），点和线用同一公式。

因此同一障碍的点和线可以差几厘米到一两分米：线是 ECU 拟合段，点是点云，GUI 不会把点吸到线上。  
用 `S20test.asc` 量过：当前映射下点到最近线段约 **11 cm**；若把点也按线那样 XY 互换，偏差反而到约 **30 cm**。

另外：绿色小点若是 **Obst low（点云）** 才和黄线比位置；图例里 **PDC Range=3** 也是绿色，但 PDC 是从探头沿朝向按距离画的色带，本来就不会和 MapObj 线段重合。

---

## 8. 代码入口

| 路径 | 文件 | 函数 |
|---|---|---|
| 画布 | `src/VehUpperDemo.py` | `VehicleCanvas.world_to_canvas` |
| TXT | `src/VehUpperDemo.py` | `LogParser._parse_frame` / `_parse_header` |
| 调试器 | `src/OnlinePort.py` | `build_frame` |
| ASC/CAN | `src/CanOnlinePort.py` | `VisualizationModel._coord` / `_store_segment` / `frame` |

相关测试：`tests/test_coordinate_systems.py`、`tests/test_can_online_port.py`。
