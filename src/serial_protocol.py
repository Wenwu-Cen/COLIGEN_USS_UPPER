"""UPPER serial v1: explicit little-endian fields, TLV blocks and CRC32.

The format deliberately does not transmit C structure padding. See
docs/SERIAL_PROTOCOL.md and the matching UpperSerial.c firmware adapter.
"""

from dataclasses import dataclass
import math
import struct
import zlib


MAGIC = b"USSV"
VERSION = 1
HEADER = struct.Struct("<4sBBHI")
TLV = struct.Struct("<BH")
STATUS = struct.Struct("<BHfQ")
ODO = struct.Struct("<fff")
VEHICLE = struct.Struct("<HH24h")
RAW_HEADER = struct.Struct("<HHBBB")
RAW = struct.Struct("<B9H")
PDC_HEADER = struct.Struct("<BBBB")
PDC = struct.Struct("<HBB")
POINT = struct.Struct("<HhhBBB")
LINE = struct.Struct("<BBBhhhhH")
SLOT_HEADER = struct.Struct("<BBBB")
SLOT = struct.Struct("<QBBHHhhBhhhhhhhhhhB")
MAX_PAYLOAD = 8192
SENSOR_NAMES = ("RRS", "RRC", "RRM", "RLM", "RLC", "RLS",
                "FRS", "FRC", "FRM", "FLM", "FLC", "FLS")
DISPLAY_NAMES = ("FLS", "FLC", "FLM", "FRM", "FRC", "FRS",
                 "RLS", "RLC", "RLM", "RRM", "RRC", "RRS")


@dataclass(frozen=True)
class UpperFrame:
    sequence: int
    status: tuple
    odo: tuple
    vehicle: tuple
    raw_meta: tuple
    raw: tuple
    pdc_meta: tuple
    pdc: tuple
    points: tuple
    lines: tuple
    slot_meta: tuple
    slots: tuple


def _records(body, record, count, offset=0, maximum=256):
    if count > maximum or len(body) != offset + count * record.size:
        raise ValueError("数组数量或字段长度错误")
    return tuple(record.iter_unpack(body[offset:]))


def decode_payload(sequence, payload):
    blocks = {}
    offset = 0
    while offset < len(payload):
        if len(payload) - offset < TLV.size:
            raise ValueError("结构体块头不完整")
        tag, size = TLV.unpack_from(payload, offset)
        offset += TLV.size
        if tag in blocks or offset + size > len(payload):
            raise ValueError("结构体块重复或不完整")
        blocks[tag] = payload[offset:offset + size]
        offset += size
    if not set(range(1, 9)).issubset(blocks):
        raise ValueError("缺少完整的 sf_Upper 调试变量块")
    try:
        status = STATUS.unpack(blocks[1])
        odo = ODO.unpack(blocks[2])
        vehicle = VEHICLE.unpack(blocks[3])
        raw_meta = RAW_HEADER.unpack_from(blocks[4])
        if raw_meta[4] != 12:
            raise ValueError("RAW 必须包含 12 个探头")
        raw = _records(blocks[4], RAW, 12, RAW_HEADER.size, 12)
        pdc_meta = PDC_HEADER.unpack_from(blocks[5])
        if pdc_meta[3] != 12:
            raise ValueError("PDC 必须包含 12 个探头")
        pdc = _records(blocks[5], PDC, 12, PDC_HEADER.size, 12)
        points = _records(blocks[6], POINT, struct.unpack_from("<H", blocks[6])[0], 2)
        lines = _records(blocks[7], LINE, struct.unpack_from("<H", blocks[7])[0], 2, 64)
        slot_meta = SLOT_HEADER.unpack_from(blocks[8])
        _, left, right, side_capacity = slot_meta
        if side_capacity not in (3, 4) or max(left, right) > side_capacity:
            raise ValueError("车位数量或容量错误")
        slots = _records(blocks[8], SLOT, side_capacity * 2, SLOT_HEADER.size, 8)
    except struct.error as exc:
        raise ValueError("sf_Upper 结构体长度错误") from exc
    if not all(math.isfinite(v) for v in (status[2], *odo)):
        raise ValueError("速度或里程计含非有限值")
    return UpperFrame(sequence, status, odo, vehicle, raw_meta[:4], raw,
                      pdc_meta[:3], pdc, points, lines, slot_meta, slots)


