import sys
import struct
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import lauterbach.trace32.rcl as t32
import numpy as np
import DataSheet
from DataSheet import *

RETRY_TIME = 0.030  # s

dbg = None

# ----------------------------------------------------------------
# 错误上报（供 UI 层弹窗显示，避免只在控制台打印刷屏）
# ----------------------------------------------------------------
ERROR_CALLBACK = None
_last_reported_error = None


def set_error_callback(cb):
    """注册错误回调，回调参数为错误消息字符串（传 None 注销）。"""
    global ERROR_CALLBACK
    ERROR_CALLBACK = cb


def _is_permanent_error(e):
    """判断是否为永久性错误（重试无法解决，例如符号未找到）。"""
    msg = str(e).lower()
    return ('symbol not found' in msg or 'not found' in msg)


def _report_error(msg):
    """上报错误：调用已注册的回调并打印到控制台。
    连续相同的错误只上报一次，避免刷屏。
    """
    global _last_reported_error
    if msg == _last_reported_error:
        return
    _last_reported_error = msg
    try:
        if ERROR_CALLBACK:
            ERROR_CALLBACK(msg)
    except Exception:
        pass
    print(msg)


def read_port_connect(info):
    global dbg
    global _last_reported_error
    _last_reported_error = None  # 重新连接后允许再次上报相同错误
    try:
        dbg = t32.connect(port=str(info))
    except Exception as e:
        raise RuntimeError('无法连接 Trace32 RCL (port=%s): 请确认 Trace32 已启动、'
                           '已允许远程控制<RESet/PORT>，且端口号正确。原始错误: %s' % (info, e))
    try:
        dbg.cmd("SYStem.Attach")
    except Exception as e:
        raise RuntimeError('Trace32 已连通 (port=%s) 但 SYStem.Attach 失败: '
                           '请确认目标板已上电/复位，或先在 Trace32 中手动执行 Attach。原始错误: %s' % (info, e))


def read_port_disconnect():
    dbg.disconnect()


def reconnect():
    """连接可能断开时尝试重新连接（对应 CS+ 路径的 _connect_backend）。"""
    if dbg is None:
        return
    try:
        dbg.cmd("SYStem.Attach")
    except Exception:
        pass


# ----------------------------------------------------------------
# 通用读取辅助：符号地址解析缓存 + 失败重试 + 错误上报
# ----------------------------------------------------------------
# 符号地址缓存：连接后按需解析一次并缓存。
# 初始 0 地址直接 memory.read() 在地址恰好可读（如 flash 向量表）时
# 会静默读到垃圾数据且不触发符号解析，所以必须先经 _resolve_symbol 解析。
_ADDR_CACHE = {}


def _resolve_symbol(symbol):
    """解析并缓存符号地址；symbol 缺失时抛出（由 _retry 上报）。"""
    if symbol not in _ADDR_CACHE or _ADDR_CACHE[symbol] == 0:
        addrstr = dbg.fnc(symbol)
        _ADDR_CACHE[symbol] = dbg.address.from_string(addrstr)
    return _ADDR_CACHE[symbol]


def _retry(desc, callback):
    """通用读取重试封装：执行 callback() 直到成功。
    desc   : 中文模块名，用于错误消息（如 '点云' → '点云读取失败'）
    callback: 每次尝试执行的函数，成功返回其返回值。

    永久性错误(symbol not found 等)直接上报并返回 None；
    其余错误上报后重试（每次重试前尝试重新 SYStem.Attach），
    超过 10 次后上报并返回 None。
    """
    err = 1
    while err:
        try:
            return callback()
        except Exception as e:
            if _is_permanent_error(e):
                _report_error('%s读取失败: %s' % (desc, e))
                return None
            # 非永久性错误（连接瞬断/地址不可读等）：重试前尝试重新 Attach 并计数上报，
            # 保证任何一次读取失败都会累加 err，避免“地址一直读取却永不报错”的死循环。
            try:
                dbg.cmd("SYStem.Attach")
            except Exception:
                pass
            time.sleep(RETRY_TIME)
            err = err + 1
            _report_error('%s读取失败: %s' % (desc, e))
            if err > 10:
                _report_error('%s读取失败(重试 %d 次后放弃)' % (desc, err - 1))
                return None


