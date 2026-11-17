/* Included once, by S20 Replay/dataReplay_main.c after scheduler definitions.
 * Transport only: the existing signal decoder and task bodies remain shared.
 */
#ifndef COLIGEN_REPLAY_STREAM_DRIVER_H
#define COLIGEN_REPLAY_STREAM_DRIVER_H
#include "ReplayStreamInput.h"
#include "UpperSerialDebug.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#ifdef _WIN32
#include <io.h>
#define RCP_DUP _dup
#define RCP_DUP2 _dup2
#define RCP_FILENO _fileno
#define RCP_FDOPEN _fdopen
#else
#include <unistd.h>
#define RCP_DUP dup
#define RCP_DUP2 dup2
#define RCP_FILENO fileno
#define RCP_FDOPEN fdopen
#endif

static FILE *rcp_wire;
static int rcp_failed;
static uint32_t rcp_u32(const uint8_t *p)
{ return (uint32_t)p[0] | ((uint32_t)p[1]<<8u) | ((uint32_t)p[2]<<16u) | ((uint32_t)p[3]<<24u); }
static uint64_t rcp_u64(const uint8_t *p)
{ return (uint64_t)rcp_u32(p) | ((uint64_t)rcp_u32(p+4u)<<32u); }
static void rcp_put32(uint8_t *p, uint32_t value)
{ unsigned i; for(i=0;i<4u;i++) p[i]=(uint8_t)(value>>(8u*i)); }
static void rcp_put64(uint8_t *p, uint64_t value)
{ unsigned i; for(i=0;i<8u;i++) p[i]=(uint8_t)(value>>(8u*i)); }
static uint32_t rcp_crc(const uint8_t *p, unsigned length)
{
    uint32_t crc=0xffffffffu; unsigned i,j;
    for(i=0;i<length;i++) { crc^=p[i]; for(j=0;j<8u;j++) crc=(crc>>1u)^(0xedb88320u & (0u-(crc&1u))); }
    return ~crc;
}
static int rcp_write(unsigned kind, const uint8_t *body, unsigned length)
{
    uint8_t header[16]; memcpy(header,"RCP1",4u);
    rcp_put32(header+4u,kind); rcp_put32(header+8u,length);
    rcp_put32(header+12u,rcp_crc(body,length));
    if(fwrite(header,1u,16u,rcp_wire)!=16u ||
       (length && fwrite(body,1u,length,rcp_wire)!=length) || fflush(rcp_wire)!=0) { rcp_failed=1; return -1; }
    return 0;
}
static int rcp_failure(const char *message)
{ fprintf(stderr,"%s\n",message); (void)rcp_write(5u,(const uint8_t *)message,(unsigned)strlen(message)); return 2; }
static int rcp_output(const uint8_t *data, uint16_t length, void *context)
{
    uint8_t body[8192];
    static uint32_t output_boot=0u, output_cycle=0u, output_ordinal=0u;
    (void)context;
    if(output_boot!=g_replayStreamBoot || output_cycle!=g_replayStreamCycle)
        output_ordinal=0u;
    output_boot=g_replayStreamBoot; output_cycle=g_replayStreamCycle;
    ++output_ordinal;
    if((unsigned)length+16u>sizeof(body)) return -1;
    rcp_put32(body,g_replayStreamBoot); rcp_put32(body+4u,g_replayStreamCycle);
    rcp_put64(body+8u,output_ordinal);
    memcpy(body+16u,data,length);
    return rcp_write(2u,body,(unsigned)length+16u);
}
static int ReplayStream_Open(void)
{
    int descriptor=RCP_DUP(RCP_FILENO(stdout));
    if(descriptor<0) return -1;
    rcp_wire=RCP_FDOPEN(descriptor,"wb");
    if(!rcp_wire) return -1;
#ifdef _WIN32
    _setmode(RCP_FILENO(rcp_wire),_O_BINARY);
    _setmode(RCP_FILENO(stdin),_O_BINARY);
#endif
    /* Existing printf diagnostics cannot corrupt the framed result stream. */
    if(RCP_DUP2(RCP_FILENO(stderr),RCP_FILENO(stdout))<0) return -1;
    setvbuf(rcp_wire,NULL,_IONBF,0);
    return 0;
}
static int ReplayStream_Run(void)
{
    uint8_t header[16], body[1296];
    uint64_t last_ms=0u, tick_ms;
    uint32_t previous_cycle=0u;
    int have_input=0;
    extern int UpperSerialReplay_ForceEveryOutput;
    const char *hello="{\"version\":2,\"vehicle\":\"S20\",\"strict\":true,\"identity\":\"input_cycle_output_ordinal\",\"capabilities\":[\"point\",\"line\",\"attribute\"],\"coordinates\":\"forward_left_mm\"}";
    UpperSerialDebug_SetWriter(rcp_output,NULL);
    UpperSerialReplay_ForceEveryOutput=1;
    if(rcp_write(3u,(const uint8_t *)hello,(unsigned)strlen(hello))!=0) return 2;
    for(;;)
    {
        unsigned kind,length;
        if(fread(header,1u,sizeof(header),stdin)!=sizeof(header)) return rcp_failure("input stream truncated");
        kind=rcp_u32(header+4u); length=rcp_u32(header+8u);
        if(memcmp(header,"RCP1",4u)!=0 || length>sizeof(body)) return rcp_failure("invalid input header");
        if(length && fread(body,1u,length,stdin)!=length) return rcp_failure("input body truncated");
        if(rcp_u32(header+12u)!=rcp_crc(body,length)) return rcp_failure("input CRC mismatch");
        if(kind==4u && length==0u) break;
        if(kind!=1u || length!=sizeof(body)) return rcp_failure("expected 20 complete input records");
        tick_ms=rcp_u64(body+8u)/1000u;
        {
            uint8_t verify[1264];
            const uint8_t *meta=body+16u+19u*64u;
            memcpy(verify,body+16u,1263u); verify[1263]=meta[63];
            if(!rcp_u32(body) || meta[50]!=0xc1u ||
               (rcp_u32(meta+47u)&0xffffffu)!=rcp_u32(body) ||
               rcp_u32(meta+51u)!=rcp_u32(body+4u) ||
               rcp_u32(meta+55u)!=tick_ms ||
               rcp_u32(meta+59u)!=rcp_crc(verify,sizeof(verify)))
                return rcp_failure("raw cycle identity/CRC missing");
        }
        if(have_input && (rcp_u32(body)!=g_replayStreamBoot ||
           rcp_u32(body+4u)!=previous_cycle+1u || tick_ms<=last_ms))
            return rcp_failure("input discontinuity: restart replay epoch");
        if(have_input && tick_ms>last_ms+10000u) return rcp_failure("input gap exceeds 10 seconds");
        if(!have_input)
        {
            static ReplayTaskConfig tasks[] = {
                {"stream1ms",1u,2u,Replay_Core3HighTask,NULL,1u},
                {"stream5ms",5u,1u,Replay_Core3Task5ms,NULL,1u},
                {"stream10ms",10u,1u,Replay_Core3Task10ms,NULL,1u},
                {"stream20ms",20u,1u,Replay_Core3Task20ms,NULL,1u}};
            unsigned index;
            uint64_t start=tick_ms>0u?tick_ms-1u:0u;
            for(index=0u;index<4u;index++)
            {
                uint32_t period=tasks[index].period_ms;
                uint32_t delay=(uint32_t)((1u+period-start%period)%period);
                tasks[index].first_release_delay_ms=delay?delay:period;
            }
            g_replayScheduler=ReplayScheduler_Create(tasks,4u,start);
            if(!g_replayScheduler) return rcp_failure("scheduler allocation failed");
            g_replayScheduleTickMs=start;
        }
        else if(tick_ms>g_replayScheduleTickMs+1u &&
                Replay_RunTasksUntil(REPLAY_SCHED_VEHICLE_CORE3,tick_ms-1u)!=0)
            return rcp_failure("scheduler advance failed");
        g_replayStreamBoot=rcp_u32(body);
        g_replayStreamCycle=rcp_u32(body+4u);
        memcpy(g_replayStreamFrames,body+16u,1280u);
        g_replayNextInputTickMs=tick_ms;
        g_replayStreamPending=1;
        if(Replay_RunTasksUntil(REPLAY_SCHED_VEHICLE_CORE3,tick_ms)!=0 || rcp_failed)
            return rcp_failure("input delivery failed");
        last_ms=tick_ms; previous_cycle=g_replayStreamCycle; have_input=1;
    }
    if(have_input && Replay_RunTasksUntil(REPLAY_SCHED_VEHICLE_CORE3,last_ms+20u)!=0)
        return rcp_failure("scheduler drain failed");
    if(g_replayScheduler) { ReplayScheduler_Destroy(g_replayScheduler); g_replayScheduler=NULL; }
    if(rcp_failed) return 2;
    return rcp_write(4u,NULL,0u)==0?0:2;
}
#endif
