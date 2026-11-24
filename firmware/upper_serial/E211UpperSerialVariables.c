/* E211 counted native exports -> transport-independent USSV v1.
 * Build with UPPER_SERIAL_E211, using the E211 Lauterbach_Var.h. */
#include "Lauterbach_Var.h"
#include "UpperSerialDebug.h"
#include <stddef.h>
#include <string.h>
#if defined(UPPER_SERIAL_E211) && defined(XCP_UPPER_DEBUG)
extern Upper_StatusOutSignal sf_Upper_StatusOutSignal;
extern Upper_OdoOutSignal sf_Upper_OdoOutSignal;
extern Upper_VehicleOutSignal sf_Upper_VehicleOutSignal;
extern Upper_RawDataOutSignal sf_Upper_RawDataOutSignal;
extern Upper_PDCOutSignal sf_Upper_PDCOutSignal;
extern Upper_PointOutSignal sf_Upper_PointOutSignal;
extern Upper_LineOutSignal sf_Upper_LineOutSignal;
int UpperSerialDebug_SendVariables(void)
{
    static UpperSerialFrame frame;
    int16_t mounts[24];
    unsigned int i;
    if (!UpperSerialDebug_HasWriter()) return UPPER_SERIAL_ERR_NO_WRITER;
    memset(&frame, 0, sizeof(frame));
    frame.status.gear = sf_Upper_StatusOutSignal.GearLever;
    frame.status.temperature = (uint16_t)(((int16_t)sf_Upper_StatusOutSignal.Temp + 40) * 2);
    frame.status.speed = sf_Upper_StatusOutSignal.Speed;
    frame.status.timestamp = sf_Upper_StatusOutSignal.TimeStamp;
    frame.odo.x = sf_Upper_OdoOutSignal.odo_y / 1000.0f;
    frame.odo.y = -sf_Upper_OdoOutSignal.odo_x / 1000.0f;
    frame.odo.angle = sf_Upper_OdoOutSignal.odo_ang;
    frame.vehicle.length = sf_Upper_VehicleOutSignal.CarLength;
    frame.vehicle.width = sf_Upper_VehicleOutSignal.CarWidth;
    memcpy(mounts, (const uint8_t *)&sf_Upper_VehicleOutSignal + offsetof(Upper_VehicleOutSignal, SnsPosRRS_X), sizeof(mounts));
    for (i = 0; i < 12; ++i) {
        const Upper_RawDataOutSignalInfo *raw = &sf_Upper_RawDataOutSignal.rawdata_info[i];
        UpperSerialRaw *dst = &frame.raw[i];
        frame.vehicle.sensor_xy[i * 2] = mounts[i * 2 + 1];
        frame.vehicle.sensor_xy[i * 2 + 1] = -mounts[i * 2];
        dst->mode = raw->mode;
        dst->de = raw->de; dst->de_peak = raw->de_peak; dst->de_width = raw->de_width;
        dst->ce_left = raw->ce_left; dst->ce_left_peak = raw->ce_left_peak; dst->ce_left_width = raw->ce_left_width;
        dst->ce_right = raw->ce_right; dst->ce_right_peak = raw->ce_right_peak; dst->ce_right_width = raw->ce_right_width;
        frame.pdc[i].distance = sf_Upper_PDCOutSignal.snspdc_info[i].dis;
        frame.pdc[i].range = sf_Upper_PDCOutSignal.snspdc_info[i].range;
        frame.pdc[i].fault = sf_Upper_PDCOutSignal.snspdc_info[i].fault;
    }
    frame.same_frequency_front_count = sf_Upper_RawDataOutSignal.samefreq_front_Cnt;
    frame.same_frequency_rear_count = sf_Upper_RawDataOutSignal.samefreq_rear_Cnt;
    frame.same_frequency_front_flag = sf_Upper_RawDataOutSignal.samefreq_front_Flag;
    frame.same_frequency_rear_flag = sf_Upper_RawDataOutSignal.samefreq_rear_Flag;
    frame.pdc_status = sf_Upper_PDCOutSignal.pdc_sts;
    frame.pdc_front_status = sf_Upper_PDCOutSignal.front_sts;
    frame.pdc_rear_status = sf_Upper_PDCOutSignal.rear_sts;
    frame.pdc_function_present = 1;
    frame.pdc_state = sf_Upper_PDCOutSignal.eState;
    frame.pdc_request_avm = sf_Upper_PDCOutSignal.pdcRequestAvm;
    frame.front_stop_request = sf_Upper_PDCOutSignal.frontStopReq;
    frame.rear_stop_request = sf_Upper_PDCOutSignal.rearStopReq;
    frame.front_min_distance = sf_Upper_PDCOutSignal.frontMinDst;
    frame.rear_min_distance = sf_Upper_PDCOutSignal.rearMinDst;
    frame.pdc_sensor_fault = sf_Upper_PDCOutSignal.SnsrFltOfPrkgDstCtrl;
    frame.pdc_mute = sf_Upper_PDCOutSignal.PdcMuteBtnSts;
    frame.point_count = sf_Upper_PointOutSignal.point_count;
    frame.line_count = sf_Upper_LineOutSignal.line_count;
    if (frame.point_count > UPPER_SERIAL_POINT_MAX || frame.line_count > UPPER_SERIAL_LINE_MAX)
        return UPPER_SERIAL_ERR_ARGUMENT;
    for (i = 0; i < frame.point_count; ++i) {
        const Upper_PointOutSignalInfo *src = &sf_Upper_PointOutSignal.point_info[i];
        frame.points[i].object_id = src->ObjID;
        frame.points[i].x = src->x; frame.points[i].y = src->y;
        frame.points[i].height = src->cHight;
        frame.points[i].tx_index = src->SNS_Txindex; frame.points[i].rx_index = src->SNS_Rxindex;
    }
    for (i = 0; i < frame.line_count; ++i) {
        const Upper_LineOutSignalInfo *src = &sf_Upper_LineOutSignal.line_info[i];
        frame.lines[i].number = src->cNum; frame.lines[i].height = src->cHight;
        frame.lines[i].object_type = src->cObjType;
        frame.lines[i].start_x = src->wStartx; frame.lines[i].start_y = src->wStarty;
        frame.lines[i].end_x = src->wEndx; frame.lines[i].end_y = src->wEndy;
        frame.lines[i].distance = src->wDist;
    }
    frame.slot_side_capacity = 3; /* E211 has no slot output. */
    return UpperSerialDebug_SendFrame(&frame);
}
#endif