def _read_symbol(desc, symbol, length, fmt):
    """read_symbol 的常用形态：解析符号地址 + memory.read + struct.unpack。"""
    def _do():
        return struct.unpack(fmt, dbg.memory.read(
            _resolve_symbol(symbol), length=length, width=4))
    return _retry(desc, _do)


# read test
"""
import lauterbach.trace32.rcl as t32
import struct
dbg = t32.connect(port = '20001')
dbg.cmd("SYStem.Attach")
while True:
    PtNum = dbg.variable.read("ParkingSlot_Data_st_Output.NumOfParkingSlot").value
    if PtNum >0:
        addrstr = dbg.fnc("ParkingSlot_Data_st_Output")
        address = dbg.address.from_string(addrstr)
        buffer = dbg.memory.read(address,length=384, width=4)
        format_str = '<' + 'hhhhhhhhHHIIII' * 8
        read_data = struct.unpack(format_str, buffer)
        print(PtNum,read_data)
    time.sleep(0.05)
"""


def read_vehicleInfo():
    """读取 sf_Upper_VehicleOutSignal 车身参数（车长/车宽/12探头位置）。
    结构体 Upper_VehicleOutSignal（默认 2 字节对齐，无 padding，52 字节）：
        uint16_t CarLength;         // offset 0
        uint16_t CarWidth;          // offset 2
        int16_t  SnsPosRRS_X/Y;     // offset 4..7
        ...(12 组传感器位置 SnsPos*_X/Y, RRS->FLS 顺序)
    坐标系（与 main 一致）：X=纵向(+前), Y=横向(+右)
    """
    # CarLength, CarWidth, 12*(x,y)
    read_data = _read_symbol('车身参数', 'sf_Upper_VehicleOutSignal', 52,
                             '<' + 'HH' + 'hh' * 12)
    if read_data is None:
        return 0

    # read_data: [0]=CarLength, [1]=CarWidth, [2:]=12组(x,y)（RRS..FLS）
    DataSheet.VehicleLength = int(read_data[0])
    DataSheet.VehicleWidth = int(read_data[1])
    for i in range(12):
        DataSheet.VehicleProbePos[i] = (int(read_data[2 + i * 2]),
                                        int(read_data[3 + i * 2]))
    return 1


