POINT_CLOUD_NUM = 80#12#20
POINT_LINE_NUM = 20
POINT_SLOT_NUM = 8

POINT_CLOUD_LOW = 0
POINT_CLOUD_HEIGHT = 1

POINT_LINE_LOW = 0
POINT_LINE_HEIGHT = 1

GEAR_STR_LIST = ['P', 'R', 'N', 'D']
POINT_X_Y_DEFAULT = 0
POINT_HEIGHT_DEFAULT = 0

SLOT_TYPE_STR_LIST = ("无","水平","垂直","斜线")
SNS_STR_LIST = ('RRS', 'RRC', 'RRM', 'RLM', 'RLC', 'RLS', 'FRS', 'FRC', 'FRM', 'FLM', 'FLC', 'FLS')
HEIGHT_BREAK_STR_LIST = ('无','未知','低','高')

DATA_TYPE_POINT_CLOUD_X = 1
DATA_TYPE_POINT_CLOUD_Y = 2
DATA_TYPE_POINT_CLOUD_H = 3
DATA_TYPE_POINT_CLOUD_T = 4
DATA_TYPE_POINT_LINE_X1 = 5
DATA_TYPE_POINT_LINE_X2 = 6
DATA_TYPE_POINT_LINE_Y1 = 7
DATA_TYPE_POINT_LINE_Y2 = 8
DATA_TYPE_POINT_LINE_H = 9
DATA_TYPE_POINT_LINE_T  = 10
DATA_TYPE_ECHO_DE      = 11
DATA_TYPE_ECHO_CE_LEFT = 12
DATA_TYPE_ECHO_CE_RIGHT = 13
DATA_TYPE_POINT_CLOUD_TIME = 14
DATA_TYPE_POINT_CLOUD_TX_MASK = 15
DATA_TYPE_POINT_CLOUD_RX_MASK = 16
DATA_TYPE_VEHICLE_INFO = 17
DATA_TYPE_SLOT_X1 = 18
DATA_TYPE_SLOT_Y1 = 19
DATA_TYPE_SLOT_X2 = 20
DATA_TYPE_SLOT_Y2 = 21
DATA_TYPE_SLOT_X3 = 22
DATA_TYPE_SLOT_Y3 = 23
DATA_TYPE_SLOT_X4 = 24
DATA_TYPE_SLOT_Y4 = 25
DATA_TYPE_SLOT_LENGTH = 26
DATA_TYPE_SLOT_DEPTH = 27
DATA_TYPE_SLOT_TYPE = 28
DATA_TYPE_POINT_CLOUD_RAW = 29
DATA_TYPE_POINT_LINE_RAW = 30
DATA_TYPE_SLOT_RAW = 31

VehicleGear = 0
VehicleSpeed = 0.0        # 车速 km/h（sf_Upper_StatusOutSignal.Speed，浮点型）
VehicleTemp = 0           # sf_Upper_StatusOutSignal.Temp（在线读取，温度）
VehicleTimeStamp = 0      # sf_Upper_StatusOutSignal.TimeStamp（在线读取，时间戳）
VehicleCenterPt = [0.0,0.0,0.0]

# sf_Upper_OdoOutSignal 原始里程计数数据（在线读取）
OdoX = 0.0                # odo_x
OdoY = 0.0                # odo_y
OdoAng = 0.0              # odo_ang（rad）


# sf_Upper_VehicleOutSignal 车身参数（在线读取）
VehicleLength = 0         # 车长 mm
VehicleWidth = 0          # 车宽 mm
# 12 个探头位置 (x, y)，顺序同 SNS_STR_LIST: RRS,RRC,RRM,RLM,RLC,RLS,FRS,FRC,FRM,FLM,FLC,FLS
# 约定与旧 log 头部一致：x=横向(+右), y=纵向(+前)（转 demo 时 wx=y, wy=-x）
VehicleProbePos = [(0, 0)] * 12

PtTime = [0] * POINT_CLOUD_NUM
PtTxMask = [0] * POINT_CLOUD_NUM
PtRxMask = [0] * POINT_CLOUD_NUM
Ptx = [0] * POINT_CLOUD_NUM
Pty = [0] * POINT_CLOUD_NUM
Pth = [0] * POINT_CLOUD_NUM
Ptype = [0] * POINT_CLOUD_NUM
PtNum = 0

PtLinex1 = [0] * POINT_LINE_NUM
PtLinex2 = [0] * POINT_LINE_NUM
PtLiney1 = [0] * POINT_LINE_NUM
PtLiney2 = [0] * POINT_LINE_NUM
PtLineh = [0] * POINT_LINE_NUM
PtLinetype = [0] * POINT_LINE_NUM
PtLineObjType = [0] * POINT_LINE_NUM  # cObjType（结构体全字段显示）
PtLineDist = [0] * POINT_LINE_NUM     # wDist
PtLineNum = 0

