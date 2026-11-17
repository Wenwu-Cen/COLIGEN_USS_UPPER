#include "UpperCanTypes.h"
#include <string.h>
/* UPPER CAN v1: one frozen USSV snapshot, transported in 56-byte pieces.
 * The existing 20 RTE PDUs are reused; no C padding/bitfields go on the wire.
 * At 80 points/20 lines/6 slots a snapshot is 1657 bytes (30 fragments),
 * hence two 40-ms batches. Unused slots in the last batch are explicit idle.
 * Keep the buffer unchanged until every fragment has been handed to RTE. */
#if defined(OBJ_DEBUGCAN) && !defined(SUPPORT_RAWDATA_DEBUGCAN)
#define UPPER_CAN_PACKET_SIZE (1657u)
#define UPPER_CAN_DATA_SIZE (56u)
#define CtCdUSS_START_SEC_VAR_ZERO_INIT_UNSPECIFIED
#include "CtCdUSS_MemMap.h"
static uint8_t UpperCanPacket[UPPER_CAN_PACKET_SIZE] = {0};
static uint32_t UpperCanSequence = 0u;
static uint8_t UpperCanBatchFirst = 0u;
#define CtCdUSS_STOP_SEC_VAR_ZERO_INIT_UNSPECIFIED
#include "CtCdUSS_MemMap.h"

