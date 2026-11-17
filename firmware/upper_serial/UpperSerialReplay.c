/* Replay-specific data acquisition. This is not part of the MCU UART driver. */
#include "UpperSerialReplay.h"
#if defined(LAUTERBACH_UPPER_DEBUG) && LAUTERBACH_UPPER_SERIAL_DEBUG
#include "UpperSerialDebug.h"
#include "Lauterbach_Var.h"
#include "SensorData.h"
#include "PDC_Track_If.h"
#include "APACommonPar.h"
#include "VehicleCommonPara_T60.h"
#include "PIT.h"
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

/* Optional PC-only binary capture, useful for protocol tests and UART replay. */
static FILE *s_capture_file;
static void close_capture(void)
{
    if (s_capture_file != NULL) {
        fclose(s_capture_file);
        s_capture_file = NULL;
    }
}

static int write_capture(const uint8_t *data, uint16_t size, void *context)
{
    FILE *file = (FILE *)context;
    return fwrite(data, 1, size, file) == size && fflush(file) == 0 ? 0 : -1;
}

static void configure_replay_writer(void)
{
    static int checked;
    const char *path;
    if (checked || UpperSerialDebug_HasWriter()) return;
    checked = 1;
    path = getenv("UPPER_SERIAL_OUTPUT");
    if (path == NULL || path[0] == '\0') return;
    s_capture_file = fopen(path, "wb");
    if (s_capture_file == NULL) {
        fprintf(stderr, "Cannot create UPPER_SERIAL_OUTPUT file: %s\n", path);
        return;
    }
    atexit(close_capture);
    UpperSerialDebug_SetWriter(write_capture, s_capture_file);
}

static int16_t saturate_s16(long value)
{
    return (int16_t)(value < INT16_MIN ? INT16_MIN : value > INT16_MAX ? INT16_MAX : value);
}