def read_PDCData():
    """读取 sf_Upper_PDCOutSignal PDC 报警信号（仅在线读取）。

    结构体 Upper_PDCOutSignal 52 字节：
        uint8_t  pdc_sts;               // offset 0
        uint8_t  front_sts;             // offset 1
        uint8_t  rear_sts;              // offset 2
        uint8_t  padding;               // offset 3 <uint16_t 对齐>
        Upper_PDCOutSignalInfo snspdc_info[12]; // offset 4..51
            // 每项 4 字节: uint16_t dis; uint8_t range; uint8_t fault

    探头顺序即 SNS_STR_LIST: RRS,RRC,RRM,RLM,RLC,RLS,FRS,FRC,FRM,FLM,FLC,FLS
    存储在 DataSheet.PDCDis/PDCRange/PDCFault（同序直写，无需转换）。
    """
    read_data = _read_symbol('PDC 信号', 'sf_Upper_PDCOutSignal', 52,
                             '<' + 'BBBx' + 'HBB' * 12)
    if read_data is None:
        return 0

    # read_data 索引(内存 offset 见函数 docstring；'x' 填充不产生输出值)：
    #   [0]=pdc_sts [1]=front_sts [2]=rear_sts
    #   [3+i*3]=dis、[4+i*3]=range、[5+i*3]=fault (i=0..11，与 C 结构体按探头交错)
    # 结构体 snspdc_info[0..11] 即 SNS_STR_LIST 顺序：
    #   RRS,RRC,RRM,RLM,RLC,RLS,FRS,FRC,FRM,FLM,FLC,FLS
    # 故直接按序写入 DataSheet，无需反转。

    DataSheet.PDC_Sts = int(read_data[0])
    DataSheet.PDC_FrontSts = int(read_data[1])
    DataSheet.PDC_RearSts = int(read_data[2])

    # 从 12 组（dis，range，fault）中拆出 3 个数组（结构体顺序 == SNS_STR_LIST 顺序）
    DataSheet.PDCDis = [read_data[3 + i * 3] for i in range(12)]
    DataSheet.PDCRange = [read_data[4 + i * 3] for i in range(12)]
    DataSheet.PDCFault = [read_data[5 + i * 3] for i in range(12)]

    # ==============================================================================
    # 数据有效性校验：地址缓存/结构体布局不对上时，memory.read 往往能
    # 成功（不抛异常）但解出的是垃圾值，此时必须返回失败，让上位机
    # “所有模块 and”门控（OnlinePort 第 501/527 行）能检测出 PDC 没读对，
    # 而不是静默显示乱值。
    # 协议取值范围（与 OnlinePort._pdc_ranges / _draw_pdc_blocks 一致）：
    #    PDCRange 0..3 (0‑无，1‑红，2‑黄，3‑绿)
    #    PDCDis   0..511 (0/511 为默认/无效，有效 1..510)
    #    PDCFault 0..1
    # ==============================================================================

    if (any(r > 3 for r in DataSheet.PDCRange)
            or any(f > 1 for f in DataSheet.PDCFault)
            or any(d > 511 for d in DataSheet.PDCDis)):
        # 清空，避免 pdc_info()/Show More Data 面板读到残留垃圾数据
        DataSheet.PDC_Sts = 0
        DataSheet.PDC_FrontSts = 0
        DataSheet.PDC_RearSts = 0
        DataSheet.PDCDis = [0] * 12
        DataSheet.PDCRange = [0] * 12
        DataSheet.PDCFault = [0] * 12

        _report_error('PDC 信号数据校验失败（疑似 sf_Upper_PDCOutSignal 地址或结构体布局不对）')
        return 0

    return 1


# =================================================================
# sf_Upper_SlotOutSignal 车位信号（在线读取）
# =================================================================

# Upper_SlotOutSignalInfo（slot_width/slot_Depth 为 uint16_t 版）：
# 劳特巴赫实测：Upper_SlotOutSignalInfo = 48 字节、Upper_SlotOutSignal = 296 字节，
# 即工程按 8 字节对齐编译（3 字节头部 + 5 字节 padding，left_slot_info 从偏移 8 开始）。
#   uint64_t timestamp;     // 0
#   uint8_t  slot_id;       // 8
#   uint8_t  slot_type;     // 9
#   uint16_t slot_width;    // 10
#   uint16_t slot_Depth;    // 12
#   int16_t  slot_A_x;      // 14
#   int16_t  slot_A_y;      // 16
#   uint8_t  slot_A_type;   // 18
#   int16_t  slot_B..F x/y; // 20..38
#   uint8_t  slot_F_type;   // 40
#   pad[7];                 // 41..47（补齐到 48 字节）
_SLOT_OUT_INFO_FORMAT = '<QBBHHhhBx' + 'hhhhhhhhhh' + 'Bx'   # 字段解包 42 字节
_SLOT_OUT_INFO_SIZE = 48    # sizeof(Upper_SlotOutSignalInfo)，8 字节对齐下（劳特巴赫实测）

# left_slot_info 起始偏移与单个结构体大小（8 字节对齐，实测确认）
_SLOT_OUT_LAYOUTS = ((8, 48),)

# 整个 Upper_SlotOutSignal = 8 + 6*48 = 296 字节（劳特巴赫实测）
_SLOT_OUT_STRUCT_SIZE = 296

SlotOutLayout = None    # (left_slot_info 起始偏移, 单个 info 结构体大小)，解析一次后缓存


