"""Estimate a brake-light indication from timestamped speed samples."""

import math


class BrakeLightView:
    WINDOW_US = 100_000
    MAX_GAP_US = 500_000
    HOLD_US = 250_000
    MIN_DROP_KMH = 0.25
    MIN_DECEL_MPS2 = 0.65

    def __init__(self):
        self.reset()

    def reset(self):
        self.active = False
        self._last = self._anchor = None
        self._lit_until = 0

    def update(self, speed_kmh, timestamp_us, *, frame_index=None, epoch=None):
        try:
            speed = abs(float(speed_kmh))
        except (TypeError, ValueError):
            self.reset()
            return
        if timestamp_us is None or not math.isfinite(speed):
            self.reset()
            return

        sample = timestamp_us, speed, frame_index, epoch
        if sample == self._last:
            return

        last = self._last
        if (last is None or epoch != last[3]
                or frame_index is not None and last[2] is not None and frame_index != last[2] + 1
                or not 0 < timestamp_us - last[0] <= self.MAX_GAP_US):
            self.reset()
            self._last = self._anchor = sample
            return

        self._last = sample
        elapsed = timestamp_us - self._anchor[0]
        if elapsed >= self.WINDOW_US:
            drop = self._anchor[1] - speed
            if drop >= max(self.MIN_DROP_KMH, self.MIN_DECEL_MPS2 * 3.6 * elapsed / 1e6):
                self._lit_until = timestamp_us + self.HOLD_US
            self._anchor = sample
        self.active = timestamp_us < self._lit_until
