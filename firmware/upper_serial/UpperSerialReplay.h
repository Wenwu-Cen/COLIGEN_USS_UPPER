#ifndef COLIGEN_UPPER_SERIAL_REPLAY_H
#define COLIGEN_UPPER_SERIAL_REPLAY_H
#include "sfType.h"

#if defined(LAUTERBACH_UPPER_DEBUG) && LAUTERBACH_UPPER_SERIAL_DEBUG
/* Called after the replay's point/line output, on the same producer task. */
void UpperSerialReplay_AfterOutput(void);
#else
#define UpperSerialReplay_AfterOutput() ((void)0)
#endif
#endif