def _pick_slot_layout(buffer):
    """确定 Upper_SlotOutSignal.left_slot_info 的起始偏移与单个结构体大小。
    返回 (left_slot_info 起始偏移, 单个 info 结构体大小)。
    工程为 8 字节对齐（劳特巴赫实测 Upper_SlotOutSignalInfo=48、总=296），
    布局固定为 (8, 48); 仍保留调试器真值校验(dbg.variable.read 解析 slot_A_x
    真值比对) 与启发式评分作双保险，避免布局假设错误时静默解析出垃圾数据。
    """
    global SlotOutLayout
    if SlotOutLayout is not None:
        return SlotOutLayout

    # 1) 真值法：完全依赖调试器符号信息，与内存布局假设无关
    try:
        gt_ax = []
        for i in range(6):
            gt_ax.append(int(dbg.variable.read(
                'sf_Upper_SlotOutSignal.left_slot_info[%d].slot_A_x' % i).value))
        best, best_match = _SLOT_OUT_LAYOUTS[0], -1
        for off, stride in _SLOT_OUT_LAYOUTS:
            match = 0
            for i in range(6):
                try:
                    info = struct.unpack_from(_SLOT_OUT_INFO_FORMAT, buffer,
                                              off + i * stride)
                except Exception:
                    break
                if gt_ax[i] != 0 and int(info[5]) == gt_ax[i]:
                    match += 1
            if match > best_match:
                best, best_match = (off, stride), match
        if best_match > 0:
            SlotOutLayout = best
            return best
    except Exception:
        pass

    # 2) 启发式评分
    best, best_score = _SLOT_OUT_LAYOUTS[0], -1
    for off, stride in _SLOT_OUT_LAYOUTS:
        score = 0
        for i in range(6):
            try:
                info = struct.unpack_from(_SLOT_OUT_INFO_FORMAT, buffer,
                                          off + i * stride)
            except Exception:
                break
            (ts, sid, styp, sw, sd, ax, ay, at, bx, by, cx, cy,
             dx, dy, ex, ey, fx, fy, ft) = info
            # 属性字段（slot_id/slot_type/slot_A_type/slot_F_type）应为小值
            for v in (sid, styp, at, ft):
                if 0 <= v <= 20:
                    score += 1
            # 六点坐标应为合理的毫米值（车位通常不超过 ±30000mm）
            for v in (ax, ay, bx, by, cx, cy, dx, dy, ex, ey, fx, fy):
                if -30000 <= v <= 30000:
                    score += 1
        if score > best_score:
            best, best_score = (off, stride), score
    SlotOutLayout = best
    return best


