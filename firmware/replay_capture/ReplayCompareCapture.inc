/* Include once in the existing Lauterbach_Var.c translation unit. */
#include "ReplayCompareCapture.h"
#include <string.h>
#define CtCdUSS_START_SEC_VAR_ZERO_INIT_UNSPECIFIED
#include "CtCdUSS_MemMap.h"
volatile uint32_t sf_Upper_CompareGeneration = 0u;
volatile uint32_t sf_Upper_CompareLength = 0u;
volatile uint8_t sf_Upper_CompareBuffer[2048] = {0};
static volatile uint32_t compare_boot = 0u, compare_cycle = 0u;
static uint32_t compare_latched_boot = 0u, compare_latched_cycle = 0u;
static uint32_t compare_output_ordinal = 0u;
#define CtCdUSS_STOP_SEC_VAR_ZERO_INIT_UNSPECIFIED
#include "CtCdUSS_MemMap.h"
#define CtCdUSS_START_SEC_CODE
#include "CtCdUSS_MemMap.h"
static void compare_put32(volatile uint8_t *p, uint32_t value)
{ unsigned i; for(i=0u;i<4u;i++) p[i]=(uint8_t)(value>>(i*8u)); }
static uint32_t compare_crc_byte(uint32_t crc, uint8_t value)
{
    unsigned bit; crc^=value;
    for(bit=0u;bit<8u;bit++) crc=(crc>>1u)^(0xedb88320u & (0u-(crc&1u)));
    return crc;
}
void ReplayCompare_StampRaw(uint8_t *frames[20], uint32_t tick_ms, uint32_t boot_seed)
{
    unsigned i,j; uint32_t crc=0xffffffffu;
    if(compare_boot==0u) compare_boot=(boot_seed & 0xffffffu)?(boot_seed & 0xffffffu):1u;
    ++compare_cycle;
    for(i=0u;i<20u;i++)
        for(j=0u;j<(i==19u?47u:64u);j++) crc=compare_crc_byte(crc,frames[i][j]);
    crc=compare_crc_byte(crc,frames[19][63]);
    compare_put32(frames[19]+47u,compare_boot | 0xc1000000u);
    compare_put32(frames[19]+51u,compare_cycle);
    compare_put32(frames[19]+55u,tick_ms);
    compare_put32(frames[19]+59u,~crc);
}
void ReplayCompare_Latch(void)
{
    uint32_t boot=compare_boot, cycle=compare_cycle;
    if(boot!=compare_latched_boot || cycle!=compare_latched_cycle)
        compare_output_ordinal=0u;
    compare_latched_boot=boot; compare_latched_cycle=cycle;
    ++compare_output_ordinal;
}
void ReplayCompare_Publish(const uint8_t *packet, uint32_t size, uint64_t task_us)
{
    unsigned i;
    (void)task_us; /* Wall time remains in USSV; it is not a pairing key. */
    if(!compare_latched_boot || size+16u>sizeof(sf_Upper_CompareBuffer)) return;
    ++sf_Upper_CompareGeneration; /* odd: producer owns the frozen buffer */
    compare_put32(sf_Upper_CompareBuffer,compare_latched_boot);
    compare_put32(sf_Upper_CompareBuffer+4u,compare_latched_cycle);
    compare_put32(sf_Upper_CompareBuffer+8u,compare_output_ordinal);
    compare_put32(sf_Upper_CompareBuffer+12u,0u);
    for(i=0u;i<size;i++) sf_Upper_CompareBuffer[16u+i]=packet[i];
    sf_Upper_CompareLength=size+16u;
    ++sf_Upper_CompareGeneration; /* even: CS+ must verify before/after equality */
}
#define CtCdUSS_STOP_SEC_CODE
#include "CtCdUSS_MemMap.h"