Slotx1 = [0] * POINT_SLOT_NUM
Sloty1 = [0] * POINT_SLOT_NUM
Slotx2 = [0] * POINT_SLOT_NUM
Sloty2 = [0] * POINT_SLOT_NUM
Slotx3 = [0] * POINT_SLOT_NUM
Sloty3 = [0] * POINT_SLOT_NUM
Slotx4 = [0] * POINT_SLOT_NUM
Sloty4 = [0] * POINT_SLOT_NUM
SlotLength = [0] * POINT_SLOT_NUM
SlotDepth = [0] * POINT_SLOT_NUM
SlotType = [0] * POINT_SLOT_NUM
SlotNum = 0

# sf_Upper_SlotOutSignal 车位信号（在线读取）
# 6 个槽位：前 3 个为 left_slot_info[0..2]，后 3 个
SlotOutNum = 0              # 车位总数（left_slot_
SlotOutLeftNum = 0          # left_slot_num: 左侧车
SlotOutRightNum = 0         # right_slot_num: 右侧
SlotOutSts = 0              # slot_sts: 车位状态
SlotOutId = [0] * 6         # 槽位 ID
SlotOutType = [0] * 6       # 槽位类型（1=水平 2=垂
SlotOutWidth = [0] * 6      # 车位宽度 mm
SlotOutDepth = [0] * 6      # 车位深度 mm
# A..F 六点坐标（main 坐标系：X=+前，Y=+右）
SlotOutAx = [0] * 6
SlotOutAy = [0] * 6
SlotOutBx = [0] * 6
SlotOutBy = [0] * 6
SlotOutCx = [0] * 6
SlotOutCy = [0] * 6
SlotOutDx = [0] * 6
SlotOutDy = [0] * 6
SlotOutEx = [0] * 6
SlotOutEy = [0] * 6
SlotOutFx = [0] * 6
SlotOutFy = [0] * 6
SlotOutTime = [0] * 6      # 时间戳
SlotOutAType = [0] * 6     # A 点类型
SlotOutFType = [0] * 6     # F 点类型
SlotOutValid = [0] * 6     # 1=六点数据有效

de_echo_data = [0] * 180
ce_echo_data_left = [0] * 180
ce_echo_data_right = [0] * 180

# sf_Upper_RawDataOutSignal 头部同频标志（=1 时点亮车前/车后同频小灯）
RawSameFreqFrontCnt = 0   # 前向同频计数器（samefreq_front_Cnt）
RawSameFreqRearCnt = 0    # 后向同频计数器（samefreq_rear_Cnt）
RawSameFreqFrontFlag = 0  # 前向同频标志（samefreq_front_Flag，=1 前小灯亮）
RawSameFreqRearFlag = 0   # 后向同频标志（samefreq_rear_Flag，=1 后小灯亮）

# sf_Upper_RawDataOutSignal.rawdata_info[12]: 每探头一个元组
# (mode, de, de_peak, de_width, ce_left, ce_left_peak, ce_left_width,
#  ce_right, ce_right_peak, ce_right_width)
raw_data = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0) for _ in range(12)]

# sf_Upper_PDCOutSignal PDC 报警信号（在线读取）
PDC_Sts = 0        # PDC 系统状态
PDC_FrontSts = 0   # 前部状态
PDC_RearSts = 0    # 后部状态
# 下列数组顺序同 SNS_STR_LIST:
#   RRS, RRC, RRM, RLM, RLC, RLS, FRS, FRC, FRM, FLM, FLC, FLS
# （C 端结构体为 Upper_PDCOutSignalInfo snspdc_info[12]，
#  每项 {uint16_t dis; uint8_t range; uint8_t fault}, 数组顺序与 SNS_STR_LIST 一致，
#  上位机侧按同一顺序拆成 3 个数组，直写无需反转）
PDCDis = [0] * 12     # 最近障碍物距离
PDCRange = [0] * 12   # 障碍物距离区间
PDCFault = [0] * 12   # 传感器故障标志

# class PDC_WarningGroup:
#     def __init__(self, PDC_Sts, Distance_FLS, Distance_FLC, Distance_FLM, Distance_FRM, Distance_FRC, Distance_FRS, Distance_RLS, Distance_RLC, Distance_RLM, Distance_RRM, Distance_RRC, Distance_RRS
#     , Range_FLS, Range_FLC, Range_FLM, Range_FRM, Range_FRC, Range_FRS, Range_RLS, Range_RLC, Range_RLM, Range_RRM, Range_RRC, Range_RRS
#     , Fault_FLS, Fault_FLC, Fault_FLM, Fault_FRM, Fault_FRC, Fault_FRS, Fault_RLS, Fault_RLC, Fault_RLM, Fault_RRM, Fault_RRC, Fault_RRS):
#         self.PDC_Sts = PDC_Sts

