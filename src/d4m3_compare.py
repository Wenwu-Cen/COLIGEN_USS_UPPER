"""D4M3 E541 UDP cycle metadata and visualization result identity."""

from binascii import crc_hqx
from struct import Struct

from replay_capture_protocol import InputCycle, LEGACY_IDS

INPUT_IDENTITY = Struct("<IIIBH")
INPUT_IDS = frozenset(LEGACY_IDS)


class D4M3DatagramAssembler:
    """Each CAN68 datagram carries one complete D4M3 measurement."""

    def __init__(self):
        self.complete = self.incomplete = self.invalid = self.legacy = 0
        self.last = None

    def feed_datagram(self, records):
        frames = dict(records)
        if not frames.keys() & INPUT_IDS:
            return None
        if len(records) != len(frames):
            self.invalid += 1
            return None
        if frames.keys() != INPUT_IDS:
            self.incomplete += 1
            return None
        payloads = tuple(frames[identifier] for identifier in LEGACY_IDS)
        if any(len(data) != 64 for data in payloads):
            self.invalid += 1
            return None
        vehicle, timing = payloads[-1], payloads[-2]
        tagged, cycle, result_cycle, _, ordinal = INPUT_IDENTITY.unpack_from(vehicle, 48)
        if tagged >> 24 != 0xD4:
            self.legacy += 1
            return None
        boot = tagged & 0xFFFFFF
        timestamp = timing[44:50] + timing[58:60]
        checksum = crc_hqx(vehicle[48:56] + timing[50:58] + vehicle[56:63] + timestamp, 0xFFFF)
        if not boot or checksum != int.from_bytes(timing[60:62], "little"):
            self.invalid += 1
            return None
        if self.last and self.last[:2] == (boot, cycle):
            if self.last[2] != payloads:
                self.invalid += 1
            return None
        if self.last and self.last[0] == boot:
            delta = (cycle - self.last[1]) & 0xFFFFFFFF
            if not 0 < delta < 0x80000000:
                self.invalid += 1
                return None
            self.incomplete += delta - 1
        self.last = boot, cycle, payloads
        self.complete += 1
        result_stamp = int.from_bytes(timestamp, "little")
        tick_ms = int.from_bytes(timing[50:58], "little")
        identity = (result_stamp, (boot, result_cycle, ordinal)) if result_stamp and ordinal else None
        return InputCycle(boot, cycle, tick_ms * 1000, payloads), identity