def read_SlotOutData():
    """读取 sf_Upper_SlotOutSignal 车位信号并存入 DataSheet.SlotOut*。

    结构体 Upper_SlotOutSignal:
        uint8_t slot_sts;                 // offset 0
        uint8_t left_slot_num;            // offset 1
        uint8_t right_slot_num;           // offset 2
        Upper_SlotOutSignalInfo left_slot_info[3];  // 左 3 个车位
        Upper_SlotOutSignalInfo right_slot_info[3]; // 右 3 个车位

    只解析纯符号名 sf_Upper_SlotOutSignal（与工程其它信号相同的已验证方式），
    从基址一次性读取整个结构体内存块；left_slot_info 起始偏移与单个结构体大小
    通过 _pick_slot_layout() 运行时确定，不依赖编译器对齐假设。
    坐标存入 DataSheet（main 坐标系：X=+前，Y=+右，单位 mm）。
    """
    # 清空上一帧数据
    DataSheet.SlotOutNum = 0
    DataSheet.SlotOutLeftNum = 0
    DataSheet.SlotOutRightNum = 0
    DataSheet.SlotOutSts = 0
    for i in range(6):
        DataSheet.SlotOutValid[i] = 0
        DataSheet.SlotOutId[i] = 0
        DataSheet.SlotOutType[i] = 0
        DataSheet.SlotOutWidth[i] = 0
        DataSheet.SlotOutDepth[i] = 0
        DataSheet.SlotOutAx[i] = 0
        DataSheet.SlotOutAy[i] = 0
        DataSheet.SlotOutBx[i] = 0
        DataSheet.SlotOutBy[i] = 0
        DataSheet.SlotOutCx[i] = 0
        DataSheet.SlotOutCy[i] = 0
        DataSheet.SlotOutDx[i] = 0
        DataSheet.SlotOutDy[i] = 0
        DataSheet.SlotOutEx[i] = 0
        DataSheet.SlotOutEy[i] = 0
        DataSheet.SlotOutFx[i] = 0
        DataSheet.SlotOutFy[i] = 0
        DataSheet.SlotOutTime[i] = 0
        DataSheet.SlotOutAType[i] = 0
        DataSheet.SlotOutFType[i] = 0

    def _do():
        # 整个结构体一次性读取（覆盖 2/4/8 字节对齐下的全部布局）
        buffer = dbg.memory.read(_resolve_symbol('sf_Upper_SlotOutSignal'),
                                  length=_SLOT_OUT_STRUCT_SIZE, width=4)
        slot_sts, left_slot_num, right_slot_num = struct.unpack_from('<BBB', buffer, 0)
        left_off, info_stride = _pick_slot_layout(buffer)
        infos = []
        for i in range(6):
            infos.append(struct.unpack_from(_SLOT_OUT_INFO_FORMAT, buffer,
                                            left_off + i * info_stride))
        return slot_sts, left_slot_num, right_slot_num, infos

    res = _retry('车位信号', _do)
    if res is None:
        return 0
    slot_sts, left_slot_num, right_slot_num, infos = res

    DataSheet.SlotOutSts = int(slot_sts)
    DataSheet.SlotOutLeftNum = int(left_slot_num)
    DataSheet.SlotOutRightNum = int(right_slot_num)
    DataSheet.SlotOutNum = int(left_slot_num) + int(right_slot_num)

    for i, info in enumerate(infos):
        (timestamp, slot_id, slot_type, slot_width, slot_depth,
         ax, ay, a_type, bx, by, cx, cy, dx, dy, ex, ey, fx, fy, f_type) = info
        # 有效判据：六点坐标至少两点非零（坐标全 0 视为空槽位）
        nonzero = [v for v in (ax, ay, bx, by, cx, cy, dx, dy, ex, ey, fx, fy)
                   if v != 0]
        if len(nonzero) < 2:
            continue
        DataSheet.SlotOutValid[i] = 1
        DataSheet.SlotOutId[i] = int(slot_id)
        DataSheet.SlotOutType[i] = int(slot_type)
        DataSheet.SlotOutWidth[i] = int(slot_width)
        DataSheet.SlotOutDepth[i] = int(slot_depth)
        DataSheet.SlotOutAx[i] = int(ax)
        DataSheet.SlotOutAy[i] = int(ay)
        DataSheet.SlotOutBx[i] = int(bx)
        DataSheet.SlotOutBy[i] = int(by)
        DataSheet.SlotOutCx[i] = int(cx)
        DataSheet.SlotOutCy[i] = int(cy)
        DataSheet.SlotOutDx[i] = int(dx)
        DataSheet.SlotOutDy[i] = int(dy)
        DataSheet.SlotOutEx[i] = int(ex)
        DataSheet.SlotOutEy[i] = int(ey)
        DataSheet.SlotOutFx[i] = int(fx)
        DataSheet.SlotOutFy[i] = int(fy)
        DataSheet.SlotOutTime[i] = int(timestamp)
        DataSheet.SlotOutAType[i] = int(a_type)
        DataSheet.SlotOutFType[i] = int(f_type)
    return 1

def read_StsData():
    """读取车辆状态（档位/速度/温度/时间戳）与里程计数据。"""
    def _do():
        DataSheet.VehicleGear = dbg.variable.read("sf_Upper_StatusOutSignal.GearLever").value
        DataSheet.VehicleTemp = dbg.variable.read("sf_Upper_StatusOutSignal.Temp").value
        DataSheet.VehicleTimeStamp = dbg.variable.read("sf_Upper_StatusOutSignal.TimeStamp").value
        speed = dbg.variable.read("sf_Upper_StatusOutSignal.Speed").value
        # 车速单位为 km/h, C 端为 float <sf_Upper_StatusOutSignal.Speed>, 保持浮点型
        DataSheet.VehicleSpeed = float(speed)

        read_data = struct.unpack('<fff',
            dbg.memory.read(_resolve_symbol('sf_Upper_OdoOutSignal'),
            length=12, width=4))
        # 里程计角度合理范围校验：超范围说明读到的是垃圾/未初始化数据
        if not (-2 * np.pi < read_data[2] < 2 * np.pi):
            raise RuntimeError('里程计角度超范围 (read_data[2]=%s)' % read_data[2])
        DataSheet.OdoX = read_data[0]
        DataSheet.OdoY = read_data[1]
        DataSheet.OdoAng = read_data[2]
        DataSheet.VehicleCenterPt = [read_data[1], -read_data[0],
                                     read_data[2] / np.pi * 180]
        return 1

    return 1 if _retry('车辆状态', _do) is not None else 0