#define CtCdUSS_START_SEC_CODE
#include "CtCdUSS_MemMap.h"
typedef char UpperCanFloat32[(sizeof(float) == 4u) ? 1 : -1];
static void UpperCanPut16(uint8_t *p, uint16_t v)
{ p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8u); }
static void UpperCanPut32(uint8_t *p, uint32_t v)
{ UpperCanPut16(p, (uint16_t)v); UpperCanPut16(p + 2u, (uint16_t)(v >> 16u)); }
static void UpperCanPut64(uint8_t *p, uint64_t v)
{ uint8_t i; for(i = 0u; i < 8u; i++) p[i] = (uint8_t)(v >> (8u * i)); }
static void UpperCanFloat(uint8_t *p, float v)
{ uint32_t bits; memcpy(&bits, &v, 4u); UpperCanPut32(p, bits); }
static uint32_t UpperCanCrc(const uint8_t *p, uint16_t n)
{
    uint32_t crc = 0xffffffffu;
    uint16_t i; uint8_t bit;
    for(i = 0u; i < n; i++) {
        crc ^= p[i];
        for(bit = 0u; bit < 8u; bit++)
            crc = (crc >> 1u) ^ ((crc & 1u) ? 0xedb88320u : 0u);
    }
    return ~crc;
}
static uint8_t *UpperCanTlv(uint8_t *p, uint8_t tag, uint16_t size)
{ p[0] = tag; UpperCanPut16(p + 1u, size); return p + 3u; }
static void UpperCanSlot(uint8_t *p, const Upper_SlotOutSignalInfo *s)
{
    UpperCanPut64(p, s->timestamp); p[8] = s->slot_id; p[9] = s->slot_type;
    UpperCanPut16(p+10u,s->slot_width); UpperCanPut16(p+12u,s->slot_Depth);
    UpperCanPut16(p+14u,(uint16_t)s->slot_A_x); UpperCanPut16(p+16u,(uint16_t)s->slot_A_y); p[18]=s->slot_A_type;
    UpperCanPut16(p+19u,(uint16_t)s->slot_B_x); UpperCanPut16(p+21u,(uint16_t)s->slot_B_y);
    UpperCanPut16(p+23u,(uint16_t)s->slot_C_x); UpperCanPut16(p+25u,(uint16_t)s->slot_C_y);
    UpperCanPut16(p+27u,(uint16_t)s->slot_D_x); UpperCanPut16(p+29u,(uint16_t)s->slot_D_y);
    UpperCanPut16(p+31u,(uint16_t)s->slot_E_x); UpperCanPut16(p+33u,(uint16_t)s->slot_E_y);
    UpperCanPut16(p+35u,(uint16_t)s->slot_F_x); UpperCanPut16(p+37u,(uint16_t)s->slot_F_y); p[39]=s->slot_F_type;
}
static void UpperCanCapture(uint64_t timestamp_us)
{
    uint8_t *p = UpperCanPacket;
    const Upper_VehicleOutSignal *v = &sf_Upper_VehicleOutSignal;
    uint8_t i;
    ++UpperCanSequence;
    p[0]='U'; p[1]='S'; p[2]='S'; p[3]='V'; p[4]=1u; p[5]=0u;
    UpperCanPut16(p+6u,UPPER_CAN_PACKET_SIZE-16u); UpperCanPut32(p+8u,UpperCanSequence);
    p = UpperCanTlv(p+12u,1u,15u);
    p[0]=sf_Upper_StatusOutSignal.GearLever; UpperCanPut16(p+1u,sf_Upper_StatusOutSignal.Temp);
    UpperCanFloat(p+3u,sf_Upper_StatusOutSignal.Speed);
    /* Capture clock is explicitly microseconds; do not inherit the old raw-CAN ms tick. */
    UpperCanPut64(p+7u,timestamp_us);
    p=UpperCanTlv(p+15u,2u,12u);
    UpperCanFloat(p,sf_Upper_OdoOutSignal.odo_x); UpperCanFloat(p+4u,sf_Upper_OdoOutSignal.odo_y); UpperCanFloat(p+8u,sf_Upper_OdoOutSignal.odo_ang);
    p=UpperCanTlv(p+12u,3u,52u);
    UpperCanPut16(p,v->CarLength); UpperCanPut16(p+2u,v->CarWidth);
#define UPPER_CAN_SENSOR_POS(index, name) \
    UpperCanPut16(p+4u+4u*(index),(uint16_t)v->SnsPos##name##_X); \
    UpperCanPut16(p+6u+4u*(index),(uint16_t)v->SnsPos##name##_Y)
    UPPER_CAN_SENSOR_POS(0u,RRS); UPPER_CAN_SENSOR_POS(1u,RRC); UPPER_CAN_SENSOR_POS(2u,RRM);
    UPPER_CAN_SENSOR_POS(3u,RLM); UPPER_CAN_SENSOR_POS(4u,RLC); UPPER_CAN_SENSOR_POS(5u,RLS);
    UPPER_CAN_SENSOR_POS(6u,FRS); UPPER_CAN_SENSOR_POS(7u,FRC); UPPER_CAN_SENSOR_POS(8u,FRM);
    UPPER_CAN_SENSOR_POS(9u,FLM); UPPER_CAN_SENSOR_POS(10u,FLC); UPPER_CAN_SENSOR_POS(11u,FLS);
#undef UPPER_CAN_SENSOR_POS
    p=UpperCanTlv(p+52u,4u,235u);
    UpperCanPut16(p,sf_Upper_RawDataOutSignal.samefreq_front_Cnt);
    UpperCanPut16(p+2u,sf_Upper_RawDataOutSignal.samefreq_rear_Cnt);
    p[4]=sf_Upper_RawDataOutSignal.samefreq_front_Flag; p[5]=sf_Upper_RawDataOutSignal.samefreq_rear_Flag; p[6]=12u; p+=7u;
    for(i=0u;i<12u;i++,p+=19u) {
        const Upper_RawDataOutSignalInfo *r=&sf_Upper_RawDataOutSignal.rawdata_info[i];
        p[0]=r->mode; UpperCanPut16(p+1u,r->de); UpperCanPut16(p+3u,r->de_peak); UpperCanPut16(p+5u,r->de_width);
        UpperCanPut16(p+7u,r->ce_left); UpperCanPut16(p+9u,r->ce_left_peak); UpperCanPut16(p+11u,r->ce_left_width);
        UpperCanPut16(p+13u,r->ce_right); UpperCanPut16(p+15u,r->ce_right_peak); UpperCanPut16(p+17u,r->ce_right_width);
    }
    p=UpperCanTlv(p,5u,52u);
    p[0]=sf_Upper_PDCOutSignal.pdc_sts; p[1]=sf_Upper_PDCOutSignal.front_sts; p[2]=sf_Upper_PDCOutSignal.rear_sts; p[3]=12u; p+=4u;
    for(i=0u;i<12u;i++,p+=4u) {
        UpperCanPut16(p,sf_Upper_PDCOutSignal.snspdc_info[i].dis);
        p[2]=sf_Upper_PDCOutSignal.snspdc_info[i].range; p[3]=sf_Upper_PDCOutSignal.snspdc_info[i].fault;
    }
    p=UpperCanTlv(p,6u,722u); UpperCanPut16(p,80u); p+=2u;
    for(i=0u;i<80u;i++,p+=9u) {
        const Upper_PointOutSignal *s=&sf_Upper_PointOutSignal[i];
        UpperCanPut16(p,s->ObjID); UpperCanPut16(p+2u,(uint16_t)s->x); UpperCanPut16(p+4u,(uint16_t)s->y);
        p[6]=s->cHight; p[7]=s->SNS_Txindex; p[8]=s->SNS_Rxindex;
    }
    p=UpperCanTlv(p,7u,262u); UpperCanPut16(p,20u); p+=2u;
    for(i=0u;i<20u;i++,p+=13u) {
        const Upper_LineOutSignal *s=&sf_Upper_LineOutSignal[i];
        p[0]=s->cNum; p[1]=s->cHight; p[2]=s->cObjType;
        UpperCanPut16(p+3u,(uint16_t)s->wStartx); UpperCanPut16(p+5u,(uint16_t)s->wStarty);
        UpperCanPut16(p+7u,(uint16_t)s->wEndx); UpperCanPut16(p+9u,(uint16_t)s->wEndy); UpperCanPut16(p+11u,s->wDist);
    }
    p=UpperCanTlv(p,8u,244u); p[0]=sf_Upper_SlotOutSignal.slot_sts;
    p[1]=(sf_Upper_SlotOutSignal.left_slot_num>3u)?3u:sf_Upper_SlotOutSignal.left_slot_num;
    p[2]=(sf_Upper_SlotOutSignal.right_slot_num>3u)?3u:sf_Upper_SlotOutSignal.right_slot_num;
    p[3]=3u; p+=4u;
    for(i=0u;i<3u;i++,p+=40u) UpperCanSlot(p,&sf_Upper_SlotOutSignal.left_slot_info[i]);
    for(i=0u;i<3u;i++,p+=40u) UpperCanSlot(p,&sf_Upper_SlotOutSignal.right_slot_info[i]);
    /* Optional USSV v1 extension: one direction byte per line, same array order. */
    p=UpperCanTlv(p,9u,20u);
    for(i=0u;i<20u;i++) *p++=sf_Upper_LineOutSignal[i].cDirect;
    UpperCanPut32(p,UpperCanCrc(UpperCanPacket,UPPER_CAN_PACKET_SIZE-4u));
}
void OutputSignalCan_BeginBatch(uint64_t timestamp_us)
{
    if(UpperCanBatchFirst==0u) UpperCanCapture(timestamp_us);
}
void OutputSignalCan_GetFrame(uint8_t slot, uint8_t *out)
{
    uint8_t fragment=(uint8_t)(UpperCanBatchFirst+slot);
    uint16_t offset=(uint16_t)fragment*UPPER_CAN_DATA_SIZE;
    uint16_t count;
    memset(out,0,64u);
    out[0]='U'; out[1]='C'; out[2]=1u; out[3]=0xffu;
    UpperCanPut16(out+4u,(uint16_t)UpperCanSequence); UpperCanPut16(out+6u,UPPER_CAN_PACKET_SIZE);
    if(slot<20u && offset<UPPER_CAN_PACKET_SIZE) {
        out[3]=fragment; count=(uint16_t)(UPPER_CAN_PACKET_SIZE-offset);
        if(count>UPPER_CAN_DATA_SIZE) count=UPPER_CAN_DATA_SIZE;
        memcpy(out+8u,UpperCanPacket+offset,count);
    }
    if(slot==19u) UpperCanBatchFirst=(UpperCanBatchFirst==0u)?20u:0u;
}
#define CtCdUSS_STOP_SEC_CODE
#include "CtCdUSS_MemMap.h"
#endif
