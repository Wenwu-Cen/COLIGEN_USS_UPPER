#include "UpperSerialDebug.h"
#include "Lauterbach_Var.h"
#include <stdio.h>
#include <string.h>

static UpperSerialFrame frame;
static unsigned int bytes_sent;
static int reject_frame(const uint8_t *data, uint16_t size, void *context)
{
    (void)data; (void)size; (void)context;
    return -1;
}
static int capture(const uint8_t *data, uint16_t size, void *context)
{
    FILE *file = (FILE *)context;
    if (UpperSerialDebug_SendFrame(&frame) != UPPER_SERIAL_ERR_BUSY) return -1;
    bytes_sent += size;
    return fwrite(data, 1, size, file) == size ? 0 : -1;
}
int main(int argc, char **argv)
{
    unsigned int i;
    FILE *file;
    if (argc != 2) return 2;
    if (UpperSerialDebug_Crc32((const uint8_t *)"123456789", 9) != 0xcbf43926u) return 3;
    frame.point_count = 80;
    frame.line_count = 20;
    frame.slot_side_capacity = 3;
    if (UpperSerialDebug_SendFrame(&frame) != UPPER_SERIAL_ERR_NO_WRITER) return 4;
    UpperSerialDebug_SetWriter(reject_frame, NULL);
    if (UpperSerialDebug_SendFrame(&frame) != UPPER_SERIAL_ERR_WRITE) return 5;
    frame.slot_left_count = 4;
    if (UpperSerialDebug_SendFrame(&frame) != UPPER_SERIAL_ERR_ARGUMENT) return 6;
    frame.slot_left_count = 0;
    file = fopen(argv[1], "wb");
    if (!file) return 7;
    sf_Upper_StatusOutSignal.GearLever = 2;
    sf_Upper_StatusOutSignal.Temp = 35;
    sf_Upper_StatusOutSignal.Speed = 12.5f;
    sf_Upper_StatusOutSignal.TimeStamp = 1234567890123ULL;
    sf_Upper_OdoOutSignal.odo_x = 1.5f;
    sf_Upper_OdoOutSignal.odo_y = -2.5f;
    sf_Upper_OdoOutSignal.odo_ang = .25f;
    sf_Upper_VehicleOutSignal.CarLength = 5000;
    sf_Upper_VehicleOutSignal.CarWidth = 2000;
    sf_Upper_VehicleOutSignal.SnsPosFLS_X = 3900;
    sf_Upper_VehicleOutSignal.SnsPosFLS_Y = 850;
    for (i = 0; i < 80; ++i) {
        sf_Upper_PointOutSignal[i].ObjID = (uint16_t)(1000+i);
        sf_Upper_PointOutSignal[i].x = (int16_t)(100+i);
        sf_Upper_PointOutSignal[i].y = -(int16_t)(200+i);
        sf_Upper_PointOutSignal[i].cHight = i%3;
        sf_Upper_PointOutSignal[i].SNS_Txindex = 3;
        sf_Upper_PointOutSignal[i].SNS_Rxindex = 4;
    }
    for (i = 0; i < 20; ++i) {
        sf_Upper_LineOutSignal[i].cNum = (uint8_t)(10+i);
        sf_Upper_LineOutSignal[i].wStartx = 100;
        sf_Upper_LineOutSignal[i].wStarty = -200;
        sf_Upper_LineOutSignal[i].wEndx = 300;
        sf_Upper_LineOutSignal[i].wEndy = -400;
        sf_Upper_LineOutSignal[i].wDist = 500;
    }
    for (i = 0; i < 12; ++i) {
        sf_Upper_RawDataOutSignal.rawdata_info[i].de = (uint16_t)(321+i);
        sf_Upper_RawDataOutSignal.rawdata_info[i].de_width = (uint16_t)(50+i);
        sf_Upper_PDCOutSignal.snspdc_info[i].dis = (uint16_t)(100+i);
        sf_Upper_PDCOutSignal.snspdc_info[i].range = 2;
    }
    sf_Upper_PDCOutSignal.pdc_sts = 1;
    sf_Upper_PDCOutSignal.front_sts = 1;
    sf_Upper_PDCOutSignal.rear_sts = 1;
    sf_Upper_SlotOutSignal.slot_sts = 1;
    sf_Upper_SlotOutSignal.left_slot_num = 1;
    sf_Upper_SlotOutSignal.left_slot_info[0].timestamp = 99999;
    sf_Upper_SlotOutSignal.left_slot_info[0].slot_id = 7;
    sf_Upper_SlotOutSignal.left_slot_info[0].slot_A_x = 100;
    sf_Upper_SlotOutSignal.left_slot_info[0].slot_A_y = 200;
    sf_Upper_SlotOutSignal.left_slot_info[0].slot_A_type = 1;
    sf_Upper_SlotOutSignal.left_slot_info[0].slot_F_x = 1100;
    sf_Upper_SlotOutSignal.left_slot_info[0].slot_F_y = -1200;
    sf_Upper_SlotOutSignal.left_slot_info[0].slot_F_type = 2;
    UpperSerialDebug_SetWriter(capture, file);
    if (UpperSerialDebug_SendVariables() != UPPER_SERIAL_OK) return 8;
    fclose(file);
    UpperSerialDebug_SetWriter(NULL, NULL);
    return bytes_sent == 1634u ? 0 : 9;
}