""" PointCloudData_st_Output
import lauterbach.trace32.rcl as t32
import struct
dbg = t32.connect()
0 0 8 uint64 PointTimestamp_u64; /*ns */
1 8 2 sint16 PointX_s16; /*mm */
2 10 2 sint16 PointY_s16;
3 12 2 sint16 PointXError_s16;
4 14 2 sint16 PointYError_s16;
5 16 2 sint16 PointSpeedX_s16;
6 18 2 sint16 PointSpeedY_s16;
7 20 2 sint16 PointSpeedXError_s16;
8 22 2 sint16 PointSpeedYError_s16;
9 24 2 sint16 PointRelatedObjectID_u16;
10 26 1 uint8 PointSensorRxMask_u8;
11 27 1 uint8 PointSensorTxMask_u8;
12 28 4 uint8 PointExistProbability_u8;
13 32 4 Type_Enum_HeightLevel PointHeight_en;
14 36 4 uint8 PointHeightProbability_u8;
15 40 4 Type_Enum_LocationState PointLocationState_en;
16 44 4 Type_Enum_DetectionState PointDetectionState_en;
"""

# d_UssTri_Baselink_Obj POINT_CLOUD_NUM = 20
def read_PtData():
    global PtNum
    PtNum = 0
    for index in range(POINT_CLOUD_NUM):
        Ptype[index] = 0
        PtTime[index] = 0
        PtRxMask[index] = 0
        PtTxMask[index] = 0
        Ptx[index] = POINT_X_Y_DEFAULT
        Pty[index] = POINT_X_Y_DEFAULT
        Pth[index] = POINT_HEIGHT_DEFAULT

    format_str = '<' + ('HhhBBBB' ) * POINT_CLOUD_NUM
    read_data = _read_symbol('点云', 'sf_Upper_PointOutSignal',
                             10 * POINT_CLOUD_NUM, format_str)
    if read_data is None:
        return 0, 0
    DataSheet.PtNum = 0

    char_num_point_temp = int((len(format_str) - 1) / POINT_CLOUD_NUM)
    for index in range(POINT_CLOUD_NUM):
        Ptype[index] = 0
        if (read_data[index*char_num_point_temp + 1] != 0 and read_data[index*char_num_point_temp + 2] != 0):
            PtTime[index] = 0 # int(read_data[index * char_num_point_temp +14])
            Ptx[index] = int(read_data[index * char_num_point_temp + 1])
            Pty[index] = int(read_data[index * char_num_point_temp + 2])
            Pth[index] = int(read_data[index * char_num_point_temp + 3])
            PtTxMask[index] = int(read_data[index * char_num_point_temp + 4])
            PtRxMask[index] = int(read_data[index * char_num_point_temp + 5])
            DataSheet.PtNum += 1
            Ptype[index] = 1
        else:
            continue
    return 1, read_data


