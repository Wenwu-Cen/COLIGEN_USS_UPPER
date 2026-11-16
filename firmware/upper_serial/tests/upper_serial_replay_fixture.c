/* Controlled producer fixture; no input file or UART hardware required. */
#include "UpperSerialReplay.h"
#include "UpperSerialDebug.h"
#include "SensorData.h"
#include "PDC_Track_If.h"
#include "APACommonPar.h"
#include <stdio.h>

#define DEFINE_STUB(name) __typeof__(name) name
DEFINE_STUB(VCU_GearLeverPos);
DEFINE_STUB(VCU_AmbientTemp);
DEFINE_STUB(VCU_VehicleSpeed_KM_H);
DEFINE_STUB(stTrackCurCarPos);
DEFINE_STUB(stPointOut_Upper);
DEFINE_STUB(stOneOutSi_Upper);
DEFINE_STUB(d_SameFreq_Front_Cnt);
DEFINE_STUB(d_SameFreq_Rear_Cnt);
DEFINE_STUB(Front_SameFreq_Flag);
DEFINE_STUB(Rear_SameFreq_Flag);
DEFINE_STUB(USS_OriginalInfoGroup_data);
DEFINE_STUB(USS_OriginalInfo_DE_Std_Filt);
DEFINE_STUB(USS_OriginalInfo_CE_Std_Filt);
static uint64_t now_ms;
static unsigned int calls;
uint64_t R_GetTimeStamp_1ms_Cnt(void) { return now_ms; }
static int capture(const uint8_t *data, uint16_t size, void *context)
{
    ++calls;
    return fwrite(data, 1, size, (FILE *)context) == size ? 0 : -1;
}
int main(int argc, char **argv)
{
    FILE *file;
    if (argc != 2) return 2;
    file = fopen(argv[1], "wb");
    if (file == NULL) return 3;
    VCU_GearLeverPos = 2;
    VCU_AmbientTemp = 25;
    VCU_VehicleSpeed_KM_H = 7.5f;
    stTrackCurCarPos.Coordinate.x = 2000;
    stTrackCurCarPos.Coordinate.y = -3000;
    stTrackCurCarPos.CarAng = .5f;
    stPointOut_Upper[3].ObjID = 333;
    stPointOut_Upper[3].x = 1000;
    stPointOut_Upper[3].y = 250;
    stOneOutSi_Upper[4].cNum = 17;
    stOneOutSi_Upper[4].wStartx = 200;
    stOneOutSi_Upper[4].wStarty = 300;
    stOneOutSi_Upper[4].wEndx = 400;
    stOneOutSi_Upper[4].wEndy = 500;
    USS_OriginalInfo_DE_Std_Filt.USS_OriginalInfo[0].USS_ObjInfo[0].USS_ObjDis = 123;
    USS_OriginalInfo_DE_Std_Filt.USS_OriginalInfo[0].USS_ObjInfo[0].USS_ObjWidth = 45;
    USS_OriginalInfo_CE_Std_Filt[CE_From_RightSns].USS_OriginalInfo[1].USS_ObjInfo[0].USS_ObjDis = 567;
    USS_OriginalInfo_CE_Std_Filt[CE_From_RightSns].USS_OriginalInfo[1].USS_ObjInfo[0].USS_ObjWidth = 67;
    UpperSerialDebug_SetWriter(capture, file);
    now_ms = 100;
    UpperSerialReplay_AfterOutput();
    now_ms = 150;
    UpperSerialReplay_AfterOutput(); /* throttled */
    now_ms = 200;
    UpperSerialReplay_AfterOutput();
    fclose(file);
    return calls == 2 ? 0 : 4;
}
