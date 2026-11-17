#include "Lauterbach_Var.h"
#include "UpperSerialDebug.h"
#include <string.h>

#ifdef LAUTERBACH_UPPER_DEBUG
/* Native Lauterbach_Var.h versions may declare only their OutputSignalRead_*
 * functions. These compatible externs allow retaining that MCU header. */
extern Upper_PointOutSignal sf_Upper_PointOutSignal[80];
extern Upper_LineOutSignal sf_Upper_LineOutSignal[20];
extern Upper_StatusOutSignal sf_Upper_StatusOutSignal;
extern Upper_OdoOutSignal sf_Upper_OdoOutSignal;
extern Upper_VehicleOutSignal sf_Upper_VehicleOutSignal;
extern Upper_RawDataOutSignal sf_Upper_RawDataOutSignal;
extern Upper_PDCOutSignal sf_Upper_PDCOutSignal;
extern Upper_SlotOutSignal sf_Upper_SlotOutSignal;
int UpperSerialDebug_SendVariables(void)
{
    static UpperSerialFrame frame;
    unsigned int i;
    const Upper_VehicleOutSignal *vehicle = &sf_Upper_VehicleOutSignal;
    if (!UpperSerialDebug_HasWriter()) return UPPER_SERIAL_ERR_NO_WRITER;
    memset(&frame, 0, sizeof(frame));
    frame.status.gear = sf_Upper_StatusOutSignal.GearLever;
    frame.status.temperature = sf_Upper_StatusOutSignal.Temp;
    frame.status.speed = sf_Upper_StatusOutSignal.Speed;
    frame.status.timestamp = sf_Upper_StatusOutSignal.TimeStamp;
    frame.odo.x = sf_Upper_OdoOutSignal.odo_x;
    frame.odo.y = sf_Upper_OdoOutSignal.odo_y;
    frame.odo.angle = sf_Upper_OdoOutSignal.odo_ang;
    frame.vehicle.length = vehicle->CarLength;
    frame.vehicle.width = vehicle->CarWidth;
    frame.vehicle.sensor_xy[0] = vehicle->SnsPosRRS_X;
    frame.vehicle.sensor_xy[1] = vehicle->SnsPosRRS_Y;
    frame.vehicle.sensor_xy[2] = vehicle->SnsPosRRC_X;
    frame.vehicle.sensor_xy[3] = vehicle->SnsPosRRC_Y;
    frame.vehicle.sensor_xy[4] = vehicle->SnsPosRRM_X;
    frame.vehicle.sensor_xy[5] = vehicle->SnsPosRRM_Y;
    frame.vehicle.sensor_xy[6] = vehicle->SnsPosRLM_X;
    frame.vehicle.sensor_xy[7] = vehicle->SnsPosRLM_Y;
    frame.vehicle.sensor_xy[8] = vehicle->SnsPosRLC_X;
    frame.vehicle.sensor_xy[9] = vehicle->SnsPosRLC_Y;
    frame.vehicle.sensor_xy[10] = vehicle->SnsPosRLS_X;
    frame.vehicle.sensor_xy[11] = vehicle->SnsPosRLS_Y;
    frame.vehicle.sensor_xy[12] = vehicle->SnsPosFRS_X;
    frame.vehicle.sensor_xy[13] = vehicle->SnsPosFRS_Y;
    frame.vehicle.sensor_xy[14] = vehicle->SnsPosFRC_X;
    frame.vehicle.sensor_xy[15] = vehicle->SnsPosFRC_Y;
    frame.vehicle.sensor_xy[16] = vehicle->SnsPosFRM_X;
    frame.vehicle.sensor_xy[17] = vehicle->SnsPosFRM_Y;
    frame.vehicle.sensor_xy[18] = vehicle->SnsPosFLM_X;
    frame.vehicle.sensor_xy[19] = vehicle->SnsPosFLM_Y;
    frame.vehicle.sensor_xy[20] = vehicle->SnsPosFLC_X;
    frame.vehicle.sensor_xy[21] = vehicle->SnsPosFLC_Y;
    frame.vehicle.sensor_xy[22] = vehicle->SnsPosFLS_X;
    frame.vehicle.sensor_xy[23] = vehicle->SnsPosFLS_Y;
    frame.same_frequency_front_count = sf_Upper_RawDataOutSignal.samefreq_front_Cnt;
    frame.same_frequency_rear_count = sf_Upper_RawDataOutSignal.samefreq_rear_Cnt;
    frame.same_frequency_front_flag = sf_Upper_RawDataOutSignal.samefreq_front_Flag;
    frame.same_frequency_rear_flag = sf_Upper_RawDataOutSignal.samefreq_rear_Flag;
    frame.pdc_status = sf_Upper_PDCOutSignal.pdc_sts;
    frame.pdc_front_status = sf_Upper_PDCOutSignal.front_sts;
    frame.pdc_rear_status = sf_Upper_PDCOutSignal.rear_sts;
    for (i = 0; i < 12; ++i) {
        const Upper_RawDataOutSignalInfo *raw = &sf_Upper_RawDataOutSignal.rawdata_info[i];
        UpperSerialRaw *dst = &frame.raw[i];
        dst->mode = raw->mode;
        dst->de = raw->de;
        dst->de_peak = raw->de_peak;
        dst->de_width = raw->de_width;
        dst->ce_left = raw->ce_left;
        dst->ce_left_peak = raw->ce_left_peak;
        dst->ce_left_width = raw->ce_left_width;
        dst->ce_right = raw->ce_right;
        dst->ce_right_peak = raw->ce_right_peak;
        dst->ce_right_width = raw->ce_right_width;
        frame.pdc[i].distance = sf_Upper_PDCOutSignal.snspdc_info[i].dis;
        frame.pdc[i].range = sf_Upper_PDCOutSignal.snspdc_info[i].range;
        frame.pdc[i].fault = sf_Upper_PDCOutSignal.snspdc_info[i].fault;
    }
    frame.point_count = 80;
    frame.line_count = 20;
    for (i = 0; i < 80; ++i) {
        const Upper_PointOutSignal *point = &sf_Upper_PointOutSignal[i];
        frame.points[i].object_id = point->ObjID;
        frame.points[i].x = point->x;
        frame.points[i].y = point->y;
        frame.points[i].height = point->cHight;
        frame.points[i].tx_index = point->SNS_Txindex;
        frame.points[i].rx_index = point->SNS_Rxindex;
    }
    for (i = 0; i < 20; ++i) {
        const Upper_LineOutSignal *line = &sf_Upper_LineOutSignal[i];
        frame.lines[i].number = line->cNum;
        frame.lines[i].height = line->cHight;
        frame.lines[i].object_type = line->cObjType;
        frame.lines[i].direction = line->cDirect;
        frame.lines[i].start_x = line->wStartx;
        frame.lines[i].start_y = line->wStarty;
        frame.lines[i].end_x = line->wEndx;
        frame.lines[i].end_y = line->wEndy;
        frame.lines[i].distance = line->wDist;
    }
    frame.slot_status = sf_Upper_SlotOutSignal.slot_sts;
    frame.slot_left_count = sf_Upper_SlotOutSignal.left_slot_num;
    frame.slot_right_count = sf_Upper_SlotOutSignal.right_slot_num;
    frame.slot_side_capacity = 3;
    for (i = 0; i < 6; ++i) {
        const Upper_SlotOutSignalInfo *slot = i < 3 ?
            &sf_Upper_SlotOutSignal.left_slot_info[i] :
            &sf_Upper_SlotOutSignal.right_slot_info[i-3];
        UpperSerialSlot *dst = &frame.slots[i];
        dst->timestamp = slot->timestamp;
        dst->id = slot->slot_id;
        dst->type = slot->slot_type;
        dst->width = slot->slot_width;
        dst->depth = slot->slot_Depth;
        dst->point_xy[0] = slot->slot_A_x;
        dst->point_xy[1] = slot->slot_A_y;
        dst->point_xy[2] = slot->slot_B_x;
        dst->point_xy[3] = slot->slot_B_y;
        dst->point_xy[4] = slot->slot_C_x;
        dst->point_xy[5] = slot->slot_C_y;
        dst->point_xy[6] = slot->slot_D_x;
        dst->point_xy[7] = slot->slot_D_y;
        dst->point_xy[8] = slot->slot_E_x;
        dst->point_xy[9] = slot->slot_E_y;
        dst->point_xy[10] = slot->slot_F_x;
        dst->point_xy[11] = slot->slot_F_y;
        dst->point_a_type = slot->slot_A_type;
        dst->point_f_type = slot->slot_F_type;
    }
    return UpperSerialDebug_SendFrame(&frame);
}
#endif
