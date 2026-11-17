#include "ReplayStreamInput.h"
#include <string.h>
int g_replayStreamActive;
int g_replayStreamPending;
uint32_t g_replayStreamBoot;
uint32_t g_replayStreamCycle;
uint8_t g_replayStreamFrames[20][64];
int ReplayStream_GetData(uint32_t id, uint8_t *data, int *length)
{
    unsigned index;
    if (id == 0x640u) index = 0u;
    else if (id >= 0x6b6u && id <= 0x6c8u) index = (unsigned)(id - 0x6b6u) + 1u;
    else return 1;
    memcpy(data, g_replayStreamFrames[index], 64u);
    *length = 64;
    return 0;
}