def read_PtLineData():
    global PtLineNum
    PtLineNum = 0
    for index in range(POINT_LINE_NUM):
        PtLinetype[index] = 0
        PtLinex1[index] = POINT_X_Y_DEFAULT
        PtLiney1[index] = POINT_X_Y_DEFAULT
        PtLinex2[index] = POINT_X_Y_DEFAULT
        PtLiney2[index] = POINT_X_Y_DEFAULT
        PtLineh[index] = POINT_HEIGHT_DEFAULT
        PtLineObjType[index] = 0
        PtLineDist[index] = 0

    format_str = '<' + ('BBBBhhhhH') * POINT_LINE_NUM
    read_data = _read_symbol('线段障碍物', 'sf_Upper_LineOutSignal',
                             14 * POINT_LINE_NUM, format_str)  # 14 * POINT_LINE_NUM 字节
    if read_data is None:
        return 0, 0
    DataSheet.PtLineNum = 0

    char_num_line_temp = int((len(format_str) - 1) / POINT_LINE_NUM)
    # if main.logging_flag:
    #     main.logging_data(list(read_data),DATA_TYPE_POINT_LINE_RAW,int(time.time()*1000))

    for index in range(POINT_LINE_NUM):
        PtLinetype[index] = 0
        if read_data[index*char_num_line_temp+4] != 0 and read_data[index*char_num_line_temp+5] != 0 and read_data[index*char_num_line_temp+6] != 0 and read_data[index*char_num_line_temp+7] != 0:
            PtLinex1[index] = (read_data[index*char_num_line_temp+4])
            PtLiney1[index] = (read_data[index*char_num_line_temp+5])
            PtLinex2[index] = (read_data[index*char_num_line_temp+6])
            PtLiney2[index] = (read_data[index*char_num_line_temp+7])
            PtLineh[index] = int(read_data[index*char_num_line_temp+1])
            PtLineObjType[index] = int(read_data[index*char_num_line_temp+2])
            PtLineDist[index] = int(read_data[index*char_num_line_temp+8])
            DataSheet.PtLineNum += 1
            PtLinetype[index] = 1
        else:
            continue
    return 1,read_data

def read_echoData():
    """读取 sf_Upper_RawDataOutSignal 并存入 DataSheet.raw_data【含同频标志】。

    新结构体246字节，默认 2 字节对齐：
        uint16_t samefreq_front_Cnt;        // offset 0
        uint16_t samefreq_rear_Cnt;         // offset 2
        uint8_t  samefreq_front_Flag;       // offset 4 <1 前同频小灯亮>
        uint8_t  samefreq_rear_Flag;        // offset 5 <1 后同频小灯亮>
        Upper_RawDataOutSignalInfo rawdata_info[12]; // offset 6..245
        // 每项 20 字节：uint8_t mode +1 padding + 9*uint16
        //  (de, de_peak, de_width, ce_left, ce_left_peak, ce_left_width,
        //   ce_right, ce_right_peak, ce_right_width)

    同频标志存入 DataSheet.RawSameFreqFront* / RawSameFreqRear*
    每探头 10 元组存入 DataSheet.raw_data[i]（与旧格式一致）。
    """
    read_data = _read_symbol("回波数据", 'sf_Upper_RawDataOutSignal', 246,
                             '<' + 'HHBB' + 'BxHHHHHHHHH' * 12)
    if read_data is None:
        return 0

    # 头部 4 个解包值: samefreq_front_Cnt, samefreq_rear_Cnt,
    #                   samefreq_front_Flag, samefreq_rear_Flag
    DataSheet.RawSameFreqFrontCnt = int(read_data[0])
    DataSheet.RawSameFreqRearCnt = int(read_data[1])
    DataSheet.RawSameFreqFrontFlag = int(read_data[2])
    DataSheet.RawSameFreqRearFlag = int(read_data[3])

    # 每 10 个解包值为一组 (`x` 只跳过 padding 不产生输出值):
    #   idx+0: mode, idx+1: de, idx+2: de_peak, idx+3: de_width,
    #   idx+4: ce_left, idx+5: ce_left_peak, idx+6: ce_left_width,
    #   idx+7: ce_right, idx+8: ce_right_peak, idx+9: ce_right_width
    for i in range(12):
        idx = 4 + i * 10
        DataSheet.raw_data[i] = (
            read_data[idx + 0],      # mode
            read_data[idx + 1],      # de
            read_data[idx + 2],      # de_peak
            read_data[idx + 3],      # de_width
            read_data[idx + 4],      # ce_left
            read_data[idx + 5],      # ce_left_peak
            read_data[idx + 6],      # ce_left_width
            read_data[idx + 7],      # ce_right
            read_data[idx + 8],      # ce_right_peak
            read_data[idx + 9],      # ce_right_width
        )
    return 1
