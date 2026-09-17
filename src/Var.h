typedef struct
{
    uint16_t ObjID;
    int16_t x;
    int16_t y;
    uint8_t cHight;
    uint8_t SNS_Txindex;
    uint8_t SNS_Rxindex;
} Upper_PointOutSignal;

typedef struct
{
    uint8_t cNum;
    uint8_t cHight;
    uint8_t cObjType;
    int16_t wStartx;
    int16_t wStarty;
    int16_t wEndx;
    int16_t wEndy;
    uint16_t wDist;
} Upper_LineOutSignal;

typedef struct
{
    uint8_t GearLever;
    uint16_t Temp;
    float Speed;
    uint64_t TimeStamp;
} Upper_StatusOutSignal;

typedef struct
{
    float odo_x;
    float odo_y;
    float odo_ang;
} Upper_OdoOutSignal;

typedef struct
{
    uint16_t CarLength;
    uint16_t CarWidth;

    int16_t SnsPosRRS_X;
    int16_t SnsPosRRS_Y;

    int16_t SnsPosRRC_X;
    int16_t SnsPosRRC_Y;

    int16_t SnsPosRRM_X;
    int16_t SnsPosRRM_Y;

    int16_t SnsPosRLM_X;
    int16_t SnsPosRLM_Y;

    int16_t SnsPosRLC_X;
    int16_t SnsPosRLC_Y;

    int16_t SnsPosRLS_X;
    int16_t SnsPosRLS_Y;

    int16_t SnsPosFRS_X;
    int16_t SnsPosFRS_Y;

    int16_t SnsPosFRC_X;
    int16_t SnsPosFRC_Y;

    int16_t SnsPosFRM_X;
    int16_t SnsPosFRM_Y;

    int16_t SnsPosFLM_X;
    int16_t SnsPosFLM_Y;

    int16_t SnsPosFLC_X;
    int16_t SnsPosFLC_Y;

    int16_t SnsPosFLS_X;
    int16_t SnsPosFLS_Y;
} Upper_VehicleOutSignal;

typedef struct
{
    uint8_t mode;

    uint16_t de;
    uint16_t de_peak;
    uint16_t de_width;

    uint16_t ce_left;
    uint16_t ce_left_peak;
    uint16_t ce_left_width;

    uint16_t ce_right;
    uint16_t ce_right_peak;
    uint16_t ce_right_width;
} Upper_RawDataOutSignalInfo;

typedef struct
{
    uint16_t samefreq_front_Cnt;
    uint16_t samefreq_rear_Cnt;
    uint8_t samefreq_front_Flag;
    uint8_t samefreq_rear_Flag;
    Upper_RawDataOutSignalInfo rawdata_info[12];
} Upper_RawDataOutSignal;

typedef struct
{
    uint16_t dis;
    uint8_t range;
    uint8_t fault;
} Upper_PDCOutSignalInfo;

typedef struct
{
    uint8_t pdc_sts;
    uint8_t front_sts;
    uint8_t rear_sts;
    Upper_PDCOutSignalInfo snspdc_info[12];
} Upper_PDCOutSignal;

typedef struct
{
    uint64_t timestamp;

    uint8_t slot_id;
    uint8_t slot_type;
    uint16_t slot_width;
    uint16_t slot_Depth;

    int16_t slot_A_x;
    int16_t slot_A_y;
    uint8_t slot_A_type;

    int16_t slot_B_x;
    int16_t slot_B_y;

    int16_t slot_C_x;
    int16_t slot_C_y;

    int16_t slot_D_x;
    int16_t slot_D_y;

    int16_t slot_E_x;
    int16_t slot_E_y;

    int16_t slot_F_x;
    int16_t slot_F_y;
    uint8_t slot_F_type;
} Upper_SlotOutSignalInfo;

typedef struct
{
    uint8_t slot_sts;
    uint8_t left_slot_num;
    uint8_t right_slot_num;
    Upper_SlotOutSignalInfo left_slot_info[3];
    Upper_SlotOutSignalInfo right_slot_info[3];
} Upper_SlotOutSignal;

Upper_PointOutSignal sf_Upper_PointOutSignal[80] = {0};
Upper_LineOutSignal sf_Upper_LineOutSignal[20] = {0};
Upper_StatusOutSignal sf_Upper_StatusOutSignal = {0};
Upper_OdoOutSignal sf_Upper_OdoOutSignal = {0};
Upper_VehicleOutSignal sf_Upper_VehicleOutSignal = {0};
Upper_RawDataOutSignal sf_Upper_RawDataOutSignal = {0};
Upper_PDCOutSignal sf_Upper_PDCOutSignal = {0};
Upper_SlotOutSignal sf_Upper_SlotOutSignal = {0};