def encode_frame(frame):
    """Reference encoder, also used by the serial simulator and interoperability tests."""
    bodies = (
        STATUS.pack(*frame.status), ODO.pack(*frame.odo), VEHICLE.pack(*frame.vehicle),
        RAW_HEADER.pack(*frame.raw_meta, len(frame.raw))
        + b"".join(RAW.pack(*r) for r in frame.raw),
        PDC_HEADER.pack(*frame.pdc_meta, len(frame.pdc))
        + b"".join(PDC.pack(*r) for r in frame.pdc),
        struct.pack("<H", len(frame.points)) + b"".join(POINT.pack(*r) for r in frame.points),
        struct.pack("<H", len(frame.lines)) + b"".join(LINE.pack(*r) for r in frame.lines),
        SLOT_HEADER.pack(*frame.slot_meta) + b"".join(SLOT.pack(*r) for r in frame.slots),
    )
    payload = b"".join(TLV.pack(i, len(body)) + body for i, body in enumerate(bodies, 1))
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("串口帧过长")
    packet = HEADER.pack(MAGIC, VERSION, 0, len(payload), frame.sequence) + payload
    return packet + struct.pack("<I", zlib.crc32(packet))


class UpperStreamDecoder:
    """Incremental framing; recover from noise, corruption and truncated packets."""

    def __init__(self):
        self.buffer = bytearray()
        self.frames_total = 0
        self.decode_errors = 0
        self.discarded_bytes = 0
        self.last_error = ""

    def _error(self, message):
        self.decode_errors += 1
        self.last_error = message

    def _complete_packet_at(self, offset):
        if len(self.buffer) - offset < HEADER.size:
            return False
        _, version, flags, size, _ = HEADER.unpack_from(self.buffer, offset)
        end = offset + HEADER.size + size
        return (version == VERSION and flags == 0 and size <= MAX_PAYLOAD
                and len(self.buffer) >= end + 4
                and zlib.crc32(self.buffer[offset:end])
                == struct.unpack_from("<I", self.buffer, end)[0])

    def feed(self, chunk):
        self.buffer.extend(chunk)
        frames = []
        while True:
            start = self.buffer.find(MAGIC)
            if start < 0:
                keep = min(len(MAGIC) - 1, len(self.buffer))
                self.discarded_bytes += len(self.buffer) - keep
                del self.buffer[:len(self.buffer) - keep]
                break
            if start:
                self.discarded_bytes += start
                del self.buffer[:start]
            if len(self.buffer) < HEADER.size:
                break
            _, version, flags, size, sequence = HEADER.unpack_from(self.buffer)
            if version != VERSION or flags != 0 or size > MAX_PAYLOAD:
                self._error("帧版本、标志或长度错误")
                del self.buffer[0]
                continue
            end = HEADER.size + size
            if len(self.buffer) < end + 4:
                # A dropped tail must not hold up the next complete valid frame.
                later = self.buffer.find(MAGIC, HEADER.size)
                while later >= 0 and not self._complete_packet_at(later):
                    later = self.buffer.find(MAGIC, later + 1)
                if later < 0:
                    break
                self._error("丢弃不完整帧")
                self.discarded_bytes += later
                del self.buffer[:later]
                continue
            if zlib.crc32(self.buffer[:end]) != struct.unpack_from("<I", self.buffer, end)[0]:
                self._error("CRC32 校验失败")
                del self.buffer[0]
                continue
            payload = bytes(self.buffer[HEADER.size:end])
            del self.buffer[:end + 4]
            try:
                frames.append(decode_payload(sequence, payload))
                self.frames_total += 1
            except ValueError as exc:
                self._error(str(exc))
        return frames
