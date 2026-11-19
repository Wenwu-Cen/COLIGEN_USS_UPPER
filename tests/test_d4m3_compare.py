from binascii import crc_hqx
import json
from pathlib import Path
import struct

from d4m3_compare import D4M3DatagramAssembler
from recording_session import RawEvent, read_events
from replay_capture_protocol import LEGACY_IDS
from replay_runtime import CaptureRuntime, CaptureSettings
from udp_source import IpcDbcDecoder, UdpReader


def _pack_raw(cycle, tick_ms, result_cycle=0, ordinal=0, timestamp=0):
    frames = {frame_id: bytes(64) for frame_id in LEGACY_IDS}
    vehicle, timing = bytearray(64), bytearray(64)
    struct.pack_into("<IIIBH", vehicle, 48, 0xD4000017, cycle, result_cycle, 1, ordinal)
    stamp = struct.pack("<Q", timestamp)
    timing[44:50], timing[58:60] = stamp[:6], stamp[6:]
    struct.pack_into("<Q", timing, 50, tick_ms)
    check = crc_hqx(vehicle[48:56] + timing[50:58] + vehicle[56:63] + stamp, 0xFFFF)
    struct.pack_into("<H", timing, 60, check)
    frames.update({0x102: bytes(timing), 0x103: bytes(vehicle)})
    return list(frames.items())


def test_d4m3_group_checks_identity_and_counts_duplicates_and_gaps():
    assembler = D4M3DatagramAssembler()
    rows = _pack_raw(20, 400, 19, 2, 390004)
    cycle, result = assembler.feed_datagram(rows)
    assert (cycle.boot, cycle.cycle, cycle.tick_us) == (0x17, 20, 400000)
    assert result == (390004, (0x17, 19, 2))
    assert assembler.feed_datagram(rows) is None
    assert assembler.feed_datagram(rows[:-1]) is None
    assert assembler.feed_datagram(_pack_raw(22, 440))[0].cycle == 22
    damaged = _pack_raw(23, 460)
    frame_id, data = damaged[-2]
    damaged[-2] = frame_id, data[:49] + b"\x01" + data[50:]
    assert assembler.feed_datagram(damaged) is None
    assert (assembler.complete, assembler.incomplete, assembler.invalid) == (2, 2, 1)


def test_d4m3_records_visualization_and_raw_without_timestamp_guessing(tmp_path):
    settings = CaptureSettings(
        project="D4M3", dependency="udp", id_profile="legacy", root=str(tmp_path),
        udp_host="192.168.98.123", udp_port=39001, udp_sender="192.168.98.233",
    )
    runtime = CaptureRuntime(settings)
    receiver = UdpReader(config=None, sender_address=settings.udp_sender)
    receiver.decoder = IpcDbcDecoder()
    receiver.subscribe_snapshot(runtime.baseline_udp)

    def receive(datagram):
        runtime.raw(RawEvent("udp", settings.udp_sender + ":40001", 1, datagram))
        receiver._consume(datagram, settings.udp_sender)

    fixture = Path(__file__).parent / "fixtures/udp_uss_cycle.json"
    packets = [bytes.fromhex(packet) for packet in json.loads(fixture.read_text())["datagrams"]]
    timestamp = struct.unpack_from(">Q", packets[19], 24)[0]
    for packet in packets:
        receive(packet)
    for rows in (_pack_raw(20, 400, 18, 1, timestamp + 1),
                 _pack_raw(21, 420, 19, 2, timestamp)):
        receive(b"".join(struct.pack(">I", frame_id) + data for frame_id, data in rows))
    runtime.close()
    assert receiver.refresh_total == 1 and receiver.decode_errors == 0
    assert len(list(read_events(runtime.session.path, "raw"))) == 29
    assert len(list(read_events(runtime.session.path, "input"))) == 2
    [baseline] = list(read_events(runtime.session.path, "baseline"))
    assert baseline[3]["key"] == [0x17, 19, 2]
    assert not baseline[3]["scene"]["slots"]
