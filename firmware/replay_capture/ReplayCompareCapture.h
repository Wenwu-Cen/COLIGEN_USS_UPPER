#ifndef COLIGEN_REPLAY_COMPARE_CAPTURE_H
#define COLIGEN_REPLAY_COMPARE_CAPTURE_H
#include <stdint.h>
/* APIs are observational; callers retain ownership of the 20 frozen PDUs. */
void ReplayCompare_StampRaw(uint8_t *frames[20], uint32_t tick_ms, uint32_t boot_seed);
void ReplayCompare_Latch(void);
void ReplayCompare_Publish(const uint8_t *packet, uint32_t size, uint64_t task_us);
extern volatile uint32_t sf_Upper_CompareGeneration;
extern volatile uint32_t sf_Upper_CompareLength;
extern volatile uint8_t sf_Upper_CompareBuffer[2048];
#endif