static void capture_replay(void)
{
    unsigned int i;
    Upper_VehicleOutSignal *vehicle = &sf_Upper_VehicleOutSignal;
    sf_Upper_StatusOutSignal.GearLever = VCU_GearLeverPos;
    sf_Upper_StatusOutSignal.Temp = VCU_AmbientTemp;
    sf_Upper_StatusOutSignal.Speed = VCU_VehicleSpeed_KM_H;
    sf_Upper_StatusOutSignal.TimeStamp = (uint64_t)R_GetTimeStamp_1ms_Cnt() * 1000u;
    /* Replay tracking pose: X=right/Y=forward, mm; wire: X=forward/Y=left, m. */
    sf_Upper_OdoOutSignal.odo_x = stTrackCurCarPos.Coordinate.y * 0.001f;
    sf_Upper_OdoOutSignal.odo_y = -stTrackCurCarPos.Coordinate.x * 0.001f;
    sf_Upper_OdoOutSignal.odo_ang = stTrackCurCarPos.CarAng;
    vehicle->CarLength = (uint16_t)kLengthOfCar;
    vehicle->CarWidth = (uint16_t)kWidthOfCar;
    vehicle->SnsPosRRS_X = (int16_t)kSnsPosRRS_Y;
    vehicle->SnsPosRRS_Y = saturate_s16(-(long)kSnsPosRRS_X);
    vehicle->SnsPosRRC_X = (int16_t)kSnsPosRRC_Y;
    vehicle->SnsPosRRC_Y = saturate_s16(-(long)kSnsPosRRC_X);
    vehicle->SnsPosRRM_X = (int16_t)kSnsPosRRM_Y;
    vehicle->SnsPosRRM_Y = saturate_s16(-(long)kSnsPosRRM_X);
    vehicle->SnsPosRLM_X = (int16_t)kSnsPosRLM_Y;
    vehicle->SnsPosRLM_Y = saturate_s16(-(long)kSnsPosRLM_X);
    vehicle->SnsPosRLC_X = (int16_t)kSnsPosRLC_Y;
    vehicle->SnsPosRLC_Y = saturate_s16(-(long)kSnsPosRLC_X);
    vehicle->SnsPosRLS_X = (int16_t)kSnsPosRLS_Y;
    vehicle->SnsPosRLS_Y = saturate_s16(-(long)kSnsPosRLS_X);
    vehicle->SnsPosFRS_X = (int16_t)kSnsPosFRS_Y;
    vehicle->SnsPosFRS_Y = saturate_s16(-(long)kSnsPosFRS_X);
    vehicle->SnsPosFRC_X = (int16_t)kSnsPosFRC_Y;
    vehicle->SnsPosFRC_Y = saturate_s16(-(long)kSnsPosFRC_X);
    vehicle->SnsPosFRM_X = (int16_t)kSnsPosFRM_Y;
    vehicle->SnsPosFRM_Y = saturate_s16(-(long)kSnsPosFRM_X);
    vehicle->SnsPosFLM_X = (int16_t)kSnsPosFLM_Y;
    vehicle->SnsPosFLM_Y = saturate_s16(-(long)kSnsPosFLM_X);
    vehicle->SnsPosFLC_X = (int16_t)kSnsPosFLC_Y;
    vehicle->SnsPosFLC_Y = saturate_s16(-(long)kSnsPosFLC_X);
    vehicle->SnsPosFLS_X = (int16_t)kSnsPosFLS_Y;
    vehicle->SnsPosFLS_Y = saturate_s16(-(long)kSnsPosFLS_X);
    sf_Upper_RawDataOutSignal.samefreq_front_Cnt = d_SameFreq_Front_Cnt;
    sf_Upper_RawDataOutSignal.samefreq_rear_Cnt = d_SameFreq_Rear_Cnt;
    sf_Upper_RawDataOutSignal.samefreq_front_Flag = Front_SameFreq_Flag;
    sf_Upper_RawDataOutSignal.samefreq_rear_Flag = Rear_SameFreq_Flag;
    for (i = 0; i < 12; ++i) {
        Upper_RawDataOutSignalInfo *raw = &sf_Upper_RawDataOutSignal.rawdata_info[i];
        raw->mode = USS_OriginalInfoGroup_data.USS_OriginalInfo[i].USS_WorkMode;
        raw->de = USS_OriginalInfo_DE_Std_Filt.USS_OriginalInfo[i].USS_ObjInfo[0].USS_ObjDis;
        raw->de_peak = USS_OriginalInfo_DE_Std_Filt.USS_OriginalInfo[i].USS_ObjInfo[0].USS_Obj14bitAmp;
        raw->de_width = USS_OriginalInfo_DE_Std_Filt.USS_OriginalInfo[i].USS_ObjInfo[0].USS_ObjWidth;
        raw->ce_left = raw->ce_left_peak = raw->ce_left_width = 0;
        raw->ce_right = raw->ce_right_peak = raw->ce_right_width = 0;
        /* Match OutputSignalRead_Rawdata in the MCU Lauterbach exporter. */
        if (i % 6 != 5) {
            raw->ce_left = USS_OriginalInfo_CE_Std_Filt[CE_From_RightSns].USS_OriginalInfo[i+1].USS_ObjInfo[0].USS_ObjDis;
            raw->ce_left_peak = USS_OriginalInfo_CE_Std_Filt[CE_From_RightSns].USS_OriginalInfo[i+1].USS_ObjInfo[0].USS_Obj14bitAmp;
            raw->ce_left_width = USS_OriginalInfo_CE_Std_Filt[CE_From_RightSns].USS_OriginalInfo[i+1].USS_ObjInfo[0].USS_ObjWidth;
        }
        if (i % 6 != 0) {
            raw->ce_right = USS_OriginalInfo_CE_Std_Filt[CE_From_LeftSns].USS_OriginalInfo[i-1].USS_ObjInfo[0].USS_ObjDis;
            raw->ce_right_peak = USS_OriginalInfo_CE_Std_Filt[CE_From_LeftSns].USS_OriginalInfo[i-1].USS_ObjInfo[0].USS_Obj14bitAmp;
            raw->ce_right_width = USS_OriginalInfo_CE_Std_Filt[CE_From_LeftSns].USS_OriginalInfo[i-1].USS_ObjInfo[0].USS_ObjWidth;
        }
    }
    for (i = 0; i < 80; ++i) {
        Upper_PointOutSignal *point = &sf_Upper_PointOutSignal[i];
        point->ObjID = stPointOut_Upper[i].ObjID;
        /* PointCloud StartPt and CAN line outputs are already forward/left. */
        point->x = stPointOut_Upper[i].x;
        point->y = stPointOut_Upper[i].y;
        point->cHight = stPointOut_Upper[i].cHight;
        point->SNS_Txindex = stPointOut_Upper[i].SNS_Txindex;
        point->SNS_Rxindex = stPointOut_Upper[i].SNS_Rxindex;
    }
    for (i = 0; i < 20; ++i) {
        Upper_LineOutSignal *line = &sf_Upper_LineOutSignal[i];
        line->cNum = stOneOutSi_Upper[i].cNum;
        line->cHight = stOneOutSi_Upper[i].cHight;
        line->cObjType = stOneOutSi_Upper[i].cObjType;
        line->cDirect = 0; /* This replay profile does not export direction. */
        line->wStartx = stOneOutSi_Upper[i].wStartx;
        line->wStarty = stOneOutSi_Upper[i].wStarty;
        line->wEndx = stOneOutSi_Upper[i].wEndx;
        line->wEndy = stOneOutSi_Upper[i].wEndy;
        line->wDist = 0; /* Not computed by the replay line exporter. */
    }
    /* PDC/slot algorithms are absent from this replay profile. Their mirrors
     * remain available for a firmware producer to fill; no values are invented. */
}

void UpperSerialReplay_AfterOutput(void)
{
    static uint64_t last_sent;
    static int have_sent;
    uint64_t now;
    int result;
    configure_replay_writer();
    if (!UpperSerialDebug_HasWriter()) return;
    now = (uint64_t)R_GetTimeStamp_1ms_Cnt() * 1000u;
    if (have_sent && now >= last_sent && now-last_sent < UPPER_SERIAL_PERIOD_US) return;
    capture_replay();
    result = UpperSerialDebug_SendVariables();
    if (result == UPPER_SERIAL_OK) {
        last_sent = now;
        have_sent = 1;
    }
}
#endif
