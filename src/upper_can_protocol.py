"""S20 UC v1 CAN-FD fragments containing a complete CRC-checked USSV snapshot.

The bytes carry the native S20 sf_Upper_* values (CS+ conventions), rather
than the metres/forward-left convention of the serial adapter.
"""
from collections import OrderedDict
from dataclasses import replace
import struct
import zlib

from serial_protocol import HEADER, VERSION, decode_payload, SENSOR_NAMES

CAN_IDS = (0x640, *range(0x6B6, 0x6C9))
SLOTS = {can_id: i for i, can_id in enumerate(CAN_IDS)}
FRAGMENT = struct.Struct("<2sBBHH")
DATA_SIZE = 56
PACKET_SIZE = 1634


class UpperCanDecoder:
    """Bounded assembly: out-of-order IDs, duplicates, loss and restart safe.

    A partial snapshot is never visible. The inner sequence and CRC must agree
    with the outer envelope. Only four in-flight snapshots are retained.
    """

    def __init__(self):
        self.pending = OrderedDict()
        self.completed = OrderedDict()
        self.frames_total = 0
        self.decode_errors = 0
        self.last_error = None
        self.last_sequence = None

    @staticmethod
    def recognizes(can_id, data):
        # Signature is reserved for the new protocol on these IDs; malformed
        # lengths/versions are rejected here rather than fed to the legacy DBC.
        return can_id in SLOTS and data[:2] == b"UC"

    def feed(self, can_id, data):
        if not self.recognizes(can_id, data):
            return None
        try:
            if len(data) != 64:
                raise ValueError("UPPER CAN 必须为 64 字节 CAN-FD")
            _, version, index, sequence, size = FRAGMENT.unpack_from(data)
            if version != 1 or size != PACKET_SIZE:
                raise ValueError("UPPER CAN 版本或长度错误")
            if index == 255:  # Explicit idle in the final batch.
                return None
            count = (size + DATA_SIZE - 1) // DATA_SIZE
            if index >= count or index % 20 != SLOTS[can_id]:
                raise ValueError("UPPER CAN 分片编号与 CAN ID 不一致")
            key = (sequence, size)
            fragments = self.pending.setdefault(key, {})
            self.pending.move_to_end(key)
            while len(self.pending) > 4:
                self.pending.popitem(last=False)
            chunk = data[8:8 + min(DATA_SIZE, size - index * DATA_SIZE)]
            if index in fragments and fragments[index] != chunk:
                # A reboot may reuse a sequence. Discard all old pieces before
                # accepting the replacement; never stitch across the restart.
                fragments.clear()
            fragments[index] = chunk
            if len(fragments) != count:
                return None
            del self.pending[key]
            packet = b"".join(fragments[i] for i in range(count))
            magic, version, flags, length, full_sequence = HEADER.unpack_from(packet)
            if (magic != b"USSV" or version != VERSION or flags != 0
                    or length + HEADER.size + 4 != size
                    or full_sequence & 0xFFFF != sequence):
                raise ValueError("UPPER CAN 内外帧头不一致")
            crc = struct.unpack_from("<I", packet, size - 4)[0]
            if zlib.crc32(packet[:-4]) != crc:
                raise ValueError("UPPER CAN CRC32 校验失败")
            # Include CRC in the fingerprint so a reboot/sequence reuse is not
            # mistaken for a retransmission of a previous complete snapshot.
            fingerprint = (full_sequence, crc)
            if fingerprint in self.completed:
                return None
            frame = decode_payload(full_sequence, packet[HEADER.size:-4])
            if (len(frame.points), len(frame.lines), frame.slot_meta[3]) != (80, 20, 3):
                raise ValueError("S20 UPPER CAN 数组容量错误")
            if self.last_sequence is not None:
                delta = (full_sequence - self.last_sequence) & 0xFFFFFFFF
                if delta >= 0x80000000 and full_sequence != 1:
                    # A delayed old snapshot must not move the displayed scene
                    # backwards. Sequence 1 is the MCU's explicit reboot start.
                    return None
            self.last_sequence = full_sequence
            # New complete frame supersedes all partial older scenes. This also
            # prevents a late tail from overwriting the current geometry.
            self.pending.clear()
            self.completed[fingerprint] = None
            while len(self.completed) > 4:
                self.completed.popitem(last=False)
            self.frames_total += 1
            return frame
        except (ValueError, struct.error) as exc:
            self.decode_errors += 1
            self.last_error = str(exc)
            return None


def build_can_snapshot(frame):
    """Use the normal UI models, while explicitly applying S20/CS+ units."""
    from map_view import ODO_MM_RIGHT_FORWARD
    from serial_source import build_serial_snapshot

    snapshot = build_serial_snapshot(frame, lateral_sign=-1)
    # CS+ slot decoding preserves the six coordinate pairs verbatim. Slots
    # have their own firmware convention; do not mirror them with obstacles.
    from viewer_models import LogSlot
    slots = []
    _, left, right, capacity = frame.slot_meta
    for i, row in enumerate(frame.slots):
        if i % capacity >= (left if i < capacity else right):
            continue
        xy = [(row[5], row[6]), *zip(row[8:18:2], row[9:18:2])]
        if (len({point for point in xy if point != (0, 0)}) < 2
                or any(v in (-32768, 32767) for point in xy for v in point)):
            continue
        slots.append(LogSlot(i, row[1], row[2], row[3], row[4], row[0], row[7], row[18], xy))
    snapshot.frame[6][:] = slots
    # S20 vehicle and odometry are X=right/Y=forward in mm. Obstacles
    # are X=forward/Y=right in mm. Speed already comes from ESP in km/h.
    probes = {name: (frame.vehicle[3 + 2*i], -frame.vehicle[2 + 2*i])
              for i, name in enumerate(SENSOR_NAMES)}
    vehicle = dict(length=frame.vehicle[0], width=frame.vehicle[1], probes=probes)
    data = dict(snapshot.data, odo_convention=ODO_MM_RIGHT_FORWARD,
                odo=frame.odo, vehicle_demo=vehicle, vehicle=vehicle,
                transport="upper_can_v1")
    return replace(snapshot, data=data)
