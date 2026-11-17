#ifndef COLIGEN_REPLAY_STREAM_INPUT_H
#define COLIGEN_REPLAY_STREAM_INPUT_H
#include <stdint.h>
extern int g_replayStreamActive;
extern int g_replayStreamPending;
extern uint32_t g_replayStreamBoot;
extern uint32_t g_replayStreamCycle;
extern uint8_t g_replayStreamFrames[20][64];
int ReplayStream_GetData(uint32_t id, uint8_t *data, int *length);
#endif
